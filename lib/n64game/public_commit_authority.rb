# frozen_string_literal: true

require "open3"

module N64Game
  module PublicCommitAuthority
    REPOSITORY = "oh-ashen-one/n64game".freeze
    PUBLIC_URL = "https://github.com/#{REPOSITORY}.git".freeze
    HEX40 = /\A[0-9a-f]{40}\z/.freeze
    BRANCH_REF = /\Arefs\/heads\/[A-Za-z0-9][A-Za-z0-9._\/-]*\z/.freeze
    PULL_HEAD_REF = /\Arefs\/pull\/[1-9][0-9]*\/head\z/.freeze
    PULL_MERGE_REF = /\Arefs\/pull\/[1-9][0-9]*\/merge\z/.freeze

    class Violation < StandardError
      attr_reader :issues

      def initialize(issues)
        @issues = issues.freeze
        super(issues.join("; "))
      end
    end

    module_function

    def select_advertised_ref!(head:, status_bytes:, advertised_bytes:, branch_ref_valid:)
      issues = []
      issues << "public concept authority requires a clean worktree and index" unless status_bytes == ""
      issues << "public concept authority HEAD is malformed" unless head.is_a?(String) && HEX40.match?(head)
      issues << "public concept authority advertised-ref response must be a String" unless advertised_bytes.is_a?(String)
      issues << "public concept authority requires a branch-ref validator" unless branch_ref_valid.respond_to?(:call)
      raise Violation.new(issues) unless issues.empty?

      rows = []
      advertised_bytes.lines.each_with_index do |line, index|
        row = line.chomp
        match = row.match(/\A([0-9a-f]{40})\t([^\t\r\n]+)\z/)
        unless match
          issues << "advertised-ref row #{index + 1} is malformed"
          next
        end
        oid = match[1]
        ref = match[2]
        kind = ref_kind(ref, branch_ref_valid)
        unless kind
          issues << "advertised ref is outside the allowed branch/PR namespace: #{ref}"
          next
        end
        rows << [oid, ref, kind]
      end

      rows = rows.uniq
      rows.group_by { |row| row[1] }.each do |ref, ref_rows|
        issues << "advertised ref has conflicting object IDs: #{ref}" if ref_rows.map(&:first).uniq.length != 1
      end
      matching = rows.select { |oid, _ref, _kind| oid == head }
      issues << "current HEAD is not the tip of an allowed advertised public ref" if matching.empty?
      raise Violation.new(issues) unless issues.empty?

      selected = matching.sort_by { |_oid, ref, kind| [kind_rank(kind), ref.b] }.first
      { "commit" => selected[0], "ref" => selected[1], "kind" => selected[2] }
    end

    def verify_fetched_ref!(expected_head:, fetched_oid:)
      issues = []
      issues << "expected public concept HEAD is malformed" unless expected_head.is_a?(String) && HEX40.match?(expected_head)
      issues << "explicitly fetched advertised ref did not resolve to a canonical commit" unless
        fetched_oid.is_a?(String) && HEX40.match?(fetched_oid)
      issues << "advertised public ref moved or disappeared during verification" unless fetched_oid == expected_head
      raise Violation.new(issues) unless issues.empty?

      true
    end

    def clone_and_fetch!(remote_url:, selected_ref:, expected_head:, root:, env:)
      issues = []
      issues << "public authority remote URL is missing" unless remote_url.is_a?(String) && !remote_url.empty?
      issues << "public authority selected ref is malformed" unless
        selected_ref.is_a?(String) && (BRANCH_REF.match?(selected_ref) ||
          PULL_HEAD_REF.match?(selected_ref) || PULL_MERGE_REF.match?(selected_ref))
      issues << "public authority expected HEAD is malformed" unless
        expected_head.is_a?(String) && HEX40.match?(expected_head)
      issues << "public authority clone root is missing or unsafe" unless
        root.is_a?(String) && File.directory?(root) && !File.symlink?(root)
      issues << "public authority clone environment must be explicit" unless env.is_a?(Hash)
      raise Violation.new(issues) unless issues.empty?

      clone = File.join(root, "repo")
      command_prefix = ["/usr/bin/git", "-c", "credential.helper=", "-c", "http.extraHeader="]
      _clone_out, clone_error, clone_status = Open3.capture3(
        env, *command_prefix, "clone", "--no-checkout", "--no-tags", "--quiet",
        remote_url, clone, chdir: root, unsetenv_others: true
      )
      unless clone_status.success?
        raise Violation.new(["credential-free fresh clone failed: #{clone_error.lines.first.to_s.strip}"])
      end

      destination_ref = "refs/n64game/public-concept-authority"
      _fetch_out, fetch_error, fetch_status = Open3.capture3(
        env, *command_prefix, "fetch", "--force", "--no-tags", remote_url,
        "+#{selected_ref}:#{destination_ref}", chdir: clone, unsetenv_others: true
      )
      unless fetch_status.success?
        raise Violation.new([
          "selected advertised ref moved/disappeared during explicit fetch: #{fetch_error.lines.first.to_s.strip}"
        ])
      end
      fetched_out, fetched_error, fetched_status = Open3.capture3(
        env, *command_prefix, "rev-parse", "#{destination_ref}^{commit}",
        chdir: clone, unsetenv_others: true
      )
      unless fetched_status.success?
        raise Violation.new([
          "cannot resolve explicitly fetched advertised ref: #{fetched_error.lines.first.to_s.strip}"
        ])
      end
      verify_fetched_ref!(expected_head: expected_head, fetched_oid: fetched_out.strip)

      _lfs_out, lfs_error, lfs_status = Open3.capture3(
        env, *command_prefix, "lfs", "fetch", remote_url, expected_head, destination_ref,
        chdir: clone, unsetenv_others: true
      )
      unless lfs_status.success?
        raise Violation.new(["fresh-clone Git LFS fetch failed: #{lfs_error.lines.first.to_s.strip}"])
      end
      clone
    end

    def validate_control_transaction!(public_head:, control_commit:, parents:, reviewed_payload_commit:,
                                      changed_paths:, current_descends_from_control:, control_public:,
                                      control_bytes_equal:, public_tree_equal:)
      issues = []
      issues << "current public revision is malformed" unless public_head.is_a?(String) && HEX40.match?(public_head)
      issues << "benchmark control commit is malformed" unless control_commit.is_a?(String) && HEX40.match?(control_commit)
      issues << "reviewed payload commit is malformed" unless
        reviewed_payload_commit.is_a?(String) && HEX40.match?(reviewed_payload_commit)
      issues << "benchmark control commit must have exactly one parent" unless
        parents.is_a?(Array) && parents.length == 1 && parents.first.is_a?(String) && HEX40.match?(parents.first)
      if parents.is_a?(Array) && parents.length == 1
        issues << "benchmark control parent differs from Reviewed payload Git commit" unless
          parents.first == reviewed_payload_commit
      end
      issues << "payload-to-control transaction must change only docs/VISUAL_BENCHMARK_APPROVAL.md" unless
        changed_paths == ["docs/VISUAL_BENCHMARK_APPROVAL.md"]
      issues << "current advertised public revision does not descend from the benchmark control commit" unless
        current_descends_from_control == true
      issues << "benchmark control commit is not present in the verified public clone" unless control_public == true
      issues << "benchmark control bytes at the transaction commit differ from current public control bytes" unless
        control_bytes_equal == true
      issues << "current advertised revision tree differs from the benchmark control transaction tree" unless
        public_tree_equal == true
      raise Violation.new(issues) unless issues.empty?

      true
    end

    def ref_kind(ref, branch_ref_valid)
      return "branch" if BRANCH_REF.match?(ref) && branch_ref_valid.call(ref)
      return "pull_head" if PULL_HEAD_REF.match?(ref)
      return "pull_merge" if PULL_MERGE_REF.match?(ref)

      nil
    end

    def kind_rank(kind)
      { "branch" => 0, "pull_head" => 1, "pull_merge" => 2 }.fetch(kind, 3)
    end
  end
end
