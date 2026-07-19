# frozen_string_literal: true

require "digest"
require "date"
require "json"
require "time"

module N64Game
  # Pure validation for the portable portion of a per-asset authoring receipt.
  # Filesystem/Git materialization and evidence-manifest ownership stay in the
  # production validator adapter.
  module AuthoringStackReceipt
    RECEIPT_KEYS = %w[
      schema scope_id gate source_manifest_sha256 output_manifest_sha256 build_id
      toolchain_lock_sha256 checker_sha256 blender_executable_sha256 blender_seal
      fast64_source_manifest_sha256 probe_mode result checked_at
    ].freeze
    SCHEMA = "n64game-authoring-stack-receipt-v1".freeze
    BLENDER_SEAL = "DEEP_STRICT_EXPLICIT_REQUIREMENT_PASS".freeze
    PROBE_MODE = "ISOLATED_COPY_ENABLED_LOADED_NO_INHERITED_ENV".freeze
    CHECKER_BUNDLE_DOMAIN = "n64game-authoring-checker-bundle-v1\n".b.freeze
    CHECKER_BUNDLE_PATHS = %w[
      scripts/check-authoring-stack
      scripts/record-authoring-stack-receipt
      tools/n64game_authoring.py
      tools/n64game_authoring_receipt.py
    ].freeze
    RECEIPT_BASENAME = "AUTHORING_STACK_RECEIPT.txt".freeze
    ROOT_REQUIRED_MODES = {
      "scripts/validate-asset-contract" => "100755",
      "lib/n64game/authoring_stack_receipt.rb" => "100644",
      "config/toolchain.lock.json" => "100644",
      "scripts/check-authoring-stack" => "100755",
      "scripts/record-authoring-stack-receipt" => "100755",
      "tools/n64game_authoring.py" => "100644",
      "tools/n64game_authoring_receipt.py" => "100644"
    }.freeze
    APPLICABLE_PROFILES = %w[RIGGED_MODEL STATIC_MODEL_ENV ANIMATION].freeze
    BLENDER_EXECUTABLE_SHA256 = "8156431a9b9ec1daf49bccea4bd92f327f6efc1ca330d5103881580f3e7773ef".freeze
    FAST64_SOURCE_MANIFEST_SHA256 = "14bb6c7b527ba364fa5e2a5011779ddd24c61f998c79c120f28d895d92e62e6b".freeze
    FAST64_COMMIT = "8e9630c11824a9c00e9379279d43c64264eda87e".freeze
    APPROVED_TOOLCHAIN_LOCK_SHA256 = "818a0232394f58698906c30c3ebcd9ca84bb6f35c5bae8fb3bed297d78628f80".freeze
    APPROVED_CHECKER_BUNDLE_SHA256 = "92b65d0356b7e25c12d2881f050f87780fd08284175b660c6da15471030f2adc".freeze
    GATE5_EXPORT_IMPLEMENTED = false
    APPROVED_GATE5_EXPORTER_SHA256 = "PENDING".freeze
    HEX64 = /\A[0-9a-f]{64}\z/.freeze
    BUILD_ID = /\A[A-Za-z0-9][A-Za-z0-9._-]{0,95}\z/.freeze
    GENERIC_BUILD_PARTS = %w[
      pending none unassigned unknown todo tbd test testing example sample placeholder dummy fake
      reviewer operator person user agent owner creator temp temporary na n-a nil null
    ].freeze
    RFC3339 = /\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})\z/.freeze

    module_function

    def applicable?(canonical_asset_scope:, profile:, source_paths:)
      canonical_asset_scope &&
        (APPLICABLE_PROFILES.include?(profile) || Array(source_paths).any? do |path|
          path.is_a?(String) && File.extname(path).downcase == ".blend"
        end)
    end

    def receipt_path(scope_id, gate)
      raise ArgumentError, "authoring receipt gate must be G2 or G5" unless %w[G2 G5].include?(gate)

      "review/#{scope_id}/#{gate.downcase}/#{RECEIPT_BASENAME}"
    end

    def receipt_candidate?(entry)
      return false unless entry.is_a?(Hash)

      path = entry[:path] || entry["path"]
      role = entry[:role] || entry["role"]
      (path.is_a?(String) && File.basename(path).casecmp?(RECEIPT_BASENAME)) ||
        role == "authoring.stack_receipt"
    end

    # Pure manifest-graph policy used by the production adapter and portable
    # mutation tests. The caller supplies only entries transitively owned by
    # this gate's evidence manifest, plus the exact direct owner selected by
    # the production manifest walker.
    def placement_issues(scope_id:, gate:, applicable:, evidence_manifest_path:, evidence_entries:,
                         direct_owner:, source_owned_paths:, output_owned_paths:, build_id:)
      issues = []
      candidates = Array(evidence_entries).select { |entry| receipt_candidate?(entry) }
      expected = applicable && %w[G2 G5].include?(gate)
      unless expected
        issues << "authoring receipt is forbidden for this gate/profile" unless candidates.empty?
        return issues
      end

      expected_path = receipt_path(scope_id, gate)
      issues << "G2 gate row build must be -" if gate == "G2" && build_id != "-"
      candidate_paths = candidates.map { |entry| entry[:path] || entry["path"] }
      issues << "evidence closure must contain exactly the canonical authoring receipt" unless
        candidate_paths == [expected_path]
      entry = candidates.first if candidate_paths == [expected_path]
      issues << "authoring receipt must be a direct evidence-manifest member" unless
        direct_owner == evidence_manifest_path
      if entry
        role = entry[:role] || entry["role"]
        capture = entry[:capture] || entry["capture"]
        manifest_build = entry[:build] || entry["build"]
        kind = entry[:kind] || entry["kind"]
        mode = entry[:mode] || entry["mode"]
        issues << "authoring receipt manifest role mismatch" unless role == "authoring.stack_receipt"
        issues << "authoring receipt capture token must be -" unless capture == "-"
        expected_build = gate == "G2" ? "-" : build_id
        issues << "authoring receipt manifest build token mismatch" unless manifest_build == expected_build
        issues << "authoring receipt must be an ordinary Git member" unless kind.to_s == "git"
        issues << "authoring receipt manifest member must be mode 100644" unless mode == "100644"
      end
      issues << "authoring receipt must not be source-manifest-owned" if
        Array(source_owned_paths).include?(expected_path)
      issues << "authoring receipt must not be output-manifest-owned" if
        Array(output_owned_paths).include?(expected_path)
      issues
    end

    # Exact tree/manifest universe closure. A receipt-like basename catches
    # unmanifested, orphaned, nested, wrong-gate, and case-variant files; the
    # exact role set independently catches a receipt role hidden at any other
    # filename.
    def universe_issues(expected_paths:, tree_entries:, manifest_entries:)
      issues = []
      raw_expected = Array(expected_paths)
      expected = raw_expected.select { |path| path.is_a?(String) }.sort
      issues << "expected authoring receipt paths are malformed" unless expected.length == raw_expected.length
      issues << "expected authoring receipt paths are duplicated" unless expected == expected.uniq
      tree_candidates = Array(tree_entries).select do |entry|
        next false unless entry.is_a?(Hash)

        path = entry[:path] || entry["path"]
        path.is_a?(String) && File.basename(path).casecmp?(RECEIPT_BASENAME)
      end
      tree_paths = tree_candidates.map { |entry| entry[:path] || entry["path"] }.sort
      issues << "reviewed tree authoring receipt universe mismatch" unless tree_paths == expected.uniq
      tree_candidates.each do |entry|
        mode = entry[:mode] || entry["mode"]
        type = entry[:type] || entry["type"]
        issues << "reviewed authoring receipt must be one ordinary 100644 Git blob" unless
          mode == "100644" && type == "blob"
      end

      manifest_candidates = Array(manifest_entries).select { |entry| receipt_candidate?(entry) }
      raw_manifest_paths = manifest_candidates.map { |entry| entry[:path] || entry["path"] }
      manifest_paths = raw_manifest_paths.select { |path| path.is_a?(String) }.sort
      issues << "manifest authoring receipt candidate paths are malformed" unless
        manifest_paths.length == raw_manifest_paths.length
      issues << "manifest authoring receipt candidate universe mismatch" unless manifest_paths == expected.uniq
      raw_role_paths = Array(manifest_entries).select do |entry|
        next false unless entry.is_a?(Hash)

        (entry[:role] || entry["role"]) == "authoring.stack_receipt"
      end.map { |entry| entry[:path] || entry["path"] }
      role_paths = raw_role_paths.select { |path| path.is_a?(String) }.sort
      issues << "authoring.stack_receipt role paths are malformed" unless
        role_paths.length == raw_role_paths.length
      issues << "authoring.stack_receipt role universe mismatch" unless role_paths == expected.uniq
      issues
    end

    def checker_bundle_sha256(members)
      return nil unless members.keys.sort == CHECKER_BUNDLE_PATHS.sort

      digest = Digest::SHA256.new
      digest.update(CHECKER_BUNDLE_DOMAIN)
      CHECKER_BUNDLE_PATHS.sort.each do |path|
        bytes = members[path]
        return nil unless bytes.is_a?(String)

        digest.update("#{path}\t#{Digest::SHA256.hexdigest(bytes)}\n")
      end
      digest.hexdigest
    end

    def strict_rfc3339?(value)
      match = value.to_s.match(
        /\A(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(Z|([+-])(\d{2}):(\d{2}))\z/
      )
      return false unless match

      year, month, day, hour, minute, second = match.captures.first(6).map(&:to_i)
      return false unless year.positive? && Date.valid_date?(year, month, day)
      return false unless hour.between?(0, 23) && minute.between?(0, 59) && second.between?(0, 59)
      return true if match[7] == "Z"

      match[9].to_i.between?(0, 23) && match[10].to_i.between?(0, 59)
    end

    def canonical_build_id?(value)
      return false unless value.to_s.match?(BUILD_ID)

      components = value.downcase.split(/[._-]+/)
      generic = lambda do |component|
        normalized = component.delete("._-")
        GENERIC_BUILD_PARTS.any? do |root|
          normalized == root || normalized.match?(/\A#{Regexp.escape(root)}0*[0-9]+\z/)
        end
      end
      !generic.call(components.join) && components.none? { |component| generic.call(component) }
    end

    def parse(bytes)
      errors = []
      unless bytes.is_a?(String)
        return [{}, ["receipt bytes are not a String"]]
      end
      utf8 = bytes.dup.force_encoding(Encoding::UTF_8)
      errors << "receipt is not valid UTF-8" unless utf8.valid_encoding?
      errors << "receipt has a BOM" if bytes.start_with?("\xEF\xBB\xBF".b)
      errors << "receipt must use LF only" if bytes.include?("\r".b)
      errors << "receipt must have exactly one final LF" unless bytes.end_with?("\n".b) && !bytes.end_with?("\n\n".b)
      lines = bytes.split("\n".b, -1)
      lines.pop if lines.last == "".b
      errors << "receipt must contain exactly #{RECEIPT_KEYS.length} ordered lines" unless lines.length == RECEIPT_KEYS.length
      values = {}
      RECEIPT_KEYS.each_with_index do |key, index|
        line = lines[index]
        next errors << "receipt is missing ordered field #{key}" unless line

        prefix = "#{key}: ".b
        unless line.start_with?(prefix) && line.bytesize > prefix.bytesize
          errors << "receipt field #{index + 1} must be exactly #{key}: <value>"
          next
        end
        value = line.byteslice(prefix.bytesize..-1).to_s.force_encoding(Encoding::UTF_8)
        errors << "receipt field #{key} has invalid UTF-8" unless value.valid_encoding?
        values[key] = value
      end
      [values, errors]
    end

    def exact_toolchain_pins?(bytes)
      lock = JSON.parse(bytes)
      authoring = lock["authoring"]
      blender = authoring.is_a?(Hash) ? authoring["blender_macos_arm64"] : nil
      fast64 = authoring.is_a?(Hash) ? authoring["fast64"] : nil
      lock["schema_version"] == 1 && blender.is_a?(Hash) && fast64.is_a?(Hash) &&
        blender["version"] == "4.5.11 LTS" && blender["version_tuple"] == [4, 5, 11] &&
        blender["build_hash"] == "4db51e9d1e1e" && blender["build_platform"] == "Darwin" &&
        blender["executable_sha256"] == BLENDER_EXECUTABLE_SHA256 &&
        blender["bundle_identifier"] == "org.blenderfoundation.blender" &&
        blender["codesign_team_identifier"] == "68UA947AUU" &&
        fast64["version"] == "2.5.3" && fast64["tag"] == "v2.5.3" &&
        fast64["commit"] == FAST64_COMMIT &&
        fast64["source_tree_manifest_sha256"] == FAST64_SOURCE_MANIFEST_SHA256 &&
        authoring["blender_target"] == blender["version"] &&
        authoring["fast64_version"] == fast64["version"] && authoring["fast64_commit"] == fast64["commit"]
    rescue JSON::ParserError, TypeError
      false
    end

    def validate(bytes:, scope_id:, gate:, source_manifest_sha256:, output_manifest_sha256:, build_id:,
                 decided_at:, toolchain_lock_bytes:, checker_members:)
      values, errors = parse(bytes)
      expected = {
        "schema" => SCHEMA,
        "scope_id" => scope_id,
        "gate" => gate,
        "source_manifest_sha256" => source_manifest_sha256,
        "output_manifest_sha256" => output_manifest_sha256,
        "build_id" => build_id,
        "toolchain_lock_sha256" => Digest::SHA256.hexdigest(toolchain_lock_bytes),
        "checker_sha256" => checker_bundle_sha256(checker_members),
        "blender_executable_sha256" => BLENDER_EXECUTABLE_SHA256,
        "blender_seal" => BLENDER_SEAL,
        "fast64_source_manifest_sha256" => FAST64_SOURCE_MANIFEST_SHA256,
        "probe_mode" => PROBE_MODE,
        "result" => "PASS"
      }
      expected.each do |key, value|
        errors << "receipt #{key} mismatch" unless value && values[key] == value
      end
      errors << "historical toolchain lock differs from the frozen approved file" unless
        expected["toolchain_lock_sha256"] == APPROVED_TOOLCHAIN_LOCK_SHA256
      errors << "historical checker/producer bundle differs from the frozen approved bundle" unless
        expected["checker_sha256"] == APPROVED_CHECKER_BUNDLE_SHA256
      errors << "historical toolchain lock does not contain the exact Blender/Fast64 pins" unless
        exact_toolchain_pins?(toolchain_lock_bytes)
      errors << "receipt gate must be G2 or G5" unless %w[G2 G5].include?(gate)
      if gate == "G2"
        errors << "G2 receipt must bind output NONE and build -" unless
          output_manifest_sha256 == "NONE" && build_id == "-"
      elsif gate == "G5"
        errors << "Gate-5 exporter is not implemented and approved" unless
          GATE5_EXPORT_IMPLEMENTED && APPROVED_GATE5_EXPORTER_SHA256.match?(HEX64)
        errors << "G5 receipt must bind exact output and build" unless
          output_manifest_sha256.to_s.match?(HEX64) && canonical_build_id?(build_id)
      end
      checked_at = values["checked_at"]
      errors << "receipt checked_at is not strict RFC 3339" unless strict_rfc3339?(checked_at)
      errors << "gate decided_at is not strict RFC 3339" unless strict_rfc3339?(decided_at)
      if strict_rfc3339?(checked_at) && strict_rfc3339?(decided_at)
        errors << "receipt checked_at is later than the gate decision" if Time.iso8601(checked_at) > Time.iso8601(decided_at)
      end
      errors
    end
  end
end
