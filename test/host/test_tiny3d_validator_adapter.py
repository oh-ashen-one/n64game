from __future__ import annotations

import json
import hashlib
import os
import subprocess
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from test_tiny3d_package_contract import (
    ANIMATION_HEADER_PATH,
    BINDING_PATH,
    BUILD_ID,
    MODEL_PATHS,
    STREAM_PATHS,
    fixture,
)


ROOT = Path(__file__).resolve().parents[2]
RUBY = "/usr/bin/ruby"
MODEL_MANIFEST = "review/echo.quarrune/g5/OUTPUT_MANIFEST.sha256"
ANIMATION_MANIFEST = "review/anm.echo.quarrune/g5/OUTPUT_MANIFEST.sha256"
MODEL_MANIFEST_SHA = "a" * 64
ANIMATION_MANIFEST_SHA = "b" * 64


class Tiny3DValidatorAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="n64game-tiny3d-adapter-")
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def git_env() -> dict[str, str]:
        return {
            "PATH": "/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
        }

    def commit_materialized_files(
        self,
        values: dict[str, object],
        *,
        ordinary_binary: str | None = None,
        executable_path: str | None = None,
        omit_lfs_object: str | None = None,
        extra_git_blobs: dict[str, bytes] | None = None,
    ) -> str:
        env = self.git_env()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, env=env, check=True)
        attributes = (
            "review/**/*.t3dm filter=lfs diff=lfs merge=lfs -text\n"
            "review/**/*.sdata filter=lfs diff=lfs merge=lfs -text\n"
            "review/**/SKELETON_BINDING.tsv text eol=lf\n"
        ).encode()
        blobs: dict[str, tuple[bytes, str]] = {".gitattributes": (attributes, "100644")}
        materialized = values["bytes"]
        assert isinstance(materialized, dict)
        for path, raw in materialized.items():
            assert isinstance(path, str) and isinstance(raw, bytes)
            if path == BINDING_PATH:
                blob = raw
            elif path == ordinary_binary:
                blob = raw
            else:
                digest = __import__("hashlib").sha256(raw).hexdigest()
                blob = (
                    "version https://git-lfs.github.com/spec/v1\n"
                    f"oid sha256:{digest}\n"
                    f"size {len(raw)}\n"
                ).encode()
                if path != omit_lfs_object:
                    location = self.repo / ".git" / "lfs" / "objects" / digest[:2] / digest[2:4] / digest
                    location.parent.mkdir(parents=True, exist_ok=True)
                    location.write_bytes(raw)
            blobs[path] = (blob, "100755" if path == executable_path else "100644")
        for path, blob in (extra_git_blobs or {}).items():
            blobs[path] = (blob, "100644")

        for path, (blob, mode) in blobs.items():
            oid = subprocess.run(
                ["git", "hash-object", "-w", "--stdin"],
                cwd=self.repo,
                env=env,
                input=blob,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            ).stdout.decode().strip()
            subprocess.run(
                ["git", "update-index", "--add", "--cacheinfo", f"{mode},{oid},{path}"],
                cwd=self.repo,
                env=env,
                check=True,
            )
        commit_env = {
            **env,
            "GIT_AUTHOR_NAME": "N64Game Test",
            "GIT_AUTHOR_EMAIL": "n64game-test@example.invalid",
            "GIT_COMMITTER_NAME": "N64Game Test",
            "GIT_COMMITTER_EMAIL": "n64game-test@example.invalid",
        }
        subprocess.run(["git", "commit", "-q", "-m", "Tiny3D adapter fixture"], cwd=self.repo, env=commit_env, check=True)
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo, env=env, text=True).strip()

    @staticmethod
    def context(values: dict[str, object], include_model: bool = True, include_animation: bool = True) -> dict[str, object]:
        manifests: dict[str, object] = {}
        digests: dict[str, str] = {}
        model_entries = deepcopy(values["model_entries"])
        animation_entries = deepcopy(values["animation_entries"])
        if include_model:
            manifests[MODEL_MANIFEST] = model_entries
            digests[MODEL_MANIFEST] = MODEL_MANIFEST_SHA
        if include_animation:
            manifests[ANIMATION_MANIFEST] = animation_entries
            digests[ANIMATION_MANIFEST] = ANIMATION_MANIFEST_SHA
        return {"manifests": manifests, "manifest_digests": digests}

    def adapter(
        self,
        values: dict[str, object],
        commit: str,
        *,
        model_output: bool = True,
        animation_output: bool = True,
        outputs_required: bool = True,
        split_context: bool = False,
        primary_digest_overrides: dict[str, str] | None = None,
        duplicate_fallback: bool = False,
        nested_relevant: bool = False,
    ) -> list[str]:
        primary = self.context(values, include_model=True, include_animation=not split_context)
        if primary_digest_overrides:
            primary["manifest_digests"].update(primary_digest_overrides)
        if nested_relevant:
            direct = primary["manifests"][MODEL_MANIFEST]
            nested = next(entry for entry in direct if entry["path"] == MODEL_PATHS[1])
            direct.remove(nested)
            primary["manifests"][MODEL_PATHS[0]] = [nested]
        fallback = None
        if split_context:
            fallback = self.context(values, include_model=False, include_animation=True)
        elif duplicate_fallback:
            fallback = self.context(values, include_model=True, include_animation=True)
        payload = {
            "model_output": {
                "manifest_path": MODEL_MANIFEST,
                "manifest_sha256": MODEL_MANIFEST_SHA,
                "build_id": BUILD_ID,
            } if model_output else None,
            "animation_output": {
                "manifest_path": ANIMATION_MANIFEST,
                "manifest_sha256": ANIMATION_MANIFEST_SHA,
                "build_id": BUILD_ID,
            } if animation_output else None,
            "primary": primary,
            "fallback": fallback,
            "commit": commit,
            "outputs_required": outputs_required,
        }
        program = r"""
          require 'json'
          validator = ARGV.fetch(0)
          source = File.binread(validator)
          marker = "\nart = read(\"docs/ART_BIBLE.md\")\n"
          prefix, remainder = source.split(marker, 2)
          abort 'validator main marker missing' unless prefix && remainder
          eval(prefix, TOPLEVEL_BINDING, validator, 1)
          input = JSON.parse(STDIN.read)
          make_context = lambda do |raw|
            next nil unless raw
            context = new_manifest_context
            raw.fetch('manifests').each do |manifest, entries|
              normalized = entries.map { |entry| entry.each_with_object({}) { |(key, value), row| row[key.to_sym] = value } }
              context[:manifests][manifest] = normalized
              normalized.each do |entry|
                context[:entries][entry[:path]] = entry
                context[:member_owner][entry[:path]] = manifest
                context[:closure] << entry[:path]
              end
              context[:closure] << manifest
            end
            raw.fetch('manifest_digests').each { |path, digest| context[:manifest_digests][path] = digest }
            context
          end
          symbolize = lambda do |raw|
            raw && raw.each_with_object({}) { |(key, value), result| result[key.to_sym] = value }
          end
          validate_quarrune_tiny3d_pair(
            model_output: symbolize.call(input['model_output']),
            animation_output: symbolize.call(input['animation_output']),
            payload_context: make_context.call(input['primary']),
            fallback_context: make_context.call(input['fallback']),
            commit: input['commit'], fresh_clone: ARGV.fetch(1),
            label: 'adapter fixture', outputs_required: input['outputs_required']
          )
          STDOUT.write(JSON.generate(ERRORS))
        """
        completed = subprocess.run(
            [RUBY, "--disable-gems", "-e", program, str(ROOT / "scripts/validate-asset-contract"), str(self.repo)],
            input=json.dumps(payload),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=self.git_env(),
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    @staticmethod
    def manifest_bytes(entries: list[dict[str, object]]) -> bytes:
        lines = []
        for row in sorted(entries, key=lambda value: str(value["path"])):
            lines.append(
                "\t".join((
                    str(row["path"]), str(row["count"]), str(row["digest"]),
                    f"build:{row['build']}", f"capture:{row['capture']}", f"role:{row['role']}",
                ))
            )
        return ("\n".join(lines) + "\n").encode()

    def test_real_adapter_materializes_canonical_lfs_pair(self) -> None:
        values = fixture()
        commit = self.commit_materialized_files(values)
        self.assertEqual(self.adapter(values, commit), [])

    def test_changed_postapproval_split_context_revalidates_historical_counterpart(self) -> None:
        values = fixture()
        commit = self.commit_materialized_files(values)
        self.assertEqual(self.adapter(values, commit, split_context=True), [])

    def test_adapter_rejects_missing_counterpart_and_required_empty_pair(self) -> None:
        values = fixture()
        commit = self.commit_materialized_files(values)
        issues = self.adapter(values, commit, animation_output=False)
        self.assertTrue(any("atomically" in issue for issue in issues), issues)
        issues = self.adapter(values, commit, model_output=False, animation_output=False)
        self.assertTrue(any("both Quarrune Tiny3D packages are required" in issue for issue in issues), issues)

        self.assertEqual(
            self.adapter(values, commit, model_output=False, animation_output=False, outputs_required=False), []
        )
        issues = self.adapter(values, commit, animation_output=False, outputs_required=False)
        self.assertTrue(any("atomically" in issue for issue in issues), issues)

    def test_adapter_rejects_stale_primary_and_nested_relevant_members(self) -> None:
        values = fixture()
        commit = self.commit_materialized_files(values)
        issues = self.adapter(
            values, commit, duplicate_fallback=True,
            primary_digest_overrides={MODEL_MANIFEST: "c" * 64},
        )
        self.assertTrue(any("digest differs from the selected lifecycle row" in issue for issue in issues), issues)

        issues = self.adapter(values, commit, nested_relevant=True)
        self.assertTrue(any("must be a direct output-manifest member" in issue for issue in issues), issues)

    def test_real_manifests_populate_context_before_pair_adapter(self) -> None:
        values = fixture()
        model_manifest = self.manifest_bytes(values["model_entries"])
        animation_manifest = self.manifest_bytes(values["animation_entries"])
        model_sha = hashlib.sha256(model_manifest).hexdigest()
        animation_sha = hashlib.sha256(animation_manifest).hexdigest()
        commit = self.commit_materialized_files(
            values,
            extra_git_blobs={MODEL_MANIFEST: model_manifest, ANIMATION_MANIFEST: animation_manifest},
        )
        payload = {
            "commit": commit, "model_sha": model_sha, "animation_sha": animation_sha,
        }
        program = r"""
          require 'json'
          validator = ARGV.fetch(0)
          source = File.binread(validator)
          marker = "\nart = read(\"docs/ART_BIBLE.md\")\n"
          prefix, remainder = source.split(marker, 2)
          abort 'validator main marker missing' unless prefix && remainder
          eval(prefix, TOPLEVEL_BINDING, validator, 1)
          input = JSON.parse(STDIN.read)
          context = new_manifest_context
          validate_manifest(
            'review/echo.quarrune/g5/OUTPUT_MANIFEST.sha256', input.fetch('model_sha'),
            'real model manifest', [], input.fetch('commit'), ARGV.fetch(1), context
          )
          validate_manifest(
            'review/anm.echo.quarrune/g5/OUTPUT_MANIFEST.sha256', input.fetch('animation_sha'),
            'real animation manifest', [], input.fetch('commit'), ARGV.fetch(1), context
          )
          validate_quarrune_tiny3d_pair(
            model_output: {
              manifest_path: 'review/echo.quarrune/g5/OUTPUT_MANIFEST.sha256',
              manifest_sha256: input.fetch('model_sha'), build_id: 'n64game-g5-fixture-001'
            },
            animation_output: {
              manifest_path: 'review/anm.echo.quarrune/g5/OUTPUT_MANIFEST.sha256',
              manifest_sha256: input.fetch('animation_sha'), build_id: 'n64game-g5-fixture-001'
            },
            payload_context: context, commit: input.fetch('commit'), fresh_clone: ARGV.fetch(1),
            label: 'real parsed manifests', outputs_required: true
          )
          STDOUT.write(JSON.generate(ERRORS))
        """
        completed = subprocess.run(
            [RUBY, "--disable-gems", "-e", program, str(ROOT / "scripts/validate-asset-contract"), str(self.repo)],
            input=json.dumps(payload), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False, env=self.git_env(),
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout), [])

    def test_adapter_rejects_missing_lfs_object_ordinary_binary_and_executable(self) -> None:
        cases = (
            ("missing_object", {"omit_lfs_object": MODEL_PATHS[1]}, "LFS object is not retrievable/valid"),
            ("ordinary_binary", {"ordinary_binary": ANIMATION_HEADER_PATH}, "filter=lfs but reviewed blob is not"),
            ("executable", {"executable_path": STREAM_PATHS[0]}, "mode 100644"),
        )
        for name, kwargs, expected in cases:
            with self.subTest(case=name):
                self.tearDown()
                self.setUp()
                values = fixture()
                commit = self.commit_materialized_files(values, **kwargs)
                issues = self.adapter(values, commit)
                self.assertTrue(any(expected in issue for issue in issues), issues)

    def test_validator_contains_all_lifecycle_callsites_and_keeps_export_locked(self) -> None:
        validator = (ROOT / "scripts/validate-asset-contract").read_text(encoding="utf-8")
        for label in (
            "preapproval Quarrune Tiny3D package pair",
            "approved Quarrune Tiny3D package pair",
            "current unchanged post-approval Quarrune Tiny3D package pair",
            "current post-approval Quarrune Tiny3D package pair",
        ):
            self.assertIn(label, validator)
        self.assertEqual(validator.count("validate_quarrune_tiny3d_pair("), 5)  # definition + four calls
        self.assertIn('require ROOT.join("lib/n64game/tiny3d_package_contract").to_s', validator)
        self.assertIn("fallback_context: historical_context", validator)
        lock = (ROOT / "lib/n64game/authoring_stack_receipt.rb").read_text(encoding="utf-8")
        self.assertIn("GATE5_EXPORT_IMPLEMENTED = false", lock)
        self.assertIn('APPROVED_GATE5_EXPORTER_SHA256 = "PENDING"', lock)
        self.assertIn('"lib/n64game/tiny3d_package_contract.rb"', lock)
        self.assertIn('"scripts/validate-asset-contract"', lock)


if __name__ == "__main__":
    unittest.main()
