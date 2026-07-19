from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "test" / "host"))

import n64game_gate5_export as gate5  # noqa: E402


fixture_contract = importlib.import_module("test_tiny3d_package_contract")
BUILD_ID = fixture_contract.BUILD_ID


def manifest_entry(value: dict[str, object]) -> gate5.ManifestEntry:
    return gate5.ManifestEntry(
        path=str(value["path"]),
        count=int(value["count"]),
        digest=str(value["digest"]),
        build=str(value["build"]),
        capture=str(value["capture"]),
        role=str(value["role"]),
        kind=str(value["kind"]),
        mode=str(value["mode"]),
    )


def write_fixture(stage: Path, values: dict[str, object]) -> None:
    byte_values: dict[str, bytes] = values["bytes"]  # type: ignore[assignment]
    for relative, payload in byte_values.items():
        path = stage / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        path.chmod(0o644)
    model = [manifest_entry(value) for value in values["model_entries"]]  # type: ignore[index]
    animation = [manifest_entry(value) for value in values["animation_entries"]]  # type: ignore[index]
    for relative, entries in (
        (gate5.MODEL_MANIFEST_PATH, model),
        (gate5.ANIMATION_MANIFEST_PATH, animation),
    ):
        path = stage / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gate5.render_manifest(entries))
        path.chmod(0o644)


def source_row(
    scope: str, path: str, selectors: tuple[str, ...], role: str = "source.authored"
) -> gate5.AllowlistRow:
    digest = hashlib.sha256(path.encode()).hexdigest()
    return gate5.AllowlistRow(scope, "a" * 64, "SOURCE", path, digest, role, selectors)


def minimal_glb(animation_names: tuple[str, ...] = ()) -> bytes:
    document: dict[str, object] = {"asset": {"version": "2.0"}}
    if animation_names:
        document["animations"] = [{"name": name} for name in reversed(animation_names)]
    payload = json.dumps(document, separators=(",", ":")).encode()
    payload += b" " * ((-len(payload)) % 4)
    return b"glTF" + struct.pack("<II", 2, 12 + 8 + len(payload)) + struct.pack(
        "<II", len(payload), 0x4E4F534A
    ) + payload


GATE_ROLES = {
    1: (
        "concept.construction", "concept.silhouette", "concept.orthographic",
        "concept.functional", "concept.scale", "concept.palette", "concept.rig",
        "concept.clean_room",
    ),
    2: (
        "technical.statistics", "technical.topology", "technical.normals", "technical.uv",
        "technical.transform", "technical.naming", "technical.weights",
        "technical.deformation", "technical.validation",
    ),
    3: (
        "turntable.contact_sheet", "turntable.neutral", "turntable.game_light",
        "turntable.native_crop", "turntable.texture", "turntable.peer_comparison",
    ),
    4: (
        "animation.reel", "animation.event_table", "animation.contact_sheet",
        "animation.contact_overlay", "animation.deformation", "animation.transition",
        "animation.sync",
    ),
}


def checker_bundle_sha256(root: Path) -> str:
    digest = hashlib.sha256(b"n64game-authoring-checker-bundle-v1\n")
    for relative in sorted(gate5.AUTHORING_CHECKER_PATHS):
        digest.update(
            f"{relative}\t{hashlib.sha256((root / relative).read_bytes()).hexdigest()}\n".encode()
        )
    return digest.hexdigest()


