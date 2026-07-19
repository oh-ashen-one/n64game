from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RUBY = "/usr/bin/ruby"
ZERO_SHA = "0" * 64

CONCEPT_ID = "prop.annex.monitor_console"
CONCEPT_EVIDENCE = f"review/{CONCEPT_ID}/g1/EVIDENCE_MANIFEST.sha256"
CONCEPT_REVIEW = f"review/{CONCEPT_ID}/g1/REVIEW.md"
CONCEPT_CAPTURE = f"review/{CONCEPT_ID}/g1/concept_front.txt"

ATTEMPT_ROOT = f"review/{CONCEPT_ID}/g1/attempts/0001"
ATTEMPT_EVIDENCE = f"{ATTEMPT_ROOT}/EVIDENCE_MANIFEST.sha256"
ATTEMPT_REVIEW = f"{ATTEMPT_ROOT}/REVIEW.md"
ATTEMPT_CAPTURE = f"{ATTEMPT_ROOT}/rejected_front.txt"


RUBY_ADAPTER = r"""
  require 'json'

  validator = ARGV.fetch(0)
  repository = ARGV.fetch(1)
  source = File.binread(validator)
  marker = "\nart = read(\"docs/ART_BIBLE.md\")\n"
  prefix, remainder = source.split(marker, 2)
  abort 'validator main marker missing' unless prefix && remainder
  eval(prefix, TOPLEVEL_BINDING, validator, 1)

  input = JSON.parse(STDIN.read)
  commit = input.fetch('commit')
  results = {}

  input.fetch('reviews').each do |kind, review_input|
    context = new_manifest_context
    evidence_path = review_input.fetch('evidence_path')
    evidence_sha = review_input.fetch('evidence_sha')
    review_path = review_input.fetch('review_path')
    label = "#{kind} review DAG fixture"

    validate_manifest(
      evidence_path, review_input.fetch('manifest_binding_sha'), label, [],
      commit, repository, context
    )
    outside = review_outside_evidence_manifest?(context, evidence_path, review_path)
    error("#{label}: review must remain outside its evidence manifest") unless outside

    keys = kind == 'concept' ? CONCEPT_REVIEW_RECORD_KEYS : GATE_ATTEMPT_REVIEW_KEYS
    review = parse_machine_record(
      "#{review_path}@#{review_input.fetch('review_binding_sha')}", label, keys,
      commit: commit, fresh_clone: repository, record_context: context
    )
    if review_input.fetch('check_evidence_binding')
      require_exact_report_fields(
        review,
        {
          'schema' => review_input.fetch('schema'),
          'evidence_manifest' => "#{evidence_path}@#{evidence_sha}"
        },
        label
      )
    end
    results[kind] = {
      'outside' => outside,
      'evidence_manifest' => review['evidence_manifest']
    }
  end

  STDOUT.write(JSON.generate({ 'issues' => ERRORS, 'results' => results }))
"""


