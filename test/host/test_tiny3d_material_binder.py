from __future__ import annotations

import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = ROOT / "tools" / "n64game_tiny3d_materials.py"
SPEC = importlib.util.spec_from_file_location("n64game_tiny3d_materials", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)


def build_glb(path: Path, bad_upper_uv: bool = False) -> None:
    ranges = [
        [(0.1, 0.55), (0.8, 0.90), (0.4, 0.75)],
        [(0.1, 0.05), (0.8, 0.45), (0.4, 0.25)],
        [(0.1, 0.10), (0.8, 0.90), (0.4, 0.50)],
    ]
    if bad_upper_uv:
        ranges[0][0] = (0.1, 0.40)
    binary = bytearray()
    views = []
    accessors = []
    for values in ranges:
        offset = len(binary)
        for uv in values:
            binary.extend(struct.pack("<ff", *uv))
        views.append({"buffer": 0, "byteOffset": offset, "byteLength": 24})
        accessors.append({
            "bufferView": len(views) - 1,
            "componentType": 5126,
            "count": 3,
            "type": "VEC2",
        })
    document = {
        "asset": {"version": "2.0"},
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": views,
        "accessors": accessors,
        "materials": [
            {"name": "body_top", "extras": {"authored": True}},
            {"name": "body_bottom", "extras": {"authored": True}},
            {"name": "accent", "extras": {"authored": True}},
            {"name": "solid_trim", "extras": {"authored": True}},
            {"name": "route_light", "extras": {"authored": True}},
            {"name": "tinted_screen", "extras": {"authored": True}},
        ],
        "meshes": [{"primitives": [
            {"attributes": {"TEXCOORD_0": index}, "material": index, "mode": 4}
            for index in range(3)
        ] + [
            {"attributes": {}, "material": 3, "mode": 4},
            {"attributes": {}, "material": 4, "mode": 4},
            {"attributes": {"TEXCOORD_0": 2}, "material": 5, "mode": 4},
        ]}],
    }
    json_bytes = json.dumps(document, separators=(",", ":")).encode()
    json_bytes += b" " * ((-len(json_bytes)) % 4)
    binary += b"\0" * ((-len(binary)) % 4)
    output = bytearray(b"glTF" + struct.pack("<II", 2, 0))
    output.extend(struct.pack("<II", len(json_bytes), 0x4E4F534A))
    output.extend(json_bytes)
    output.extend(struct.pack("<II", len(binary), 0x004E4942))
    output.extend(binary)
    struct.pack_into("<I", output, 8, len(output))
    path.write_bytes(output)


def material_map(path: Path) -> None:
    path.write_text(json.dumps({
        "schema": "n64game-tiny3d-material-map-v1",
        "materials": {
            "body_top": {
                "binding": {
                    "kind": "dynamic_reference",
                    "reference": "0x41594230",
                    "width": 64,
                    "height": 32,
                },
                "source_v_range": [0.5, 1.0],
                "cull_back": False,
            },
            "body_bottom": {
                "binding": {
                    "kind": "dynamic_reference",
                    "reference": "0x41594231",
                    "width": 64,
                    "height": 32,
                },
                "source_v_range": [0.0, 0.5],
                "cull_back": True,
            },
            "accent": {
                "binding": {
                    "kind": "static_png",
                    "path": "../filesystem/echo/echo.ayselor/accent.png",
                    "width": 32,
                    "height": 32,
                },
                "source_v_range": [0.0, 1.0],
                "cull_back": False,
            },
            "solid_trim": {
                "binding": {
                    "kind": "solid_primitive",
                    "color": [0.12, 0.28, 0.26, 1.0],
                },
                "cull_back": True,
            },
            "route_light": {
                "binding": {
                    "kind": "solid_primitive_unlit",
                    "color": [0.95, 0.42, 0.08, 1.0],
                },
                "cull_back": False,
            },
            "tinted_screen": {
                "binding": {
                    "kind": "static_png_tinted",
                    "path": "../filesystem/echo/echo.ayselor/screen.png",
                    "width": 64,
                    "height": 32,
                    "color": [0.02, 0.55, 0.72, 1.0],
                },
                "source_v_range": [0.0, 1.0],
                "cull_back": False,
            },
        },
    }, sort_keys=True) + "\n", encoding="utf-8")