def stage_index_blob(root: Path, relative: str, data: bytes, mode: str = "100644") -> str:
    result = subprocess.run(
        ["/usr/bin/git", "hash-object", "-w", "--stdin"],
        cwd=root, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    oid = result.stdout.decode("ascii").strip()
    subprocess.run(
        ["/usr/bin/git", "update-index", "--add", "--cacheinfo", f"{mode},{oid},{relative}"],
        cwd=root, check=True,
    )
    return oid


def lfs_pointer(data: bytes, *, digest: str | None = None) -> bytes:
    return (
        "version https://git-lfs.github.com/spec/v1\n"
        f"oid sha256:{digest or hashlib.sha256(data).hexdigest()}\n"
        f"size {len(data)}\n"
    ).encode()


def write_gate_authority_fixture(
    root: Path,
    *,
    g1_non_owner: str = "YES",
    g3_non_owner: str = "YES",
    g2_gate_build: str = "-",
    missing_g2_receipt: bool = False,
    reversed_timestamps: bool = False,
    owner_as_reviewer: bool = False,
    generic_observation_gate: int | None = None,
) -> tuple[gate5.AllowlistRow, str, str, gate5.GitIndex]:
    scope = gate5.MODEL_SCOPE
    source_manifest_path = gate5.MODEL_SOURCE_MANIFEST_PATH
    allowlist_path = f"review/{scope}/g1/SUBSET_EXPORT_ALLOWLIST.tsv"
    provenance_path = f"review/{scope}/g1/PROVENANCE.md"
    gate_path = f"review/{scope}/g1/GATE_RECORD.tsv"
    authorization_path = f"review/{scope}/g1/AUTHORIZATION.md"
    source_bytes = b"canonical source-root manifest bytes\n"
    allowlist_bytes = (
        "\t".join(gate5.SUBSET_HEADER) + "\n"
        + f"{scope}\t{'a' * 64}\tSOURCE\t{gate5.MODEL_SOURCE_PATH}\t{'b' * 64}\t"
        "source.authored\tASSET:hero_model\n"
    ).encode()
    for relative, data in ((source_manifest_path, source_bytes), (allowlist_path, allowlist_bytes)):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    for relative in gate5.FIXED_AUTHORITY_PATHS:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)

    source_digest = hashlib.sha256(source_bytes).hexdigest()
    provenance_values = {
        "schema": "n64game-provenance-v1",
        "production_id": scope,
        "subset_sha256": "a" * 64,
        "subset_allowlist": f"{allowlist_path}@{hashlib.sha256(allowlist_bytes).hexdigest()}",
        "creator_id": "artist.alex-042",
        "rights_holder_id": "studio.n64game-042",
        "source_manifest": f"{source_manifest_path}@{source_digest}",
        "output_manifest": "NONE",
        "rights_basis": "project-original",
        "rights_evidence": f"assets-src/echo/{scope}/RIGHTS_EVIDENCE.md@{'c' * 64}",
        "transformations_sha256": "d" * 64,
        "output_license": "project-all-rights-reserved",
    }
    provenance = "".join(
        f"{key}: {provenance_values[key]}\n" for key in gate5.PROVENANCE_KEYS
    ).encode()
    (root / provenance_path).write_bytes(provenance)

    lock_bytes = (root / "config/toolchain.lock.json").read_bytes()
    lock = json.loads(lock_bytes)
    receipt_values = {
        "schema": "n64game-authoring-stack-receipt-v1",
        "scope_id": scope,
        "gate": "G2",
        "source_manifest_sha256": source_digest,
        "output_manifest_sha256": "NONE",
        "build_id": "-",
        "toolchain_lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
        "checker_sha256": checker_bundle_sha256(root),
        "blender_executable_sha256": lock["authoring"]["blender_macos_arm64"]["executable_sha256"],
        "blender_seal": "DEEP_STRICT_EXPLICIT_REQUIREMENT_PASS",
        "fast64_source_manifest_sha256": lock["authoring"]["fast64"]["source_tree_manifest_sha256"],
        "probe_mode": "ISOLATED_COPY_ENABLED_LOADED_NO_INHERITED_ENV",
        "result": "PASS",
        "checked_at": "2026-07-12T11:00:00Z",
    }
    receipt = "".join(
        f"{key}: {receipt_values[key]}\n" for key in gate5.AUTHORING_RECEIPT_KEYS
    ).encode()

    timestamps = {
        1: "2026-07-11T12:00:00Z",
        2: "2026-07-12T12:00:00Z",
        3: "2026-07-13T12:00:00Z",
        4: "2026-07-14T12:00:00Z",
    }
    if reversed_timestamps:
        timestamps[3] = "2026-07-11T11:00:00Z"
    gate_rows: list[list[str]] = []
    for index in range(1, 5):
        roles = ("gate.observation",) if generic_observation_gate == index else GATE_ROLES[index]
        evidence_rows: list[tuple[str, bytes, str]] = []
        for role in roles:
            filename = role.replace(".", "_").upper() + ".txt"
            relative = f"review/{scope}/g{index}/{filename}"
            payload = f"substantive measured evidence for {scope} G{index} {role}\n".encode()
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            (root / relative).write_bytes(payload)
            evidence_rows.append((relative, payload, role))
        if index == 2 and not missing_g2_receipt:
            receipt_path = f"review/{scope}/g2/AUTHORING_STACK_RECEIPT.txt"
            (root / receipt_path).write_bytes(receipt)
            evidence_rows.append((receipt_path, receipt, "authoring.stack_receipt"))
        evidence_path = f"review/{scope}/g{index}/EVIDENCE_MANIFEST.sha256"
        evidence = "".join(
            f"{relative}\t{len(payload)}\t{hashlib.sha256(payload).hexdigest()}\t"
            f"build:-\tcapture:-\trole:{role}\n"
            for relative, payload, role in sorted(evidence_rows)
        ).encode()
        (root / evidence_path).write_bytes(evidence)
        review_path = f"review/{scope}/g{index}/REVIEW.md"
        reviewer = "artist.alex-042" if owner_as_reviewer and index == 1 else "artlead.jules-042"
        non_owner = g1_non_owner if index == 1 else g3_non_owner if index == 3 else "YES"
        review_values = {
            "schema": "n64game-gate-review-v1",
            "scope_id": scope,
            "gate": f"G{index}",
            "decision": "pass",
            "reviewer_id": reviewer,
            "reviewer_non_owner": non_owner,
            "source_manifest_sha256": source_digest,
            "output_manifest_sha256": "NONE",
            "evidence_manifest": f"{evidence_path}@{hashlib.sha256(evidence).hexdigest()}",
            "build_id": g2_gate_build if index == 2 else "-",
            "decided_at": timestamps[index],
            "defect_ids": "NONE",
            "disposition": "NONE",
            "rationale": "Independent review confirms every exact gate requirement with measured evidence.",
        }
        review = "".join(f"{key}: {review_values[key]}\n" for key in gate5.GATE_REVIEW_KEYS).encode()
        (root / review_path).write_bytes(review)
        gate_rows.append([
            scope, "RIGGED_MODEL", "H2", f"G{index}", "pass", reviewer, non_owner,
            source_digest, "NONE", evidence_path, hashlib.sha256(evidence).hexdigest(),
            review_path, hashlib.sha256(review).hexdigest(), review_values["build_id"],
            timestamps[index], "NONE",
        ])
    for index in range(5, 8):
        gate_rows.append([
            scope, "RIGGED_MODEL", "H2", f"G{index}", "PENDING", *("PENDING" for _ in range(11)),
        ])
    gate_bytes = (
        "\t".join(gate5.GATE_RECORD_HEADER) + "\n"
        + "".join("\t".join(row) + "\n" for row in gate_rows)
    ).encode()
    (root / gate_path).write_bytes(gate_bytes)
    authorization_values = {
        "schema": "n64game-authorization-v1",
        "basis": "WB-002",
        "production_id": scope,
        "subset_sha256": "a" * 64,
        "subset_allowlist": f"{allowlist_path}@{hashlib.sha256(allowlist_bytes).hexdigest()}",
        "state": "AUTHORIZED",
        "repair_ids": "NONE",
        "build_id": BUILD_ID,
        "source_manifest": f"{source_manifest_path}@{source_digest}",
        "output_manifest": "NONE",
        "gate_record": f"{gate_path}@{hashlib.sha256(gate_bytes).hexdigest()}",
        "authorizer_id": "producer.sam-042",
        "authorized_at": "2026-07-15T12:00:00Z",
    }
    authorization = "".join(
        f"{key}: {authorization_values[key]}\n" for key in gate5.AUTHORIZATION_KEYS
    ).encode()
    (root / authorization_path).write_bytes(authorization)
    subprocess.run(["/usr/bin/git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["/usr/bin/git", "add", "--all"], cwd=root, check=True)
    row = gate5.AllowlistRow(
        scope, "a" * 64, "SOURCE", gate5.MODEL_SOURCE_PATH,
        "b" * 64, "source.authored", ("ASSET:hero_model",),
    )
    git = gate5.GitIndex(root)
    git.verify_control_file(source_manifest_path, source_bytes)
    return row, source_manifest_path, authorization_path, git


class Gate5ExporterRealTests(unittest.TestCase):
    maxDiff = None

    def test_paths_symlinks_and_lfs_materialization_fail_closed(self) -> None:
        for value in ("/absolute/file.blend", "assets-src/../escape.blend", "one", "a//b"):
            with self.subTest(value=value):
                self.assertFalse(gate5.safe_repo_path(value))
        payload = b"real authored binary bytes\0\x01\x02"
        digest = hashlib.sha256(payload).hexdigest()
        pointer = (
            "version https://git-lfs.github.com/spec/v1\n"
            f"oid sha256:{digest}\nsize {len(payload)}\n"
        ).encode()
        attributes = {"filter": "lfs", "diff": "lfs", "merge": "lfs", "text": "unset"}
        gate5.require_canonical_lfs("assets-src/echo/echo.quarrune/model.blend", payload, pointer, attributes)
        with self.assertRaisesRegex(gate5.Gate5ExportError, "Git LFS"):
            gate5.require_canonical_lfs(
                "assets-src/echo/echo.quarrune/model.blend", payload, pointer,
                {**attributes, "filter": "unspecified"},
            )
        with self.assertRaisesRegex(gate5.Gate5ExportError, "does not materialize"):
            gate5.require_canonical_lfs(
                "assets-src/echo/echo.quarrune/model.blend", payload + b"changed", pointer, attributes
            )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root / "outside"
            outside.mkdir()
            (root / "review").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(gate5.Gate5ExportError, "symlink"):
                gate5.repo_path(root, gate5.HERO_MODEL_PATH, "output", must_exist=False)

    def test_frozen_selectors_choose_only_exact_authored_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model_paths = {
                "assets-src/echo/echo.quarrune/quarrune.blend": (
                    "ASSET:distance_model", "ASSET:hero_model", "ASSET:rig"
                ),
                f"assets-src/echo/echo.quarrune/{gate5.SOURCE_FILENAMES['body']}": ("ASSET:texture",),
                f"assets-src/echo/echo.quarrune/{gate5.SOURCE_FILENAMES['accent']}": ("ASSET:texture",),
                f"assets-src/echo/echo.quarrune/{gate5.SOURCE_FILENAMES['shadow']}": ("ASSET:blob_shadow",),
            }
            animation_path = "assets-src/anm/anm.echo.quarrune/quarrune_actions.blend"
            for relative in (*model_paths, animation_path):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(relative.encode())
            model_entries = {
                path: gate5.ManifestEntry(
                    path, len(path.encode()), hashlib.sha256(path.encode()).hexdigest(), "-", "-", "source.authored"
                )
                for path in model_paths
            }
            animation_entries = {
                animation_path: gate5.ManifestEntry(
                    animation_path, len(animation_path.encode()), hashlib.sha256(animation_path.encode()).hexdigest(),
                    "-", "-", "source.authored"
                )
            }
            model_rows = tuple(source_row(gate5.MODEL_SCOPE, path, selectors) for path, selectors in sorted(model_paths.items()))
            animation_rows = (source_row(gate5.ANIMATION_SCOPE, animation_path, gate5.ANIMATION_SELECTORS),)
            gate5.validate_allowlist_sources(gate5.MODEL_SCOPE, model_rows, model_entries)
            gate5.validate_allowlist_sources(gate5.ANIMATION_SCOPE, animation_rows, animation_entries)
            inputs = gate5.select_inputs(
                root, model_rows, animation_rows, model_entries, animation_entries
            )
            self.assertEqual(inputs.model_blend.name, "quarrune.blend")
            self.assertEqual(inputs.animation_blend.name, "quarrune_actions.blend")
            broken = list(model_rows)
            broken[0] = source_row(gate5.MODEL_SCOPE, broken[0].member_path, ("ASSET:hero_model",))
            with self.assertRaisesRegex(gate5.Gate5ExportError, "selector union"):
                gate5.validate_allowlist_sources(gate5.MODEL_SCOPE, broken, model_entries)

            renamed = list(model_rows)
            renamed[0] = source_row(
                gate5.MODEL_SCOPE,
                "assets-src/echo/echo.quarrune/not_quarrune.blend",
                renamed[0].selectors,
            )
            renamed_entries = dict(model_entries)
            renamed_entries[renamed[0].member_path] = renamed_entries.pop(model_rows[0].member_path)
            with self.assertRaisesRegex(gate5.Gate5ExportError, "five exact disjoint canonical paths"):
                gate5.select_inputs(root, renamed, animation_rows, renamed_entries, animation_entries)

            wrong_role = dict(model_entries)
            authored = wrong_role[gate5.MODEL_SOURCE_PATH]
            wrong_role[gate5.MODEL_SOURCE_PATH] = gate5.ManifestEntry(
                authored.path, authored.count, authored.digest, authored.build, authored.capture,
                "source.generated",
            )
            with self.assertRaisesRegex(gate5.Gate5ExportError, "source.authored"):
                gate5.select_inputs(root, model_rows, animation_rows, wrong_role, animation_entries)

            escaped = dict(model_entries)
            escaped["assets-src/anm/anm.echo.quarrune/foreign.md"] = gate5.ManifestEntry(
                "assets-src/anm/anm.echo.quarrune/foreign.md", 1, "f" * 64, "-", "-", "rights.support"
            )
            escaped_rows = (*model_rows, source_row(
                gate5.MODEL_SCOPE, "assets-src/anm/anm.echo.quarrune/foreign.md",
                ("METADATA:rights_support",), "rights.support",
            ))
            with self.assertRaisesRegex(gate5.Gate5ExportError, "exact owner root"):
                gate5.validate_allowlist_sources(gate5.MODEL_SCOPE, escaped_rows, escaped)

    def test_converter_and_sprite_command_vectors_are_exact(self) -> None:
        root = Path("/repo")
        inputs = gate5.SourceInputs(
            root / "assets-src/echo/echo.quarrune/quarrune.blend",
            root / "assets-src/anm/anm.echo.quarrune/quarrune_actions.blend",
            root / f"assets-src/echo/echo.quarrune/{gate5.SOURCE_FILENAMES['body']}",
            root / f"assets-src/echo/echo.quarrune/{gate5.SOURCE_FILENAMES['accent']}",
            root / f"assets-src/echo/echo.quarrune/{gate5.SOURCE_FILENAMES['shadow']}",
        )
        config = gate5.ExportConfig(root, BUILD_ID, inputs, (), (), True, False)
        tools = gate5.ToolPaths(Path("/tools/blender"), Path("/tools/gltf_to_t3d"), Path("/tools/mksprite"))
        commands = gate5.tool_commands(tools, config, Path("/stage"), Path("/stage/driver.py"))
        self.assertEqual(len(commands), 8)
        for command in commands[:2]:
            self.assertEqual(command[:5], (
                "/tools/blender", "--background", "--factory-startup", "--offline-mode", "--disable-autoexec"
            ))
        self.assertEqual(
            commands[2],
            (
                "/tools/gltf_to_t3d", "/stage/intermediate/quarrune_hero.glb",
                "/stage/filesystem/echo/echo.quarrune/quarrune_hero.t3dm",
                "--base-scale=64", "--asset-path=filesystem",
            ),
        )
        expected_sprite_profiles = (("CI8", "64,64"), ("CI4", "32,32"), ("IA8", "32,32"))
        for command, (fmt, tiles) in zip(commands[5:], expected_sprite_profiles):
            self.assertEqual(command[0], "/tools/mksprite")
            self.assertEqual(command[1:13], (
                "--format", fmt, "--tiles", tiles, "--mipmap", "NONE", "--dither", "NONE",
                "--compress", "0", "-o", "/stage/filesystem/echo/echo.quarrune",
            ))

    def test_resolve_tools_requires_darwin_arm64_and_exact_n64_binary_pins(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            root = base / "repo"
            home = base / "home"
            n64_inst = base / "n64"
            root.joinpath("config").mkdir(parents=True)
            blender_relative = "Applications/Blender.app/Contents/MacOS/Blender"
            blender = home / blender_relative
            gltf = n64_inst / "bin/gltf_to_t3d"
            sprite = n64_inst / "bin/mksprite"
            payloads = {
                blender: b"pinned blender executable\n",
                gltf: b"pinned tiny3d converter\n",
                sprite: b"pinned libdragon sprite tool\n",
            }
            for path, payload in payloads.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
                path.chmod(0o755)
            lock = {
                "authoring": {
                    "blender_macos_arm64": {
                        "macos_user_relative_path": blender_relative,
                        "executable_size": len(payloads[blender]),
                        "executable_sha256": hashlib.sha256(payloads[blender]).hexdigest(),
                    },
                    "gate5_host_tools_macos_arm64": {
                        "platform": "Darwin-arm64",
                        "gltf_to_t3d": {
                            "executable_size": len(payloads[gltf]),
                            "executable_sha256": hashlib.sha256(payloads[gltf]).hexdigest(),
                        },
                        "mksprite": {
                            "executable_size": len(payloads[sprite]),
                            "executable_sha256": hashlib.sha256(payloads[sprite]).hexdigest(),
                        },
                    },
                },
                "tiny3d": {"commit": "tiny-pin"},
                "libdragon": {"commit": "dragon-pin"},
            }
            root.joinpath("config/toolchain.lock.json").write_text(json.dumps(lock), encoding="utf-8")

            def git_runner(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
                expected = b"tiny-pin\n" if any(value.endswith("vendor/tiny3d") for value in command) else b"dragon-pin\n"
                output = expected if "rev-parse" in command else b""
                return subprocess.CompletedProcess(command, 0, output, b"")

            environment = {"HOME": str(home), "N64_INST": str(n64_inst)}
            lock_bytes = json.dumps(lock).encode()
            with (
                mock.patch.dict(os.environ, environment, clear=True),
                mock.patch.object(gate5.platform, "system", return_value="Darwin"),
                mock.patch.object(gate5.platform, "machine", return_value="arm64"),
                mock.patch.object(gate5.subprocess, "run", side_effect=git_runner),
            ):
                self.assertEqual(gate5.resolve_tools(root), gate5.ToolPaths(blender, gltf, sprite))
                root.joinpath("config/toolchain.lock.json").write_text(
                    '{"transient":"unvalidated live lock"}', encoding="utf-8"
                )
                self.assertEqual(
                    gate5.resolve_tools(root, lock_bytes=lock_bytes),
                    gate5.ToolPaths(blender, gltf, sprite),
                )
                root.joinpath("config/toolchain.lock.json").write_bytes(lock_bytes)
                gltf.write_bytes(b"X" * len(payloads[gltf]))
                with self.assertRaisesRegex(gate5.Gate5ExportError, "SHA-256"):
                    gate5.resolve_tools(root)
            with (
                mock.patch.object(gate5.platform, "system", return_value="Linux"),
                mock.patch.object(gate5.platform, "machine", return_value="x86_64"),
            ):
                with self.assertRaisesRegex(gate5.Gate5ExportError, "Darwin-arm64"):
                    gate5.resolve_tools(root)

    def test_gate_authority_requires_tracked_pass_g1_g4_and_pending_g5_g7(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            row, source_manifest_path, authorization_path, git = write_gate_authority_fixture(root)
            paths = gate5.validate_gate_authority(
                root, gate5.MODEL_SCOPE, (row,), source_manifest_path, {}, candidate=True,
                build_id=BUILD_ID, git=git,
            )
            self.assertIn(authorization_path, paths)
            self.assertIn(f"review/{gate5.MODEL_SCOPE}/g4/EVIDENCE_MANIFEST.sha256", paths)
            self.assertIn(f"review/{gate5.MODEL_SCOPE}/g2/AUTHORING_STACK_RECEIPT.txt", paths)

            bad = (root / authorization_path).read_bytes().replace(
                f"build_id: {BUILD_ID}\n".encode(), b"build_id: PENDING\n"
            )
            (root / authorization_path).write_bytes(bad)
            subprocess.run(["/usr/bin/git", "add", authorization_path], cwd=root, check=True)
            bad_git = gate5.GitIndex(root)
            bad_git.verify_control_file(
                source_manifest_path, (root / source_manifest_path).read_bytes()
            )
            with self.assertRaisesRegex(gate5.Gate5ExportError, "build_id is neither"):
                gate5.validate_gate_authority(
                    root, gate5.MODEL_SCOPE, (row,), source_manifest_path, {}, candidate=True,
                    build_id=BUILD_ID, git=bad_git,
                )

    def test_gate_authority_rejects_lifecycle_shortcuts_before_export(self) -> None:
        cases = (
            ("H2 G1 self review", {"g1_non_owner": "NO"}, "requires a non-owner"),
            ("H2 G3 self review", {"g3_non_owner": "NO"}, "requires a non-owner"),
            ("G2 substantive build", {"g2_gate_build": BUILD_ID}, "G2 gate row build must be -"),
            ("missing G2 receipt", {"missing_g2_receipt": True}, "must directly contain exactly"),
            ("reversed timestamps", {"reversed_timestamps": True}, "precedes an earlier gate"),
            ("owner as reviewer", {"owner_as_reviewer": True}, "matches an asset owner"),
            ("generic observation only", {"generic_observation_gate": 1}, "gate-specific evidence"),
        )
        for label, options, expected in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                row, source_manifest_path, _authorization_path, git = write_gate_authority_fixture(
                    root, **options  # type: ignore[arg-type]
                )
                with self.assertRaisesRegex(gate5.Gate5ExportError, expected):
                    gate5.validate_gate_authority(
                        root, gate5.MODEL_SCOPE, (row,), source_manifest_path, {}, candidate=True,
                        build_id=BUILD_ID, git=git,
                    )

    def test_safe_binary_fixture_passes_full_binding_and_output_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary)
            values = fixture_contract.fixture()
            write_fixture(stage, values)
            entries = gate5.validate_staged_pair(stage, BUILD_ID, ROOT)
            self.assertEqual(set(entries), set(gate5.MANAGED_OUTPUT_PATHS))

            tampered = copy.deepcopy(values)
            binding = tampered["bytes"][gate5.SKELETON_BINDING_PATH]  # type: ignore[index]
            tampered["bytes"][gate5.SKELETON_BINDING_PATH] = binding.replace(  # type: ignore[index]
                f"build_id\t{BUILD_ID}\n".encode(), b"build_id\tn64game-g5-other-001\n"
            )
            fixture_contract.refresh_entry(tampered, gate5.SKELETON_BINDING_PATH)
            broken = stage / "broken"
            broken.mkdir()
            write_fixture(broken, tampered)
            with self.assertRaisesRegex(gate5.Gate5ExportError, "binding mismatch"):
                gate5.validate_staged_pair(broken, BUILD_ID, ROOT)

    def test_production_orchestrator_consumes_only_successful_tool_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            stage = base / "stage"
            source = base / "source"
            stage.mkdir()
            source.mkdir()
            inputs = gate5.SourceInputs(
                source / "quarrune.blend", source / "actions.blend",
                source / gate5.SOURCE_FILENAMES["body"],
                source / gate5.SOURCE_FILENAMES["accent"],
                source / gate5.SOURCE_FILENAMES["shadow"],
            )
            for path in inputs.__dict__.values():
                path.write_bytes((path.name + "\n").encode())
            config = gate5.ExportConfig(ROOT, BUILD_ID, inputs, (), (), True, False)
            tools = gate5.ToolPaths(base / "blender", base / "gltf_to_t3d", base / "mksprite")
            fixture = fixture_contract.fixture()
            fixture_bytes: dict[str, bytes] = fixture["bytes"]  # type: ignore[assignment]
            calls: list[list[str]] = []

            def runner(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
                calls.append(command)
                if command[0] == str(tools.blender):
                    mode = command[command.index("--") + 1]
                    outputs = command[command.index("--") + 2:]
                    if mode == "model":
                        for output in outputs:
                            Path(output).write_bytes(minimal_glb())
                    else:
                        Path(outputs[0]).write_bytes(minimal_glb(gate5.ANIMATION_NAMES))
                elif command[0] == str(tools.gltf_to_t3d):
                    output = Path(command[2])
                    if output.name == "quarrune_hero.t3dm":
                        output.write_bytes(fixture_bytes[gate5.HERO_MODEL_PATH])
                    elif output.name == "quarrune_distance.t3dm":
                        output.write_bytes(fixture_bytes[gate5.DISTANCE_MODEL_PATH])
                    else:
                        output.write_bytes(fixture_bytes[gate5.ANIMATION_HEADER_PATH])
                        for index, relative in enumerate(gate5.ANIMATION_STREAM_PATHS):
                            output.with_suffix(f".{index}.sdata").write_bytes(fixture_bytes[relative])
                else:
                    output_root = Path(command[command.index("-o") + 1])
                    source_name = Path(command[-1]).stem + ".sprite"
                    relative = {
                        "tex_quarrune_body_ci8_64x64.sprite": gate5.BODY_TEXTURE_PATH,
                        "tex_quarrune_accent_ci4_32x32.sprite": gate5.ACCENT_TEXTURE_PATH,
                        "tex_quarrune_blob_shadow_ia8_32x32.sprite": gate5.BLOB_SHADOW_PATH,
                    }[source_name]
                    (output_root / source_name).write_bytes(fixture_bytes[relative])
                return subprocess.CompletedProcess(command, 0, b"", b"")

            gate5.production_generate(config, stage, tools=tools, run=runner)
            self.assertEqual(len(calls), 8)
            self.assertEqual(
                set(gate5.validate_staged_pair(stage, BUILD_ID, ROOT)), set(gate5.MANAGED_OUTPUT_PATHS)
            )

    def make_transaction_root(self, parent: Path) -> tuple[Path, gate5.ExportConfig]:
        root = parent / "repo"
        root.mkdir()
        shutil.copytree(ROOT / "lib", root / "lib")
        inputs = gate5.SourceInputs(
            root / "assets-src/echo/echo.quarrune/quarrune.blend",
            root / "assets-src/anm/anm.echo.quarrune/quarrune_actions.blend",
            root / f"assets-src/echo/echo.quarrune/{gate5.SOURCE_FILENAMES['body']}",
            root / f"assets-src/echo/echo.quarrune/{gate5.SOURCE_FILENAMES['accent']}",
            root / f"assets-src/echo/echo.quarrune/{gate5.SOURCE_FILENAMES['shadow']}",
        )
        for path in (
            *inputs.__dict__.values(),
            root / f"assets-src/echo/{gate5.MODEL_SCOPE}/SOURCE_MANIFEST.sha256",
            root / f"assets-src/anm/{gate5.ANIMATION_SCOPE}/SOURCE_MANIFEST.sha256",
            root / f"review/{gate5.MODEL_SCOPE}/g1/SUBSET_EXPORT_ALLOWLIST.tsv",
            root / f"review/{gate5.ANIMATION_SCOPE}/g1/SUBSET_EXPORT_ALLOWLIST.tsv",
            root / f"review/{gate5.MODEL_SCOPE}/g1/AUTHORIZATION.md",
            root / f"review/{gate5.ANIMATION_SCOPE}/g1/AUTHORIZATION.md",
            root / f"review/{gate5.MODEL_SCOPE}/g1/GATE_RECORD.tsv",
            root / f"review/{gate5.ANIMATION_SCOPE}/g1/GATE_RECORD.tsv",
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((str(path) + "\n").encode())
        for relative in gate5.FIXED_AUTHORITY_PATHS:
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        return root, gate5.ExportConfig(root, BUILD_ID, inputs, (), (), True, False)

    def test_double_run_is_deterministic_pair_aware_and_preserves_unrelated_review(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, config = self.make_transaction_root(Path(temporary))
            unrelated = root / "review/echo.quarrune/g5/REVIEW.md"
            unrelated.parent.mkdir(parents=True, exist_ok=True)
            unrelated.write_text("independent review\n", encoding="utf-8")
            calls = 0

            def generate(_config: gate5.ExportConfig, stage: Path) -> None:
                nonlocal calls
                calls += 1
                self.assertTrue(str(_config.inputs.model_blend).startswith(str(stage / "captured-authority")))
                self.assertEqual(
                    _config.inputs.model_blend.read_bytes(),
                    (root / gate5.MODEL_SOURCE_PATH).read_bytes(),
                )
                write_fixture(stage, fixture_contract.fixture())

            result = gate5.export_pair(config, generator=generate)
            self.assertEqual(calls, 2)
            self.assertEqual(set(result), set(gate5.MANAGED_PATHS))
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "independent review\n")
            self.assertTrue(all((root / relative).is_file() for relative in gate5.MANAGED_PATHS))

    def test_nondeterminism_fails_before_any_pair_member_is_promoted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, config = self.make_transaction_root(Path(temporary))
            calls = 0

            def generate(_config: gate5.ExportConfig, stage: Path) -> None:
                nonlocal calls
                calls += 1
                values = fixture_contract.fixture(hero_triangles=900 if calls == 1 else 901)
                write_fixture(stage, values)

            with self.assertRaisesRegex(gate5.Gate5ExportError, "nondeterministic"):
                gate5.export_pair(config, generator=generate)
            self.assertFalse(any((root / relative).exists() for relative in gate5.MANAGED_PATHS))

    def test_candidate_promotion_fault_rolls_back_both_owners(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            stage = base / "stage"
            root = base / "root"
            stage.mkdir()
            root.mkdir()
            shutil.copytree(ROOT / "lib", root / "lib")
            write_fixture(stage, fixture_contract.fixture())
            def fault(event: str, relative: str | None) -> None:
                if event == "after_link" and relative and relative.endswith("anm_echo_quarrune.4.sdata"):
                    raise OSError("controlled promotion fault")

            with self.assertRaisesRegex(gate5.Gate5ExportError, "rolled back"):
                gate5.promote_pair(
                    stage, root, replace=False, build_id=BUILD_ID,
                    contract_root=root, step_hook=fault,
                )
            self.assertFalse(any((root / relative).exists() for relative in gate5.MANAGED_PATHS))
            self.assertFalse((root / gate5.JOURNAL_RELATIVE).exists())

    def test_journal_detection_and_parent_symlink_swap_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            stage = base / "stage"
            root = base / "root"
            stage.mkdir()
            root.mkdir()
            shutil.copytree(ROOT / "lib", root / "lib")
            write_fixture(stage, fixture_contract.fixture())
            journal = root / gate5.JOURNAL_RELATIVE
            journal.parent.mkdir(parents=True)
            journal.write_text('{"unfinished":true}\n', encoding="utf-8")
            with self.assertRaisesRegex(gate5.Gate5ExportError, "journal exists"):
                gate5.promote_pair(
                    stage, root, replace=False, build_id=BUILD_ID, contract_root=root
                )
            self.assertFalse(any((root / relative).exists() for relative in gate5.MANAGED_PATHS))

            journal.unlink()
            outside = base / "outside"
            outside.mkdir()

            def swap_parent(event: str, _relative: str | None) -> None:
                if event == "parents_pinned":
                    root.joinpath("review").rename(root / "review-pinned")
                    root.joinpath("review").symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(gate5.Gate5ExportError, "rolled back"):
                gate5.promote_pair(
                    stage, root, replace=False, build_id=BUILD_ID,
                    contract_root=root, step_hook=swap_parent,
                )
            self.assertEqual(list(outside.rglob("*")), [])
            self.assertFalse(any(path.is_file() for path in (root / "review-pinned").rglob("*")))

    def test_exact_lock_path_and_validated_inherited_descriptor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            expected = Path(
                "/tmp/n64game-gate5-"
                + hashlib.sha256(os.path.realpath(root).encode()).hexdigest()
                + ".lock"
            )
            self.assertEqual(gate5.transaction_lock_path(root), expected)
            fd = os.open(expected, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600)
            os.fchmod(fd, 0o600)
            gate5.fcntl.flock(fd, gate5.fcntl.LOCK_EX)
            try:
                with mock.patch.dict(os.environ, {"N64GAME_GATE5_LOCK_FD": str(fd)}, clear=False):
                    with gate5.transaction_lock(root) as observed:
                        self.assertEqual(observed, fd)
                os.fchmod(fd, 0o644)
                with mock.patch.dict(os.environ, {"N64GAME_GATE5_LOCK_FD": str(fd)}, clear=False):
                    with self.assertRaisesRegex(gate5.Gate5ExportError, "mode-0600"):
                        with gate5.transaction_lock(root):
                            pass
            finally:
                gate5.fcntl.flock(fd, gate5.fcntl.LOCK_UN)
                os.close(fd)
                expected.unlink(missing_ok=True)

    def test_full_live_authority_is_rechecked_after_each_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, config = self.make_transaction_root(Path(temporary))
            calls = 0

            def mutate_live(_config: gate5.ExportConfig, stage: Path) -> None:
                nonlocal calls
                calls += 1
                write_fixture(stage, fixture_contract.fixture())
                if calls == 1:
                    (root / ".gitattributes").write_bytes(b"changed during export\n")

            with self.assertRaisesRegex(gate5.Gate5ExportError, "source/control identity changed"):
                gate5.export_pair(config, generator=mutate_live)
            self.assertEqual(calls, 1)
            self.assertFalse(any((root / relative).exists() for relative in gate5.MANAGED_PATHS))

    def test_validated_authority_seal_rejects_contract_mutation_before_generator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, config = self.make_transaction_root(Path(temporary))
            relative = "lib/n64game/tiny3d_package_contract.rb"
            subprocess.run(["/usr/bin/git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["/usr/bin/git", "add", relative], cwd=root, check=True)
            git = gate5.GitIndex(root)
            data = (root / relative).read_bytes()
            git.verify_control_file(relative, data)
            sealed = gate5.seal_validated_authority(
                gate5.dataclass_replace(config, authority_paths=(relative,)), git
            )
            (root / relative).write_bytes(data + b"# mutation after build_config validation\n")
            calls = 0

            def generate(_config: gate5.ExportConfig, stage: Path) -> None:
                nonlocal calls
                calls += 1
                write_fixture(stage, fixture_contract.fixture())

            with self.assertRaisesRegex(gate5.Gate5ExportError, "validated immutable seal"):
                gate5.export_pair(sealed, generator=generate)
            self.assertEqual(calls, 0)
            self.assertFalse(any((root / path).exists() for path in gate5.MANAGED_PATHS))

    def test_index_seal_rejects_control_blob_drift_before_generator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, config = self.make_transaction_root(Path(temporary))
            relative = "lib/n64game/tiny3d_package_contract.rb"
            subprocess.run(["/usr/bin/git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["/usr/bin/git", "add", relative], cwd=root, check=True)
            git = gate5.GitIndex(root)
            original = (root / relative).read_bytes()
            git.verify_control_file(relative, original)
            sealed = gate5.seal_validated_authority(
                gate5.dataclass_replace(config, authority_paths=(relative,)), git
            )
            stage_index_blob(root, relative, original + b"# index-only mutation\n")
            self.assertEqual((root / relative).read_bytes(), original)
            calls = 0

            def generate(_config: gate5.ExportConfig, stage: Path) -> None:
                nonlocal calls
                calls += 1
                write_fixture(stage, fixture_contract.fixture())

            with self.assertRaisesRegex(gate5.Gate5ExportError, "Git index authority changed"):
                gate5.export_pair(sealed, generator=generate)
            self.assertEqual(calls, 0)

    def test_index_seal_rejects_lfs_pointer_mode_and_attribute_drift(self) -> None:
        for mutation in ("pointer", "mode", "attributes"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                root, config = self.make_transaction_root(Path(temporary))
                relative = gate5.MODEL_SOURCE_PATH
                subprocess.run(["/usr/bin/git", "init", "-q"], cwd=root, check=True)
                subprocess.run(["/usr/bin/git", "add", ".gitattributes"], cwd=root, check=True)
                materialized = (root / relative).read_bytes()
                pointer = lfs_pointer(materialized)
                pointer_oid = stage_index_blob(root, relative, pointer)
                git = gate5.GitIndex(root)
                git.verify_member(
                    gate5.ManifestEntry(
                        relative, len(materialized), hashlib.sha256(materialized).hexdigest(),
                        "-", "-", "source.authored",
                    ),
                    materialized,
                )
                sealed = gate5.seal_validated_authority(
                    gate5.dataclass_replace(config, authority_paths=(relative,)), git
                )
                if mutation == "pointer":
                    stage_index_blob(root, relative, lfs_pointer(materialized, digest="0" * 64))
                elif mutation == "mode":
                    subprocess.run(
                        [
                            "/usr/bin/git", "update-index", "--cacheinfo",
                            f"100755,{pointer_oid},{relative}",
                        ],
                        cwd=root, check=True,
                    )
                else:
                    stage_index_blob(root, ".gitattributes", b"*.blend -text\n")
                self.assertEqual((root / relative).read_bytes(), materialized)
                calls = 0

                def generate(_config: gate5.ExportConfig, stage: Path) -> None:
                    nonlocal calls
                    calls += 1
                    write_fixture(stage, fixture_contract.fixture())

                with self.assertRaisesRegex(gate5.Gate5ExportError, "Git index authority changed"):
                    gate5.export_pair(sealed, generator=generate)
                self.assertEqual(calls, 0)

    def test_index_only_drift_after_run_fails_before_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, config = self.make_transaction_root(Path(temporary))
            subprocess.run(["/usr/bin/git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["/usr/bin/git", "add", ".gitattributes"], cwd=root, check=True)
            git = gate5.GitIndex(root)
            input_relatives: list[str] = []
            root_absolute = root.resolve()
            for path in config.inputs.__dict__.values():
                relative = path.resolve().relative_to(root_absolute).as_posix()
                input_relatives.append(relative)
                materialized = path.read_bytes()
                stage_index_blob(root, relative, lfs_pointer(materialized))
                git.verify_member(
                    gate5.ManifestEntry(
                        relative, len(materialized), hashlib.sha256(materialized).hexdigest(),
                        "-", "-", "source.authored",
                    ),
                    materialized,
                )
            control = "lib/n64game/tiny3d_package_contract.rb"
            control_bytes = (root / control).read_bytes()
            stage_index_blob(root, control, control_bytes)
            git.verify_control_file(control, control_bytes)
            sealed = gate5.seal_validated_authority(
                gate5.dataclass_replace(
                    config, authority_paths=tuple(sorted((*input_relatives, control)))
                ),
                git,
            )
            calls = 0

            def mutate_index(_config: gate5.ExportConfig, stage: Path) -> None:
                nonlocal calls
                calls += 1
                write_fixture(stage, fixture_contract.fixture())
                if calls == 1:
                    stage_index_blob(root, control, control_bytes + b"# changed after run A\n")

            with self.assertRaisesRegex(gate5.Gate5ExportError, "Git index authority changed"):
                gate5.export_pair(sealed, generator=mutate_index)
            self.assertEqual(calls, 1)
            self.assertFalse(any((root / relative).exists() for relative in gate5.MANAGED_PATHS))

    def test_allowlist_parse_a_then_index_b_fails_before_generator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            _row, _source_manifest, _authorization, git = write_gate_authority_fixture(root)
            scope = gate5.MODEL_SCOPE
            relative = f"review/{scope}/g1/SUBSET_EXPORT_ALLOWLIST.tsv"
            rows = gate5.parse_allowlist(root, scope, git)
            original = (root / relative).read_bytes()
            changed = original.replace(b"ASSET:hero_model", b"ASSET:rig")
            (root / relative).write_bytes(changed)
            stage_index_blob(root, relative, changed)
            inputs = gate5.SourceInputs(*(Path("/unused") for _ in range(5)))
            config = gate5.ExportConfig(
                root, BUILD_ID, inputs, rows, (), True, False, authority_paths=(relative,)
            )
            sealed = gate5.seal_validated_authority(config, git)
            calls = 0

            def generate(_config: gate5.ExportConfig, stage: Path) -> None:
                nonlocal calls
                calls += 1
                write_fixture(stage, fixture_contract.fixture())

            with self.assertRaisesRegex(gate5.Gate5ExportError, "Git index authority changed"):
                gate5.export_pair(sealed, generator=generate)
            self.assertEqual(calls, 0)

    def test_evidence_digest_bytes_cannot_swap_before_manifest_parse(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            row, source_manifest_path, _authorization, git = write_gate_authority_fixture(
                root, generic_observation_gate=1
            )
            scope = gate5.MODEL_SCOPE
            evidence_path = f"review/{scope}/g1/EVIDENCE_MANIFEST.sha256"
            replacement_rows: list[tuple[str, bytes, str]] = []
            for role in GATE_ROLES[1]:
                relative = f"review/{scope}/g1/SWAP_{role.replace('.', '_').upper()}.txt"
                payload = f"replacement evidence for {role}\n".encode()
                (root / relative).write_bytes(payload)
                replacement_rows.append((relative, payload, role))
            subprocess.run(
                ["/usr/bin/git", "add", *[row[0] for row in replacement_rows]],
                cwd=root, check=True,
            )
            replacement = "".join(
                f"{relative}\t{len(payload)}\t{hashlib.sha256(payload).hexdigest()}\t"
                f"build:-\tcapture:-\trole:{role}\n"
                for relative, payload, role in sorted(replacement_rows)
            ).encode()
            original_parse_manifest = gate5.parse_manifest
            swapped = False

            def swap_then_parse(
                parse_root: Path,
                relative: str,
                parse_git: gate5.GitIndex,
                **kwargs: object,
            ) -> dict[str, gate5.ManifestEntry]:
                nonlocal swapped
                if relative == evidence_path and not swapped:
                    swapped = True
                    (root / evidence_path).write_bytes(replacement)
                    stage_index_blob(root, evidence_path, replacement)
                return original_parse_manifest(parse_root, relative, parse_git, **kwargs)

            with (
                mock.patch.object(gate5, "parse_manifest", side_effect=swap_then_parse),
                self.assertRaisesRegex(gate5.Gate5ExportError, "ordinary-Git source differs"),
            ):
                gate5.validate_gate_authority(
                    root, scope, (row,), source_manifest_path, {}, candidate=True,
                    build_id=BUILD_ID, git=git,
                )
            self.assertTrue(swapped)

    def test_unlink_recreate_split_lock_is_detected_across_two_processes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            signal = root / "release-a"
            lock_path = gate5.transaction_lock_path(root)
            lock_path.unlink(missing_ok=True)
            module_root = str(ROOT / "tools")
            root_text = str(root)
            signal_text = str(signal)
            process_a_code = f"""
import pathlib, sys, time
sys.path.insert(0, {module_root!r})
import n64game_gate5_export as gate5
root = pathlib.Path({root_text!r})
signal = pathlib.Path({signal_text!r})
try:
    with gate5.transaction_lock(root) as fd:
        print('A_LOCKED', flush=True)
        deadline = time.time() + 10
        while not signal.exists() and time.time() < deadline:
            time.sleep(0.01)
        gate5.validate_lock_boundary(root, fd, 'two-process regression')
except gate5.Gate5ExportError as exc:
    print('A_FAILED:' + str(exc), flush=True)
    raise SystemExit(0)
raise SystemExit(9)
"""
            process_b_code = f"""
import pathlib, sys
sys.path.insert(0, {module_root!r})
import n64game_gate5_export as gate5
root = pathlib.Path({root_text!r})
with gate5.transaction_lock(root):
    print('B_LOCKED', flush=True)
"""
            process_a = subprocess.Popen(
                ["/usr/bin/python3", "-u", "-c", process_a_code],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            try:
                self.assertEqual(process_a.stdout.readline().strip(), "A_LOCKED")  # type: ignore[union-attr]
                lock_path.unlink()
                replacement = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
                os.close(replacement)
                process_b = subprocess.run(
                    ["/usr/bin/python3", "-u", "-c", process_b_code],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
                )
                self.assertEqual(process_b.returncode, 0, process_b.stderr)
                self.assertIn("B_LOCKED", process_b.stdout)
                signal.write_text("release\n", encoding="utf-8")
                output, error = process_a.communicate(timeout=10)
                self.assertEqual(process_a.returncode, 0, error)
                self.assertIn("A_FAILED:", output)
                self.assertIn("lock pathname changed", output)
            finally:
                if process_a.poll() is None:
                    process_a.kill()
                    process_a.wait()
                lock_path.unlink(missing_ok=True)

    def test_concurrent_candidates_are_serialized_and_cannot_mix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, config = self.make_transaction_root(Path(temporary))
            calls: list[str] = []
            outcomes: list[tuple[str, str]] = []
            guard = threading.Lock()

            def worker(label: str, triangles: int) -> None:
                def generate(_config: gate5.ExportConfig, stage: Path) -> None:
                    with guard:
                        calls.append(label)
                    time.sleep(0.02)
                    write_fixture(stage, fixture_contract.fixture(hero_triangles=triangles))
                try:
                    gate5.export_pair(config, generator=generate)
                except gate5.Gate5ExportError as exc:
                    outcomes.append((label, f"FAIL:{exc}"))
                else:
                    outcomes.append((label, "PASS"))

            threads = [
                threading.Thread(target=worker, args=("A", 900)),
                threading.Thread(target=worker, args=("B", 920)),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)
                self.assertFalse(thread.is_alive())
            self.assertEqual(sum(result == "PASS" for _label, result in outcomes), 1)
            self.assertEqual(len(calls), 4)
            self.assertIn(calls, (["A", "A", "B", "B"], ["B", "B", "A", "A"]))
            gate5.validate_staged_pair(root, BUILD_ID, root)

    def test_final_regeneration_matches_without_rewriting_reviewed_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, candidate = self.make_transaction_root(Path(temporary))

            def generate(_config: gate5.ExportConfig, stage: Path) -> None:
                write_fixture(stage, fixture_contract.fixture())

            gate5.export_pair(candidate, generator=generate)
            entries = gate5.validate_staged_pair(root, BUILD_ID, root)
            model_rows: list[gate5.AllowlistRow] = []
            animation_rows: list[gate5.AllowlistRow] = []
            for relative, entry in sorted(entries.items()):
                scope = gate5.MODEL_SCOPE if relative in gate5.MODEL_ROLES else gate5.ANIMATION_SCOPE
                row = gate5.AllowlistRow(
                    scope, "a" * 64, "OUTPUT", relative, entry.digest, entry.role,
                    ("OUTPUT:runtime",),
                )
                (model_rows if scope == gate5.MODEL_SCOPE else animation_rows).append(row)
            before = {
                relative: ((root / relative).stat().st_ino, (root / relative).stat().st_mtime_ns)
                for relative in gate5.MANAGED_PATHS
            }
            final = gate5.ExportConfig(
                root, BUILD_ID, candidate.inputs, tuple(model_rows), tuple(animation_rows),
                False, True,
            )
            gate5.export_pair(final, generator=generate)
            after = {
                relative: ((root / relative).stat().st_ino, (root / relative).stat().st_mtime_ns)
                for relative in gate5.MANAGED_PATHS
            }
            self.assertEqual(after, before)

    def test_final_output_allowlist_must_bind_every_validated_byte(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary)
            write_fixture(stage, fixture_contract.fixture())
            entries = gate5.validate_staged_pair(stage, BUILD_ID, ROOT)
            model_rows: list[gate5.AllowlistRow] = []
            animation_rows: list[gate5.AllowlistRow] = []
            for relative, entry in sorted(entries.items()):
                scope = gate5.MODEL_SCOPE if relative in gate5.MODEL_ROLES else gate5.ANIMATION_SCOPE
                row = gate5.AllowlistRow(
                    scope, "a" * 64, "OUTPUT", relative, entry.digest, entry.role, ("OUTPUT:runtime",)
                )
                (model_rows if scope == gate5.MODEL_SCOPE else animation_rows).append(row)
            gate5.validate_output_allowlists(model_rows, animation_rows, entries, candidate=False)
            broken = list(model_rows)
            broken[0] = gate5.AllowlistRow(
                broken[0].production_id, broken[0].subset_sha256, broken[0].stage,
                broken[0].member_path, "0" * 64, broken[0].manifest_role, broken[0].selectors,
            )
            with self.assertRaisesRegex(gate5.Gate5ExportError, "differs from reviewed"):
                gate5.validate_output_allowlists(broken, animation_rows, entries, candidate=False)

    def test_final_output_allowlist_rejects_cross_owner_swapped_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary)
            write_fixture(stage, fixture_contract.fixture())
            entries = gate5.validate_staged_pair(stage, BUILD_ID, ROOT)
            model_rows: list[gate5.AllowlistRow] = []
            animation_rows: list[gate5.AllowlistRow] = []
            for relative, entry in sorted(entries.items()):
                scope = gate5.MODEL_SCOPE if relative in gate5.MODEL_ROLES else gate5.ANIMATION_SCOPE
                row = gate5.AllowlistRow(
                    scope, "a" * 64, "OUTPUT", relative, entry.digest, entry.role, ("OUTPUT:runtime",)
                )
                (model_rows if scope == gate5.MODEL_SCOPE else animation_rows).append(row)

            swapped_model = list(model_rows)
            swapped_animation = list(animation_rows)
            model_row = swapped_model[0]
            animation_row = swapped_animation[0]
            swapped_model[0] = gate5.AllowlistRow(
                model_row.production_id, model_row.subset_sha256, animation_row.stage,
                animation_row.member_path, animation_row.member_sha256,
                animation_row.manifest_role, animation_row.selectors,
            )
            swapped_animation[0] = gate5.AllowlistRow(
                animation_row.production_id, animation_row.subset_sha256, model_row.stage,
                model_row.member_path, model_row.member_sha256,
                model_row.manifest_role, model_row.selectors,
            )
            self.assertEqual(
                {row.member_path for row in (*swapped_model, *swapped_animation)},
                set(gate5.MANAGED_OUTPUT_PATHS),
            )
            self.assertTrue(all(row.production_id == gate5.MODEL_SCOPE for row in swapped_model))
            self.assertTrue(all(row.production_id == gate5.ANIMATION_SCOPE for row in swapped_animation))
            with self.assertRaisesRegex(gate5.Gate5ExportError, "owner partition"):
                gate5.validate_output_allowlists(
                    swapped_model, swapped_animation, entries, candidate=False
                )

            full_model = [
                gate5.AllowlistRow(
                    gate5.MODEL_SCOPE, row.subset_sha256, row.stage, row.member_path,
                    row.member_sha256, row.manifest_role, row.selectors,
                )
                for row in animation_rows
            ]
            full_animation = [
                gate5.AllowlistRow(
                    gate5.ANIMATION_SCOPE, row.subset_sha256, row.stage, row.member_path,
                    row.member_sha256, row.manifest_role, row.selectors,
                )
                for row in model_rows
            ]
            with self.assertRaisesRegex(gate5.Gate5ExportError, "owner partition"):
                gate5.validate_output_allowlists(full_model, full_animation, entries, candidate=False)

            duplicated = [*model_rows]
            duplicated[-1] = duplicated[0]
            with self.assertRaisesRegex(gate5.Gate5ExportError, "exact OUTPUT rows"):
                gate5.validate_output_allowlists(duplicated, animation_rows, entries, candidate=False)

            moved = [*model_rows, gate5.AllowlistRow(
                gate5.MODEL_SCOPE, animation_rows[0].subset_sha256, animation_rows[0].stage,
                animation_rows[0].member_path, animation_rows[0].member_sha256,
                animation_rows[0].manifest_role, animation_rows[0].selectors,
            )]
            with self.assertRaisesRegex(gate5.Gate5ExportError, "owner partition"):
                gate5.validate_output_allowlists(moved, animation_rows[1:], entries, candidate=False)

            case_collision = list(model_rows)
            original = case_collision[0]
            case_collision[0] = gate5.AllowlistRow(
                original.production_id, original.subset_sha256, original.stage,
                original.member_path.upper(), original.member_sha256,
                original.manifest_role, original.selectors,
            )
            with self.assertRaisesRegex(gate5.Gate5ExportError, "exact OUTPUT rows"):
                gate5.validate_output_allowlists(case_collision, animation_rows, entries, candidate=False)


if __name__ == "__main__":
    unittest.main()
