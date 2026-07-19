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
import unittest
from pathlib import Path


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

    def test_converter_and_sprite_command_vectors_are_exact(self) -> None:
        root = Path("/repo")
        inputs = gate5.SourceInputs(
            root / "assets-src/echo/echo.quarrune/quarrune.blend",
            root / "assets-src/anm/anm.echo.quarrune/actions.blend",
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
            root / "assets-src/anm/anm.echo.quarrune/actions.blend",
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
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((str(path) + "\n").encode())
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

    def test_promotion_fault_rolls_back_both_owners(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            stage = base / "stage"
            root = base / "root"
            stage.mkdir()
            root.mkdir()
            write_fixture(stage, fixture_contract.fixture())
            old = {relative: ("old:" + relative).encode() for relative in gate5.MANAGED_PATHS}
            for relative, payload in old.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
            faulted = False

            def replace_once(source: os.PathLike[str] | str, destination: os.PathLike[str] | str) -> None:
                nonlocal faulted
                if not faulted and str(destination).endswith("anm_echo_quarrune.4.sdata"):
                    faulted = True
                    raise OSError("controlled promotion fault")
                os.replace(source, destination)

            with self.assertRaisesRegex(gate5.Gate5ExportError, "rolled back"):
                gate5.promote_pair(stage, root, replace=True, replace_func=replace_once)
            for relative, payload in old.items():
                self.assertEqual((root / relative).read_bytes(), payload, relative)

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


if __name__ == "__main__":
    unittest.main()
