# frozen_string_literal: true

require "digest"
require "set"
require "time"

module N64Game
  module AssetLifecycleContract
    SCHEMA = "n64game-production-asset-lifecycle-kernel-v1".freeze
    BRANCHES = %w[public_concept populated approved repair generated_child move_pair h2 release].freeze
    HEX40 = /\A[0-9a-f]{40}\z/.freeze
    HEX64 = /\A[0-9a-f]{64}\z/.freeze
    BUILD_ID = /\A[A-Za-z0-9][A-Za-z0-9._-]{0,95}\z/.freeze
    SAFE_PATH = /\A[A-Za-z0-9][A-Za-z0-9._\/-]*\z/.freeze
    PRODUCTION_ID = /\A[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+\z/.freeze
    GENERIC_MACHINE_COMPONENTS = %w[
      pending none unassigned unknown todo tbd test testing example sample placeholder dummy fake
      reviewer operator person user agent owner creator temp temporary na n-a nil null
    ].freeze
    COMPLETE_GATE_DECISIONS = %w[pass STATIC_STATE_EQ NON_ROM_DELIVERY_EQ INHERITED_CHILD_EQ].freeze
    ALL_GATE_DECISIONS = (["PENDING", "fail"] + COMPLETE_GATE_DECISIONS).freeze
    STABLE_REPAIR_FIELDS = %w[
      basis production_id subset_sha256 authorization_path gate_record_path provenance_path
      source_manifest_path output_manifest_path
    ].freeze
    ROLLUP_SCOPES = %w[rollup.player rollup.quarrune rollup.sector rollup.presentation].freeze
    ROLLUP_PROFILES = {
      "rollup.player" => "RIGGED_MODEL",
      "rollup.quarrune" => "RIGGED_MODEL",
      "rollup.sector" => "STATIC_MODEL_ENV",
      "rollup.presentation" => "UI_FONT_IMAGE"
    }.freeze
    AGGREGATE_PATHS = %w[
      review/benchmark/PAYLOAD_MANIFEST.sha256
      review/benchmark/WHITELIST_GATE_REGISTRY.tsv
      review/benchmark/BENCHMARK_EVIDENCE_REGISTRY.tsv
      review/benchmark/ROM_BUILD_RECIPE.tsv
      review/benchmark/rollups/player/GATE_RECORD.tsv
      review/benchmark/rollups/quarrune/GATE_RECORD.tsv
      review/benchmark/rollups/sector/GATE_RECORD.tsv
      review/benchmark/rollups/presentation/GATE_RECORD.tsv
    ].freeze
    ROLLUP_KEYS = %w[build_id gate_record_sha256 gates scope].freeze
    GENERATED_CAMERA_CHILDREN = {
      "ASSET_CAMERA_SHOT_UI_NONE" => "ui.panel.dialogue",
      "ASSET_CAMERA_SHOT_SIM_COMMS" => "env.annex.sim_chamber",
      "ASSET_CAMERA_SHOT_ANNEX_GROUP" => "env.annex.atrium_lower",
      "ASSET_CAMERA_SHOT_OREN" => "env.annex.director_lab",
      "ASSET_CAMERA_SHOT_JO_RELAY" => "env.annex.workshop",
      "ASSET_CAMERA_SHOT_PELL_RELAY" => "env.annex.atrium_upper",
      "ASSET_CAMERA_SHOT_RUSK_COURTYARD" => "env.estate.courtyard",
      "ASSET_CAMERA_SHOT_RUSK_FOYER" => "env.estate.foyer_gallery",
      "ASSET_CAMERA_SHOT_ESTATE_STUDY" => "env.estate.observatory_study",
      "ASSET_CAMERA_SHOT_ANNEX_RETURN" => "env.annex.atrium_lower",
      "ASSET_CAMERA_SHOT_HOOK_GROUP" => "lmk.annex.resonance_monitor",
      "ASSET_CAMERA_SHOT_OPTIONAL_NPC" => "col.common.camera_volumes",
      "ASSET_CAMERA_SHOT_EXAMINE_FOCUS" => "col.common.camera_volumes",
      "ASSET_CAMERA_SHOT_POST_CHAPTER" => "col.common.camera_volumes",
      "ASSET_CAMERA_SHOT_MAP_UI" => "env.world_map.desert_relief"
    }.freeze
    GENERATED_CAMERA_PAYLOAD_SHA256 = {
      "ASSET_CAMERA_SHOT_UI_NONE" => "4d077a38705ae265b97f3676e626d6fefdb4e08ad188ea66af1fd6ac63fefa91",
      "ASSET_CAMERA_SHOT_SIM_COMMS" => "c0b15ec2ab3c7dbb8a09bbd61311b7f3ae78a6bc99f9716b5325d22c285722a9",
      "ASSET_CAMERA_SHOT_ANNEX_GROUP" => "e9e84dcf8a6cd5496551bb1440f08e305ed059e3a8bdf629191854a7a199c28c",
      "ASSET_CAMERA_SHOT_OREN" => "c4c08d415d39ef6407e517da21ec271dc018145d4a267fbae6e23e2ab8ba9a2b",
      "ASSET_CAMERA_SHOT_JO_RELAY" => "0fb0c8d81779f6eff387ec1ba1b9ad560c8ac178fc0fd38c5ee34631cb73c4d2",
      "ASSET_CAMERA_SHOT_PELL_RELAY" => "081041dd9847495b8f3cd1109e18ef3748147455980396d3f6cae37e3cfb08e2",
      "ASSET_CAMERA_SHOT_RUSK_COURTYARD" => "ca8250efc54e83be00f5d8a6ce4c2608ad886ed59b2f684f1d20598240a03e72",
      "ASSET_CAMERA_SHOT_RUSK_FOYER" => "87e0afe8910e00ddfee93f8cb36ede279f0092a86030dbf9da34c5ea571d04d5",
      "ASSET_CAMERA_SHOT_ESTATE_STUDY" => "8915b1ee3680c6ad4a24ba06cba58863455b4fcd25873430c8717dbaca4c8b3d",
      "ASSET_CAMERA_SHOT_ANNEX_RETURN" => "7110ea379d7b8e266ef69de1abada7dca5e77c27f554e61c5fc94102ffbce749",
      "ASSET_CAMERA_SHOT_HOOK_GROUP" => "0f07dee635339de9a401c0540bfa0b4053e729bb9df8c78d17381b39c48369f4",
      "ASSET_CAMERA_SHOT_OPTIONAL_NPC" => "12dac257f1c7dff244841dcd3efc54e54ba13a3c68c8102a3e950cc7526ff5f6",
      "ASSET_CAMERA_SHOT_EXAMINE_FOCUS" => "40db0b454c17b7d8c8b24d4d85f851cf11d762b1540b1c7e3518117246851b52",
      "ASSET_CAMERA_SHOT_POST_CHAPTER" => "f078fbeeafbac5b655f39812f598e70b675f75793e5cc7a52207aae481cca849",
      "ASSET_CAMERA_SHOT_MAP_UI" => "f007686055c4fb725f3fa35f68809fd94f7e49085c6cd1d969c3427e318d2b4f"
    }.freeze
    GENERATED_CAMERA_PAYLOADS_SHA256 = "b26a6697e47daf2787ab513b13dc36ac6bd79b43d895b0b21773228d39d28cde".freeze

    class Violation < StandardError
      attr_reader :branch, :issues

      def initialize(branch, issues)
        @branch = branch
        @issues = issues.freeze
        super("#{branch}: #{issues.join('; ')}")
      end
    end

    module_function

    def validate!(branch, payload)
      branch = branch.to_s
      raise Violation.new(branch, ["unknown lifecycle branch"]) unless BRANCHES.include?(branch)
      raise Violation.new(branch, ["payload must be a Hash"]) unless payload.is_a?(Hash)

      issues = send("validate_#{branch}", payload)
      raise Violation.new(branch, issues) unless issues.empty?

      { "schema" => SCHEMA, "branch" => branch, "result" => "PASS" }
    end

    def ledger_lifecycle_issues(status, gates, has_output)
      issues = []
      unless gates.is_a?(Array) && gates.length == 7 && gates.all? { |gate| ALL_GATE_DECISIONS.include?(gate) }
        return ["gate vector must contain exactly seven production decisions"]
      end
      complete = lambda { |decision| COMPLETE_GATE_DECISIONS.include?(decision) }
      case status
      when "source"
        issues << "source status requires Gate 1 completion" unless complete.call(gates[0])
        issues << "source status cannot complete Gate 5 or later" if gates[4..-1].any? { |gate| complete.call(gate) }
        issues << "source status cannot own converted output" if has_output
      when "converted"
        issues << "converted status requires Gates 1-5 complete" unless gates.first(5).all? { |gate| complete.call(gate) }
        issues << "converted status requires Gates 6-7 PENDING" unless gates[5..-1] == %w[PENDING PENDING]
        issues << "converted status requires output manifest" unless has_output
      when "review"
        issues << "review status requires Gates 1-5 complete" unless gates.first(5).all? { |gate| complete.call(gate) }
        issues << "review status cannot retain seven completed gates" if gates.all? { |gate| complete.call(gate) }
        issues << "review status requires output manifest" unless has_output
      when "approved"
        issues << "approved status requires seven legal completion decisions" unless gates.all? { |gate| complete.call(gate) }
        issues << "approved status requires output manifest" unless has_output
      else
        issues << "active registry binding uses illegal ledger status #{status.inspect}"
      end
      issues
    end

    def validate_public_concept(payload)
      issues = []
      check(issues,
            exact_keys?(payload, %w[advanced_ids aggregate_pairs authority concept_ids decision lock registry_rows status]),
            "public-concept payload keys differ")
      check_control(payload, issues, approved: false)

      aggregate_pairs = payload["aggregate_pairs"]
      pending_pair = { "path" => "PENDING", "sha256" => "PENDING" }
      check(issues, aggregate_pairs.is_a?(Array) && aggregate_pairs.length == 8,
            "public-concept lifecycle requires exactly eight aggregate slots")
      if aggregate_pairs.is_a?(Array)
        aggregate_pairs.each_with_index do |pair, index|
          check(issues, pair == pending_pair, "public-concept aggregate pair #{index + 1} is not literal PENDING")
        end
      end

      rows = payload["registry_rows"]
      check(issues, rows.is_a?(Array) && rows.length == 52,
            "public-concept lifecycle requires exactly 52 control rows")
      ids = []
      if rows.is_a?(Array)
        rows.each_with_index do |row, index|
          basis = format("WB-%03d", index + 1)
          unless row.is_a?(Hash)
            issues << "#{basis} public-concept control row must be a Hash"
            next
          end
          check(issues, exact_keys?(row, %w[basis gates production_id state]),
                "#{basis} public-concept control row keys differ")
          check(issues, row["basis"] == basis, "#{basis} public-concept control row order mismatch")
          production_id = row["production_id"]
          ids << production_id
          check(issues, production_id.is_a?(String) && PRODUCTION_ID.match?(production_id) &&
                        !expected_profile(production_id).nil?,
                "#{basis} public-concept production ID is noncanonical")
          check(issues, row["state"] == "INACTIVE", "#{basis} public-concept control row is active")
          check(issues, row["gates"] == ["PENDING"] * 7,
                "#{basis} public-concept gate vector is not pending")
        end
        check(issues, ids.all? { |identifier| identifier.is_a?(String) } && ids.uniq.length == 52,
              "public-concept control production IDs are not unique")
      end

      concept_ids = payload["concept_ids"]
      valid_concepts = concept_ids.is_a?(Array) && !concept_ids.empty? &&
                       concept_ids.all? do |identifier|
                         identifier.is_a?(String) && PRODUCTION_ID.match?(identifier) &&
                           !expected_profile(identifier).nil?
                       end
      check(issues, valid_concepts, "public-concept lifecycle requires at least one ordinary concept ID")
      if concept_ids.is_a?(Array) && concept_ids.all? { |identifier| identifier.is_a?(String) }
        check(issues, concept_ids == concept_ids.sort.uniq,
              "public-concept IDs must be sorted and unique")
      end
      check(issues, payload["advanced_ids"] == [], "public-concept advanced IDs must be exactly empty")

      authority = payload["authority"]
      unless authority.is_a?(Hash)
        issues << "public-concept authority must be a Hash"
        return issues
      end
      check(issues, exact_keys?(authority, %w[advertised_ref clean commit fresh_clone ref]),
            "public-concept authority keys differ")
      check(issues, authority["clean"] == true && authority["advertised_ref"] == true &&
                    authority["fresh_clone"] == true,
            "public-concept authority booleans must all be true")
      check(issues, hex40?(authority["commit"]), "public-concept authority commit is malformed")
      check(issues, valid_advertised_ref?(authority["ref"]), "public-concept authority ref is malformed")
      issues
    end

    def validate_populated(payload)
      issues = []
      check_control(payload, issues, approved: false, decisions: %w[PENDING REVIEW_REQUIRED BLOCKED])
      aggregate_pairs = payload["aggregate_pairs"]
      aggregate_mask = validate_staged_aggregate_pairs(aggregate_pairs, issues)
      registry_rows = payload["registry_rows"]
      validate_registry_rows(registry_rows, issues, require_approved: false)
      active_rows = registry_rows.is_a?(Array) ? registry_rows.select do |row|
        row.is_a?(Hash) && %w[AUTHORIZED REPAIR_ONLY].include?(row["state"])
      end : []
      check(issues, !active_rows.empty?, "populated lifecycle requires at least one AUTHORIZED/REPAIR_ONLY registry row")
      if payload["decision"] == "PENDING"
        check(issues, active_rows.none? { |row| row["state"] == "REPAIR_ONLY" },
              "PENDING populated lifecycle cannot contain REPAIR_ONLY registry rows")
      end
      shared_build_id = payload["build_id"]
      check(issues, concrete_build_id?(shared_build_id),
            "populated lifecycle shared clean-build ID is malformed")
      rollups = payload["rollups"]
      validate_staged_rollups(rollups, aggregate_pairs, aggregate_mask, shared_build_id, issues)
      validate_staged_evidence_claim(registry_rows, rollups, aggregate_mask, shared_build_id, issues)
      issues
    end

    def validate_approved(payload)
      issues = []
      check_control(payload, issues, approved: true)
      check(issues, payload["defects"] == { "critical" => 0, "high" => 0, "medium" => 0 },
            "approved lifecycle requires zero critical/high/medium defects")
      build_id = payload["build_id"]
      check(issues, concrete_build_id?(build_id), "approved build ID is malformed")
      registry_rows = payload["registry_rows"]
      validate_registry_rows(registry_rows, issues, require_approved: true, build_id: build_id)
      rollups = payload["rollups"]
      validate_rollups(rollups, issues, require_complete: true, build_id: build_id)
      if registry_rows.is_a?(Array) && rollups.is_a?(Array)
        total = (registry_rows + rollups).sum do |row|
          row.is_a?(Hash) && row["gates"].is_a?(Array) ? row["gates"].count { |gate| complete_gate?(gate) } : 0
        end
        check(issues, total == 392, "approved lifecycle must project exactly 392 completed gate decisions")
      end
      validate_approved_identity(payload["identity"], issues)
      issues
    end

    def validate_repair(payload)
      issues = []
      check_control(payload, issues, approved: false, decisions: %w[REVIEW_REQUIRED BLOCKED])
      prior_rows = payload["prior_registry_rows"]
      current_rows = payload["current_registry_rows"]
      tokens = payload["return_tokens"]
      check(issues, prior_rows.is_a?(Array) && prior_rows.length == 52,
            "repair prior registry must contain exactly 52 rows")
      check(issues, current_rows.is_a?(Array) && current_rows.length == 52,
            "repair current registry must contain exactly 52 rows")
      check(issues, tokens.is_a?(Array) && !tokens.empty?, "repair lifecycle requires returned defect tokens")
      if tokens.is_a?(Array)
        all_string_tokens = tokens.all? { |token| token.is_a?(String) }
        check(issues, all_string_tokens, "repair return tokens must all be strings")
        check(issues, tokens == tokens.sort.uniq, "repair return tokens must be sorted and unique") if all_string_tokens
        valid_bases = (1..52).map { |index| format("WB-%03d", index) }.to_set
        tokens.each do |token|
          check(issues, token.is_a?(String) && token.match?(/\AWB-\d{3}:G[1-7]:[A-Z][A-Z0-9._-]{2,127}\z/),
                "repair return token is noncanonical: #{token.inspect}")
          basis = token.to_s.split(":", 2).first
          check(issues, valid_bases.include?(basis), "repair return basis is outside WB-001..WB-052: #{basis.inspect}")
        end
      end
      return_bases = Array(tokens).map { |token| token.to_s.split(":", 2).first }.uniq.to_set
      if current_rows.is_a?(Array)
        repair_bases = current_rows.select { |row| row.is_a?(Hash) && row["state"] == "REPAIR_ONLY" }
                                   .map { |row| row["basis"] }.to_set
        check(issues, repair_bases == return_bases,
              "REPAIR_ONLY registry bases do not exactly equal returned bases")
      end
      if prior_rows.is_a?(Array) && current_rows.is_a?(Array) && prior_rows.length == current_rows.length
        current_rows.each_with_index do |current, index|
          prior = prior_rows[index]
          basis = format("WB-%03d", index + 1)
          unless current.is_a?(Hash) && prior.is_a?(Hash)
            issues << "#{basis} repair row must be a Hash"
            next
          end
          check(issues, current["basis"] == basis && prior["basis"] == basis, "#{basis} repair row order mismatch")
          if return_bases.include?(basis)
            check(issues, current["state"] == "REPAIR_ONLY", "#{basis} returned row must be REPAIR_ONLY")
            STABLE_REPAIR_FIELDS.each do |field|
              check(issues, current[field] == prior[field], "#{basis} changed stable repair field #{field}")
            end
            prior_gates = Array(prior["gates"])
            current_gates = Array(current["gates"])
            (0...7).each do |gate_index|
              next if prior_gates[gate_index] == current_gates[gate_index]
              prefix = "#{basis}:G#{gate_index + 1}:"
              check(issues, Array(tokens).any? { |token| token.is_a?(String) && token.start_with?(prefix) },
                    "#{basis} changed G#{gate_index + 1} without its return token")
            end
          else
            check(issues, current == prior, "#{basis} unaffected registry row is not byte-equivalent")
          end
        end
      end
      issues
    end

    def validate_generated_child(payload)
      issues = []
      rows = payload["rows"]
      check(issues, payload["transition_commit_matches_public_head"] == true,
            "generated-child transition is not bound to current public HEAD")
      check(issues, rows.is_a?(Array) && rows.length == 15,
            "generated-child registry must contain exactly 15 rows")
      advanced = 0
      output_payloads = []
      if rows.is_a?(Array)
        rows.first(GENERATED_CAMERA_CHILDREN.length).each_with_index do |row, index|
          child_id, parent_id = GENERATED_CAMERA_CHILDREN.to_a[index]
          unless row.is_a?(Hash)
            issues << "generated-child row #{index + 1} must be a Hash"
            next
          end
          label = "generated child #{child_id}"
          check(issues, row["child_id"] == child_id && row["parent_id"] == parent_id,
                "#{label} ID/parent/order mismatch")
          state = row["state"]
          check(issues, %w[concept source converted review approved].include?(state), "#{label} state is illegal")
          if state == "concept"
            check(issues, row["lifecycle_fields_pending"] == true, "#{label} concept row does not retain PENDING fields")
            next
          end
          advanced += 1
          check(issues, row["parent_active"] == true, "#{label} parent is not active")
          check(issues, hex64?(row["initial_tuple_sha256"]), "#{label} initial tuple digest is malformed")
          check(issues, row["source_revision_path"] == "docs/DATA_SCHEMAS.md" && hex64?(row["source_revision_sha256"]),
                "#{label} source revision is noncanonical")
          has_output = %w[converted review approved].include?(state)
          gates = row["gates"]
          ledger_lifecycle_issues(state, gates, has_output).each { |issue| issues << "#{label}: #{issue}" }
          if has_output
            expected_output = "review/generated/#{child_id}/g5/CAMERA_PAYLOAD.n64cam"
            check(issues, row["output_path"] == expected_output && hex64?(row["output_sha256"]),
                  "#{label} output path/hash is noncanonical")
            check(issues, row["output_bytesize"] == 36, "#{label} deterministic camera payload is not 36 bytes")
            output_hex = row["output_bytes_hex"]
            output_bytes = if output_hex.is_a?(String) && output_hex.match?(/\A[0-9a-f]{72}\z/)
                             [output_hex].pack("H*")
                           end
            check(issues, !output_bytes.nil?, "#{label} deterministic camera payload bytes are malformed")
            check(issues, output_bytes && Digest::SHA256.hexdigest(output_bytes) == row["output_sha256"],
                  "#{label} output digest does not bind the deterministic payload bytes")
            check(issues, row["output_sha256"] == GENERATED_CAMERA_PAYLOAD_SHA256.fetch(child_id),
                  "#{label} output digest differs from its canonical DATA_SCHEMAS tuple")
            output_payloads << output_bytes if output_bytes
          else
            check(issues, row["output_path"] == "PENDING" && row["output_sha256"] == "PENDING",
                  "#{label} preconversion output fields are not PENDING")
          end
        end
      end
      check(issues, advanced.positive?, "generated-child registry must advance at least one child")
      if output_payloads.length == GENERATED_CAMERA_CHILDREN.length
        check(issues, Digest::SHA256.hexdigest(output_payloads.join) == GENERATED_CAMERA_PAYLOADS_SHA256,
              "generated-child 15-payload seal differs from DATA_SCHEMAS")
      end
      issues
    end

    def validate_move_pair(payload)
      issues = []
      pair_key = payload["pair_key"]
      check(issues, pair_key.is_a?(String) && pair_key.match?(/\A[a-z0-9]+(?:[._-][a-z0-9]+)*\z/),
            "move-pair key is malformed")
      children = payload["children"]
      expected_ids = ["sfx.move.#{pair_key}", "vfx.move.#{pair_key}"]
      check(issues, children.is_a?(Array) && children.length == 2, "move pair must contain exactly two children")
      if children.is_a?(Array)
        observed_ids = children.select { |child| child.is_a?(Hash) }.map { |child| child["asset_id"] }
        ids_well_typed = observed_ids.all? { |asset_id| asset_id.is_a?(String) }
        canonical_ids = ids_well_typed ? observed_ids.sort : []
        check(issues, children.all? { |child| child.is_a?(Hash) } && ids_well_typed && canonical_ids == expected_ids,
              "move-pair children are not canonical VFX/audio siblings")
        children.each do |child|
          next unless child.is_a?(Hash)
          check(issues, child["status"] == "approved", "move-pair child is not approved")
          check(issues, Array(child["gates"]).length == 7 && Array(child["gates"]).all? { |gate| complete_gate?(gate) },
                "move-pair child does not have seven completed gates")
          check(issues, hex64?(child["gate_record_sha256"]) && hex64?(child["output_sha256"]),
                "move-pair child identity digest is malformed")
        end
        identities = children.flat_map { |child| [child["gate_record_sha256"], child["output_sha256"]] if child.is_a?(Hash) }.compact
        check(issues, identities.length == 4 && identities.uniq.length == 4,
              "move-pair children improperly share gate/output identity")
      end
      proof = payload["proof"]
      measurement = payload["measurement"]
      if proof.is_a?(Hash) && measurement.is_a?(Hash)
        check(issues, proof["pair_key"] == pair_key && measurement["pair_key"] == pair_key,
              "move-pair proof/measurement key mismatch")
        check(issues, proof["build_id"].is_a?(String) && BUILD_ID.match?(proof["build_id"]),
              "move-pair build ID is malformed")
        check(issues, children.is_a?(Array) && children.all? do |child|
          child.is_a?(Hash) && child["build_id"] == proof["build_id"]
        end,
              "move-pair child/proof builds differ")
        sync_error = canonical_integer(proof["sync_error_ms"])
        check(issues, !sync_error.nil? && sync_error.between?(0, 33), "move-pair sync error exceeds 33 ms")
        check(issues, measurement["build_id"] == proof["build_id"] && measurement["sync_error_ms"] == proof["sync_error_ms"],
              "move-pair measurement does not project proof build/value")
        check(issues, measurement["capture_sha256"] == proof["capture_sha256"] && hex64?(proof["capture_sha256"]),
              "move-pair measurement does not bind the proof capture")
      else
        issues << "move-pair proof and measurement must be Hashes"
      end
      check(issues, payload["capture_has_audio"] == true, "move-pair synchronized capture lacks audio")
      issues
    end

    def validate_h2(payload)
      issues = []
      baseline = payload["first_in_engine"]
      passes = payload["passes"]
      check(issues, baseline.is_a?(Hash), "H2 first-in-engine baseline is missing")
      check(issues, passes.is_a?(Array) && passes.length == 2, "H2 requires exactly two polish passes")
      return issues unless baseline.is_a?(Hash) && passes.is_a?(Array) && passes.length == 2

      check(issues, hex40?(baseline["commit"]) && hex64?(baseline["source_sha256"]) && hex64?(baseline["output_sha256"]),
            "H2 first-in-engine identity is malformed")
      passes.each_with_index do |pass, index|
        label = "H2 polish pass #{index + 1}"
        unless pass.is_a?(Hash)
          issues << "#{label} must be a Hash"
          next
        end
        check(issues, pass["pass_number"] == (index + 1).to_s, "#{label} order mismatch")
        check(issues, hex40?(pass["before_commit"]) && hex40?(pass["after_commit"]), "#{label} commit is malformed")
        %w[before_source_sha256 after_source_sha256 before_output_sha256 after_output_sha256].each do |field|
          check(issues, hex64?(pass[field]), "#{label} #{field} is malformed")
        end
        changed = pass["before_source_sha256"] != pass["after_source_sha256"] ||
                  pass["before_output_sha256"] != pass["after_output_sha256"]
        check(issues, changed, "#{label} makes no material source/output change")
        check(issues, pass["ancestry_valid"] == true && pass["before_commit"] != pass["after_commit"],
              "#{label} is not a strict forward Git transition")
      end
      return issues unless passes.all? { |pass| pass.is_a?(Hash) }

      first = passes[0]
      second = passes[1]
      check(issues,
            first["before_commit"] == baseline["commit"] &&
              first["before_source_sha256"] == baseline["source_sha256"] &&
              first["before_output_sha256"] == baseline["output_sha256"],
            "H2 pass 1 does not descend from the exact first-in-engine baseline")
      check(issues,
            second["before_commit"] == first["after_commit"] &&
              second["before_source_sha256"] == first["after_source_sha256"] &&
              second["before_output_sha256"] == first["after_output_sha256"],
            "H2 polish pass chain is discontinuous")
      check(issues,
            second["after_source_sha256"] == payload["final_source_sha256"] &&
              second["after_output_sha256"] == payload["final_output_sha256"],
            "H2 pass 2 does not resolve to the reviewed final source/output")
      check(issues, payload["final_payload_ancestry_valid"] == true,
            "H2 final polish revision is not an ancestor of the reviewed payload")
      timestamps = [baseline["decided_at"], *passes.map { |pass| pass["decided_at"] },
                    payload["final_g6_decided_at"], payload["final_g7_decided_at"]]
      parsed = timestamps.map { |value| parse_time(value) }
      check(issues, parsed.none?(&:nil?), "H2 lifecycle contains a malformed timestamp")
      if parsed.none?(&:nil?)
        check(issues, parsed.each_cons(2).all? { |left, right| right > left },
              "H2 decisions are not strictly chronological")
      end
      issues
    end

    def validate_release(payload)
      issues = []
      identity = payload["identity"]
      validate_approved_identity(identity, issues)
      return issues unless identity.is_a?(Hash)

      workflow = payload["workflow_json"]
      release = payload["release_json"]
      check(issues, workflow.is_a?(Hash), "release workflow response is missing")
      check(issues, release.is_a?(Hash), "release API response is missing")
      if workflow.is_a?(Hash)
        check(issues,
              workflow["head_sha"] == identity["payload_commit"] && workflow["conclusion"] == "success" &&
                workflow["path"] == identity["workflow_path"],
              "release workflow does not bind a successful payload build")
      end
      if release.is_a?(Hash)
        check(issues, release["tag_name"] == identity["release_tag"] && release["draft"] == false,
              "release API tag/state mismatch")
        assets = release["assets"]
        asset = assets.is_a?(Array) && assets.find { |candidate| candidate.is_a?(Hash) && candidate["name"] == identity["artifact_name"] }
        check(issues, !asset.nil?, "release API lacks the derived ROM asset")
        if asset
          check(issues, asset["browser_download_url"] == identity["release_asset_url"] &&
                        asset["size"] == identity["rom_size_bytes"],
                "release asset URL/size mismatch")
          check(issues, !asset.key?("digest") || asset["digest"] == "sha256:#{identity['rom_sha256']}",
                "release asset digest mismatch")
        end
      end
      issues
    end

    def check_control(payload, issues, approved:, decisions: nil)
      expected_decisions = decisions || (approved ? ["APPROVED"] : ["PENDING"])
      check(issues, expected_decisions.include?(payload["decision"]), "lifecycle decision is not allowed for this branch")
      check(issues, payload["lock"] == (approved ? "UNLOCKED" : "LOCKED"), "lifecycle lock/decision mismatch")
      expected_status = approved ? "Gate 4 approved control record" : "Gate 4 control record"
      check(issues, payload["status"] == expected_status, "lifecycle status/decision mismatch")
    end

    def validate_staged_aggregate_pairs(pairs, issues)
      check(issues, pairs.is_a?(Array) && pairs.length == 8,
            "populated lifecycle requires exactly eight aggregate path/hash pairs")
      return nil unless pairs.is_a?(Array) && pairs.length == 8

      pending_pair = { "path" => "PENDING", "sha256" => "PENDING" }
      mask = pairs.each_with_index.map do |pair, index|
        if pair == pending_pair
          false
        elsif pair.is_a?(Hash) && exact_keys?(pair, %w[path sha256]) &&
              pair["path"] == AGGREGATE_PATHS[index] && hex64?(pair["sha256"])
          true
        else
          issues << "aggregate pair #{index + 1} must be literal PENDING or its positional canonical path/digest"
          nil
        end
      end

      if [true, false].include?(mask[0]) && [true, false].include?(mask[1]) && mask[0] != mask[1]
        issues << "aggregate payload/registry core must transition together"
      end
      if mask.drop(2).include?(true) && mask.first(2) != [true, true]
        issues << "optional aggregate requires the populated payload/registry core pair"
      end
      check(issues, mask.first(2) == [true, true], "populated lifecycle requires aggregate mask prefix 11")
      mask
    end

    def canonical_pending_rollup(scope)
      {
        "scope" => scope,
        "build_id" => "PENDING",
        "gates" => ["PENDING"] * 7,
        "gate_record_sha256" => "PENDING"
      }
    end

    def validate_staged_rollups(rows, aggregate_pairs, aggregate_mask, shared_build_id, issues)
      check(issues, rows.is_a?(Array) && rows.length == 4,
            "lifecycle requires exactly four positional integrated rollup slots")
      return unless rows.is_a?(Array) && rows.length == 4

      rows.each_with_index do |row, index|
        scope = ROLLUP_SCOPES[index]
        expected_pending = canonical_pending_rollup(scope)
        expected_present = aggregate_mask.is_a?(Array) ? aggregate_mask[index + 4] : nil
        actual_present = row.is_a?(Hash) && row != expected_pending
        if [true, false].include?(expected_present)
          check(issues, actual_present == expected_present,
                "integrated rollup presence does not match aggregate mask bits 5-8")
        end

        if expected_present == false
          check(issues, row == expected_pending, "#{scope} pending rollup slot is noncanonical")
          next
        end
        next unless expected_present == true

        unless row.is_a?(Hash)
          issues << "#{scope} populated rollup slot must be a Hash"
          next
        end
        check(issues, exact_keys?(row, ROLLUP_KEYS), "#{scope} populated rollup keys differ")
        check(issues, row["scope"] == scope, "integrated rollup scope order/set mismatch")
        gates = row["gates"]
        check(issues, gates.is_a?(Array) && gates.length == 7 &&
                      gates.all? { |gate| ALL_GATE_DECISIONS.include?(gate) },
              "#{scope} gate vector is malformed")
        check(issues, concrete_build_id?(row["build_id"]),
              "#{scope} build ID is malformed")
        check(issues, !shared_build_id.nil? && row["build_id"] == shared_build_id,
              "#{scope} build ID differs from the shared clean-build ID")
        check(issues, hex64?(row["gate_record_sha256"]), "#{scope} gate-record digest is malformed")
        aggregate_digest = if aggregate_pairs.is_a?(Array) && aggregate_pairs[index + 4].is_a?(Hash)
                             aggregate_pairs[index + 4]["sha256"]
                           end
        check(issues, hex64?(aggregate_digest) && row["gate_record_sha256"] == aggregate_digest,
              "#{scope} gate-record digest differs from its aggregate pair")
      end
    end

    def validate_staged_evidence_claim(registry_rows, rollups, aggregate_mask, shared_build_id, issues)
      return unless aggregate_mask.is_a?(Array) && aggregate_mask[2] == true

      registry_complete = registry_rows.is_a?(Array) && registry_rows.length == 52 &&
                          registry_rows.all? do |row|
                            next false unless row.is_a?(Hash) && %w[AUTHORIZED REPAIR_ONLY].include?(row["state"]) &&
                                              row["build_id"] == shared_build_id

                            profile = expected_profile(row["production_id"])
                            gates = row["gates"]
                            gates.is_a?(Array) && gates.length == 7 && gates.each_with_index.all? do |gate, gate_index|
                              completion_allowed?(gate, profile, "G#{gate_index + 1}")
                            end
                          end
      rollups_complete = aggregate_mask[4, 4] == [true, true, true, true] &&
                         rollups.is_a?(Array) && rollups.length == 4 &&
                         rollups.each_with_index.all? do |row, index|
                           next false unless row.is_a?(Hash) && row["build_id"] == shared_build_id

                           gates = row["gates"]
                           profile = ROLLUP_PROFILES[ROLLUP_SCOPES[index]]
                           gates.is_a?(Array) && gates.length == 7 && gates.each_with_index.all? do |gate, gate_index|
                             completion_allowed?(gate, profile, "G#{gate_index + 1}")
                           end
                         end
      check(issues, registry_complete && rollups_complete,
            "populated evidence aggregate requires 52 active registry rows and four complete rollups with 392 legal decisions")
    end

    def validate_registry_rows(rows, issues, require_approved:, build_id: nil)
      check(issues, rows.is_a?(Array) && rows.length == 52, "whitelist lifecycle requires exactly 52 registry rows")
      return unless rows.is_a?(Array)

      ids = []
      rows.each_with_index do |row, index|
        basis = format("WB-%03d", index + 1)
        unless row.is_a?(Hash)
          issues << "#{basis} registry row must be a Hash"
          next
        end
        ids << row["production_id"]
        check(issues, row["basis"] == basis, "#{basis} registry row order mismatch")
        check(issues, row["production_id"].is_a?(String) && !row["production_id"].empty?, "#{basis} production ID is missing")
        check(issues, hex64?(row["subset_sha256"]), "#{basis} subset digest is malformed")
        gates = row["gates"]
        state = row["state"]
        if state == "INACTIVE"
          check(issues, !require_approved, "#{basis} is INACTIVE in APPROVED lifecycle")
          check(issues, row["repair_ids"] == "NONE", "#{basis} inactive repair IDs are not NONE")
          check(issues, gates == ["PENDING"] * 7, "#{basis} inactive gate vector is not pending")
          next
        end
        check(issues, %w[AUTHORIZED REPAIR_ONLY].include?(state), "#{basis} registry state is illegal")
        check(issues, PRODUCTION_ID.match?(row["production_id"].to_s) && !expected_profile(row["production_id"]).nil?,
              "#{basis} active production ID is noncanonical")
        check(issues, gates.is_a?(Array) && gates.length == 7 && gates.all? { |gate| ALL_GATE_DECISIONS.include?(gate) },
              "#{basis} gate vector is malformed")
        check(issues, concrete_build_id?(row["build_id"]),
              "#{basis} active registry build ID is malformed")
        if require_approved
          check(issues, state == "AUTHORIZED" && row["repair_ids"] == "NONE", "#{basis} is not cleanly authorized")
          check(issues, row["build_id"] == build_id, "#{basis} build ID differs from approval")
          profile = expected_profile(row["production_id"])
          check(issues, gates.is_a?(Array) && gates.each_with_index.all? do |gate, gate_index|
            completion_allowed?(gate, profile, "G#{gate_index + 1}")
          end,
                "#{basis} does not have seven completed gates")
          check(issues, hex64?(row["source_manifest_sha256"]) && hex64?(row["output_manifest_sha256"]),
                "#{basis} approved source/output digest is malformed")
        end
      end
      check(issues, ids.compact.uniq.length == 52, "whitelist lifecycle production IDs are not unique")
    end

    def validate_rollups(rows, issues, require_complete:, build_id: nil)
      check(issues, rows.is_a?(Array) && rows.length == 4, "lifecycle requires exactly four integrated rollups")
      return unless rows.is_a?(Array)

      check(issues, rows.map { |row| row.is_a?(Hash) ? row["scope"] : nil } == ROLLUP_SCOPES,
            "integrated rollup scope order/set mismatch")
      rows.each do |row|
        next unless row.is_a?(Hash)
        gates = row["gates"]
        check(issues, gates.is_a?(Array) && gates.length == 7 && gates.all? { |gate| ALL_GATE_DECISIONS.include?(gate) },
              "#{row['scope']} gate vector is malformed")
        if require_complete
          profile = ROLLUP_PROFILES[row["scope"]]
          check(issues, !profile.nil? && gates.is_a?(Array) && gates.each_with_index.all? do |gate, gate_index|
            completion_allowed?(gate, profile, "G#{gate_index + 1}")
          end,
                "#{row['scope']} does not have seven completed gates")
          check(issues, row["build_id"] == build_id, "#{row['scope']} build ID differs from approval")
        end
      end
    end

    def validate_approved_identity(identity, issues)
      unless identity.is_a?(Hash)
        issues << "approved identity must be a Hash"
        return
      end
      payload_commit = identity["payload_commit"]
      repository = identity["repository"]
      check(issues, hex40?(payload_commit), "approved payload commit is malformed")
      check(issues, repository.is_a?(String) && repository.match?(/\A[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\z/),
            "approved repository identity is malformed")
      check(issues, hex64?(identity["payload_manifest_sha256"]) && hex64?(identity["registry_sha256"]),
            "approved payload/registry digest is malformed")
      check(issues, hex64?(identity["rom_sha256"]), "approved ROM digest is malformed")
      rom_size = canonical_integer(identity["rom_size_bytes"])
      check(issues, !rom_size.nil? && rom_size.positive? && rom_size < 16 * 1024 * 1024,
            "approved ROM size is outside the production limit")
      return unless hex40?(payload_commit) && repository.is_a?(String)

      release_tag = "n64game-benchmark-#{payload_commit}"
      artifact_name = "n64game-#{payload_commit}.z64"
      release_url = "https://github.com/#{repository}/releases/download/#{release_tag}/#{artifact_name}"
      check(issues, identity["approval_ref"] == "refs/tags/n64game-visual-benchmark/#{payload_commit[0, 12]}",
            "approved attestation ref is not payload-derived")
      check(issues, identity["release_tag"] == release_tag, "approved release tag is not payload-derived")
      check(issues, identity["artifact_name"] == artifact_name, "approved ROM artifact name is not payload-derived")
      check(issues, identity["release_asset_url"] == release_url, "approved release URL is not canonical")
    end

    def exact_keys?(hash, keys)
      hash.is_a?(Hash) && hash.keys.sort == keys.sort
    end

    def complete_gate?(decision)
      %w[pass STATIC_STATE_EQ NON_ROM_DELIVERY_EQ].include?(decision)
    end

    def expected_profile(production_id)
      case production_id.to_s
      when /\A(?:chr|echo)\./ then "RIGGED_MODEL"
      when /\A(?:env|lmk|veh|prop)\./ then "STATIC_MODEL_ENV"
      when /\A(?:ui|font)\./ then "UI_FONT_IMAGE"
      when /\Avfx\./ then "VFX"
      when /\A(?:sfx|mus|amb|vox)\./ then "AUDIO"
      when /\Aanm\./ then "ANIMATION"
      when /\A(?:col|nav|spn|int|bnd)\./ then "DATA_SPATIAL"
      when /\Asb\./ then "STORYBOARD"
      end
    end

    def completion_allowed?(decision, profile, gate)
      case decision
      when "pass"
        true
      when "STATIC_STATE_EQ"
        gate == "G4" && %w[STATIC_MODEL_ENV UI_FONT_IMAGE DATA_SPATIAL].include?(profile)
      when "NON_ROM_DELIVERY_EQ"
        profile == "STORYBOARD" && %w[G5 G6].include?(gate)
      else
        false
      end
    end

    def valid_advertised_ref?(value)
      return false unless value.is_a?(String)
      return true if value.match?(%r{\Arefs/pull/[1-9][0-9]*/(?:head|merge)\z})
      return false unless value.start_with?("refs/heads/")

      suffix = value.delete_prefix("refs/heads/")
      SAFE_PATH.match?(suffix) && !suffix.end_with?(".", "/") && !suffix.include?("..") &&
        !suffix.include?("//") && suffix.split("/").none? do |component|
          component.empty? || component.start_with?(".") || component.end_with?(".lock")
        end
    end

    def hex40?(value)
      value.is_a?(String) && HEX40.match?(value)
    end

    def concrete_build_id?(value)
      return false unless value.is_a?(String) && BUILD_ID.match?(value)

      compact = value.downcase.delete("._@+-")
      GENERIC_MACHINE_COMPONENTS.none? do |component|
        root = component.delete("._@+-")
        compact == root || compact.match?(%r{\A#{Regexp.escape(root)}0*[0-9]+\z})
      end
    end

    def hex64?(value)
      value.is_a?(String) && HEX64.match?(value)
    end

    def canonical_integer(value)
      return value if value.is_a?(Integer)
      return nil unless value.is_a?(String) && value.match?(/\A(?:0|[1-9][0-9]*)\z/)

      value.to_i
    end

    def parse_time(value)
      return nil unless value.is_a?(String)

      Time.iso8601(value)
    rescue ArgumentError
      nil
    end

    def check(issues, condition, message)
      issues << message unless condition
    end
  end
end