class ConceptReviewManifestDagTests(unittest.TestCase):
    @staticmethod
    def ruby_function_body(source: str, name: str) -> str:
        start = re.search(rf"^def {re.escape(name)}\b", source, flags=re.MULTILINE)
        if start is None:
            raise AssertionError(f"missing Ruby function: {name}")
        following = source[start.end() :]
        next_function = re.search(r"^def ", following, flags=re.MULTILINE)
        end = start.end() + next_function.start() if next_function else len(source)
        return source[start.start() : end]

    def test_production_concept_and_attempt_paths_enforce_external_reviews(self) -> None:
        source = (ROOT / "scripts/validate-asset-contract").read_text(encoding="utf-8")
        attempt_body = self.ruby_function_body(source, "validate_gate1_attempt_history")
        concept_body = self.ruby_function_body(source, "validate_concept_entries")

        for label, body in (
            ("Gate-1 attempt history", attempt_body),
            ("current concept", concept_body),
        ):
            with self.subTest(label=label):
                self.assertIn("review_outside_evidence_manifest?(", body)

    @staticmethod
    def git_env() -> dict[str, str]:
        return {
            "PATH": "/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "N64Game Concept DAG Test",
            "GIT_AUTHOR_EMAIL": "concept-dag@example.invalid",
            "GIT_COMMITTER_NAME": "N64Game Concept DAG Test",
            "GIT_COMMITTER_EMAIL": "concept-dag@example.invalid",
        }

    @staticmethod
    def digest(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def manifest(cls, rows: list[tuple[str, bytes, str]]) -> bytes:
        lines = []
        for path, data, role in sorted(rows, key=lambda row: row[0].encode("utf-8")):
            lines.append(
                "\t".join(
                    (
                        path,
                        str(len(data)),
                        cls.digest(data),
                        "build:-",
                        "capture:-",
                        f"role:{role}",
                    )
                )
            )
        return ("\n".join(lines) + "\n").encode("utf-8")

    @staticmethod
    def concept_review(evidence_sha: str) -> bytes:
        source_path = f"assets-src/prop/{CONCEPT_ID}/SOURCE_MANIFEST.sha256"
        return (
            "schema: n64game-concept-review-v1\n"
            f"production_id: {CONCEPT_ID}\n"
            "stage: G1_CONCEPT\n"
            "creator_id: artist.alex-042\n"
            f"source_manifest: {source_path}@{'a' * 64}\n"
            f"evidence_manifest: {CONCEPT_EVIDENCE}@{evidence_sha}\n"
            "status: IN_PROGRESS\n"
            "updated_at: 2026-07-19T12:00:00Z\n"
            "rationale: Refining the authored console silhouette and material hierarchy.\n"
        ).encode("utf-8")

    @staticmethod
    def attempt_review(evidence_sha: str) -> bytes:
        return (
            "schema: n64game-g1-attempt-review-v1\n"
            f"production_id: {CONCEPT_ID}\n"
            "attempt_id: G1-0001\n"
            "gate: G1\n"
            "decision: fail\n"
            "reviewer_id: reviewer.morgan-017\n"
            "reviewer_non_owner: YES\n"
            f"source_manifest_sha256: {'a' * 64}\n"
            "output_manifest_sha256: NONE\n"
            f"evidence_manifest: {ATTEMPT_EVIDENCE}@{evidence_sha}\n"
            "build_id: -\n"
            "decided_at: 2026-07-19T12:30:00Z\n"
            "defect_ids: ART_SILHOUETTE_DRIFT\n"
            "disposition: REVISE\n"
            "rationale: The rejected front view loses the approved three-lobe console identity.\n"
        ).encode("utf-8")

    @classmethod
    def add_review_graph(
        cls,
        blobs: dict[str, bytes],
        *,
        kind: str,
        layout: str,
        stale_embedded_evidence: bool,
    ) -> dict[str, Any]:
        if kind == "concept":
            evidence_path, review_path, capture_path = (
                CONCEPT_EVIDENCE,
                CONCEPT_REVIEW,
                CONCEPT_CAPTURE,
            )
            review_builder = cls.concept_review
            schema = "n64game-concept-review-v1"
            review_role = "concept.review"
            capture_role = "concept.orthographic"
        else:
            evidence_path, review_path, capture_path = (
                ATTEMPT_EVIDENCE,
                ATTEMPT_REVIEW,
                ATTEMPT_CAPTURE,
            )
            review_builder = cls.attempt_review
            schema = "n64game-g1-attempt-review-v1"
            review_role = "gate.attempt_review"
            capture_role = "gate.attempt_capture"

        capture = f"{kind} evidence bytes are independently manifest-owned.\n".encode()
        blobs[capture_path] = capture

        if layout == "external":
            evidence = cls.manifest([(capture_path, capture, capture_role)])
            evidence_sha = cls.digest(evidence)
            review = review_builder(ZERO_SHA if stale_embedded_evidence else evidence_sha)
        elif layout == "direct":
            review = review_builder(ZERO_SHA)
            evidence = cls.manifest(
                [
                    (capture_path, capture, capture_role),
                    (review_path, review, review_role),
                ]
            )
            evidence_sha = cls.digest(evidence)
        elif layout == "nested":
            review = review_builder(ZERO_SHA)
            nested_path = evidence_path.replace(
                "EVIDENCE_MANIFEST.sha256", "nested/EVIDENCE_MANIFEST.sha256"
            )
            nested = cls.manifest([(review_path, review, review_role)])
            blobs[nested_path] = nested
            evidence = cls.manifest([(nested_path, nested, "evidence.manifest")])
            evidence_sha = cls.digest(evidence)
        else:
            raise AssertionError(f"unknown layout: {layout}")

        blobs[evidence_path] = evidence
        blobs[review_path] = review
        return {
            "evidence_path": evidence_path,
            "evidence_sha": evidence_sha,
            "review_path": review_path,
            "review_sha": cls.digest(review),
            "schema": schema,
        }

    def make_repository(
        self,
        parent: Path,
        *,
        concept_layout: str = "external",
        attempt_layout: str = "external",
        stale_concept_evidence: bool = False,
        stale_attempt_evidence: bool = False,
    ) -> tuple[Path, str, dict[str, dict[str, Any]]]:
        repo = parent / "repo"
        repo.mkdir()
        blobs: dict[str, bytes] = {}
        graph = {
            "concept": self.add_review_graph(
                blobs,
                kind="concept",
                layout=concept_layout,
                stale_embedded_evidence=stale_concept_evidence,
            ),
            "attempt": self.add_review_graph(
                blobs,
                kind="attempt",
                layout=attempt_layout,
                stale_embedded_evidence=stale_attempt_evidence,
            ),
        }
        for relative, data in blobs.items():
            target = repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)

        env = self.git_env()
        subprocess.run(["/usr/bin/git", "init", "-q"], cwd=repo, env=env, check=True)
        subprocess.run(["/usr/bin/git", "add", "--", "."], cwd=repo, env=env, check=True)
        subprocess.run(
            ["/usr/bin/git", "commit", "-q", "-m", "concept review DAG fixture"],
            cwd=repo,
            env=env,
            check=True,
        )
        commit = subprocess.check_output(
            ["/usr/bin/git", "rev-parse", "HEAD"], cwd=repo, env=env, text=True
        ).strip()
        return repo, commit, graph

    def run_adapter(
        self,
        repo: Path,
        commit: str,
        graph: dict[str, dict[str, Any]],
        *,
        overrides: dict[str, dict[str, Any]] | None = None,
        check_evidence_binding: bool = True,
    ) -> dict[str, Any]:
        review_inputs: dict[str, dict[str, Any]] = {}
        for kind, values in graph.items():
            review_inputs[kind] = {
                "evidence_path": values["evidence_path"],
                "evidence_sha": values["evidence_sha"],
                "manifest_binding_sha": values["evidence_sha"],
                "review_path": values["review_path"],
                "review_binding_sha": values["review_sha"],
                "schema": values["schema"],
                "check_evidence_binding": check_evidence_binding,
            }
            review_inputs[kind].update((overrides or {}).get(kind, {}))

        completed = subprocess.run(
            [
                RUBY,
                "--disable-gems",
                "-e",
                RUBY_ADAPTER,
                str(ROOT / "scripts/validate-asset-contract"),
                str(repo),
            ],
            input=json.dumps({"commit": commit, "reviews": review_inputs}),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=self.git_env(),
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def test_external_current_concept_and_attempt_reviews_retain_evidence_path_hash(self) -> None:
        with tempfile.TemporaryDirectory(prefix="n64game-concept-dag-") as temporary:
            repo, commit, graph = self.make_repository(Path(temporary))
            result = self.run_adapter(repo, commit, graph)

        self.assertEqual(result["issues"], [], result)
        for kind, values in graph.items():
            with self.subTest(kind=kind):
                self.assertTrue(result["results"][kind]["outside"])
                self.assertEqual(
                    result["results"][kind]["evidence_manifest"],
                    f"{values['evidence_path']}@{values['evidence_sha']}",
                )

    def test_direct_and_transitively_nested_review_membership_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="n64game-concept-cycle-") as temporary:
            repo, commit, graph = self.make_repository(
                Path(temporary), concept_layout="direct", attempt_layout="nested"
            )
            result = self.run_adapter(
                repo, commit, graph, check_evidence_binding=False
            )

        self.assertFalse(result["results"]["concept"]["outside"])
        self.assertFalse(result["results"]["attempt"]["outside"])
        self.assertTrue(
            any("concept review DAG fixture: review must remain outside" in issue for issue in result["issues"]),
            result,
        )
        self.assertTrue(
            any("attempt review DAG fixture: review must remain outside" in issue for issue in result["issues"]),
            result,
        )

    def test_stale_manifest_review_and_embedded_evidence_hashes_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="n64game-concept-stale-locator-") as temporary:
            repo, commit, graph = self.make_repository(Path(temporary))
            locator_result = self.run_adapter(
                repo,
                commit,
                graph,
                overrides={
                    "concept": {"manifest_binding_sha": ZERO_SHA},
                    "attempt": {"review_binding_sha": ZERO_SHA},
                },
            )
        self.assertTrue(
            any("concept review DAG fixture manifest SHA-256 mismatch" in issue for issue in locator_result["issues"]),
            locator_result,
        )
        self.assertTrue(
            any("attempt review DAG fixture SHA-256 mismatch" in issue for issue in locator_result["issues"]),
            locator_result,
        )

        with tempfile.TemporaryDirectory(prefix="n64game-concept-stale-embedded-") as temporary:
            repo, commit, graph = self.make_repository(
                Path(temporary), stale_concept_evidence=True, stale_attempt_evidence=True
            )
            embedded_result = self.run_adapter(repo, commit, graph)
        mismatches = [
            issue for issue in embedded_result["issues"]
            if "recomputed evidence_manifest mismatch" in issue
        ]
        self.assertEqual(len(mismatches), 2, embedded_result)


if __name__ == "__main__":
    unittest.main()