def read_glb(path: Path):
    data = path.read_bytes()
    json_length = struct.unpack_from("<I", data, 12)[0]
    document = json.loads(data[20:20 + json_length].rstrip(b" "))
    binary_header = 20 + json_length
    binary_length = struct.unpack_from("<I", data, binary_header)[0]
    binary = data[binary_header + 8:binary_header + 8 + binary_length]
    return document, binary


class Tiny3DMaterialBinderTests(unittest.TestCase):
    def test_material_records_and_half_atlas_uvs_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory(prefix="n64game-material-binder-") as directory:
            root = Path(directory)
            source = root / "source.glb"
            mapping = root / "map.json"
            first = root / "first.glb"
            second = root / "second.glb"
            build_glb(source)
            material_map(mapping)
            TOOL.run(source, mapping, first)
            TOOL.run(source, mapping, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())

            document, binary = read_glb(first)
            records = {value["name"]: value["extras"]["f3d_mat"]
                       for value in document["materials"]}
            self.assertEqual(records["body_top"]["tex0"]["tex_reference"], "0x41594230")
            self.assertEqual(records["body_bottom"]["tex0"]["tex_reference_size"], [64, 32])
            self.assertEqual(
                records["accent"]["tex0"]["tex"]["name"],
                "../filesystem/echo/echo.ayselor/accent.png",
            )
            self.assertEqual(records["body_top"]["rdp_settings"]["g_mdsft_text_filt"], 0)
            self.assertEqual(records["body_bottom"]["rdp_settings"]["g_cull_back"], 1)
            self.assertEqual(records["solid_trim"]["combiner1"]["A"], 3)
            self.assertEqual(records["solid_trim"]["set_prim"], 1)
            self.assertEqual(records["solid_trim"]["prim_color"], [0.12, 0.28, 0.26, 1.0])
            self.assertNotIn("tex0", records["solid_trim"])
            self.assertEqual(records["route_light"]["combiner1"], {
                "A": 8,
                "B": 8,
                "C": 16,
                "D": 3,
                "A_alpha": 7,
                "B_alpha": 7,
                "C_alpha": 7,
                "D_alpha": 3,
            })
            self.assertEqual(records["route_light"]["set_prim"], 1)
            self.assertNotIn("tex0", records["route_light"])
            self.assertEqual(records["tinted_screen"]["combiner1"]["C"], 3)
            self.assertEqual(records["tinted_screen"]["set_prim"], 1)
            self.assertEqual(records["tinted_screen"]["tex0"]["S"]["high"], 63.0)
            self.assertEqual(records["tinted_screen"]["tex0"]["T"]["high"], 31.0)
            self.assertTrue(document["materials"][0]["extras"]["authored"])

            observed = []
            for accessor in document["accessors"]:
                view = document["bufferViews"][accessor["bufferView"]]
                start = view["byteOffset"]
                observed.append([
                    struct.unpack_from("<ff", binary, start + index * 8)
                    for index in range(accessor["count"])
                ])
            self.assertAlmostEqual(observed[0][0][1], 0.10, places=5)
            self.assertAlmostEqual(observed[0][1][1], 0.80, places=5)
            self.assertAlmostEqual(observed[1][1][1], 0.90, places=5)
            self.assertAlmostEqual(observed[2][1][1], 0.90, places=5)

    def test_uv_outside_declared_material_region_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="n64game-material-binder-bad-") as directory:
            root = Path(directory)
            source = root / "source.glb"
            mapping = root / "map.json"
            build_glb(source, bad_upper_uv=True)
            material_map(mapping)
            with self.assertRaisesRegex(TOOL.MaterialBindingError, "leaves its declared atlas region"):
                TOOL.run(source, mapping, root / "output.glb")

    def test_invalid_solid_primitive_color_fails_closed_without_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="n64game-material-binder-solid-") as directory:
            root = Path(directory)
            source = root / "source.glb"
            mapping = root / "map.json"
            output = root / "output.glb"
            build_glb(source)
            material_map(mapping)
            value = json.loads(mapping.read_text(encoding="utf-8"))
            value["materials"]["solid_trim"]["binding"]["color"][2] = 1.25
            mapping.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(TOOL.MaterialBindingError, "outside 0..1"):
                TOOL.run(source, mapping, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
