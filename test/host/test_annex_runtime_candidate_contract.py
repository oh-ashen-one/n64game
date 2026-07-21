from __future__ import annotations

import json
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "runtime-candidates" / "env" / "env.annex.threshold_kit"
MODEL = CANDIDATE / "annex_threshold_kit.glb"


def load_glb() -> tuple[dict[str, object], bytes]:
    payload = MODEL.read_bytes()
    if len(payload) < 28 or payload[:4] != b"glTF":
        raise AssertionError("Annex candidate is not one GLB")
    version, total = struct.unpack_from("<II", payload, 4)
    if version != 2 or total != len(payload):
        raise AssertionError("Annex candidate GLB header is malformed")
    json_length, json_type = struct.unpack_from("<II", payload, 12)
    if json_type != 0x4E4F534A:
        raise AssertionError("Annex candidate GLB JSON chunk is missing")
    document = json.loads(
        payload[20:20 + json_length].decode("utf-8").rstrip(" \t\r\n\x00")
    )
    binary_header = 20 + json_length
    binary_length, binary_type = struct.unpack_from("<II", payload, binary_header)
    if binary_type != 0x004E4942:
        raise AssertionError("Annex candidate GLB binary chunk is missing")
    binary = payload[binary_header + 8:binary_header + 8 + binary_length]
    if len(binary) != binary_length:
        raise AssertionError("Annex candidate GLB binary chunk is truncated")
    return document, binary


def accessor_values(
    document: dict[str, object], binary: bytes, accessor_index: int
) -> list[tuple[int | float, ...]]:
    accessor = document["accessors"][accessor_index]
    if "sparse" in accessor:
        raise AssertionError("Annex candidate accessors must not be sparse")
    view = document["bufferViews"][accessor["bufferView"]]
    formats = {
        5120: "b",
        5121: "B",
        5122: "h",
        5123: "H",
        5125: "I",
        5126: "f",
    }
    widths = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
    scalar = formats[accessor["componentType"]]
    width = widths[accessor["type"]]
    record = struct.Struct("<" + scalar * width)
    stride = int(view.get("byteStride", record.size))
    offset = int(view.get("byteOffset", 0)) + int(accessor.get("byteOffset", 0))
    count = int(accessor["count"])
    if stride < record.size or offset + (count - 1) * stride + record.size > len(binary):
        raise AssertionError("Annex candidate accessor escapes its binary chunk")
    return [record.unpack_from(binary, offset + index * stride) for index in range(count)]


class AnnexRuntimeCandidateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document, cls.binary = load_glb()
        cls.materials = cls.document["materials"]
        cls.material_index = {
            material["name"]: index for index, material in enumerate(cls.materials)
        }
        cls.primitives = cls.document["meshes"][0]["primitives"]
        cls.primitive_by_material = {
            cls.materials[primitive["material"]]["name"]: primitive
            for primitive in cls.primitives
        }

    def test_candidate_is_one_static_mesh_with_exact_budget(self) -> None:
        self.assertNotIn("animations", self.document)
        self.assertNotIn("skins", self.document)
        self.assertEqual(len(self.document["nodes"]), 1)
        self.assertEqual(len(self.document["meshes"]), 1)
        self.assertEqual(len(self.materials), 19)
        self.assertEqual(len(self.primitives), 19)
        self.assertEqual(len(self.primitive_by_material), 19)
        self.assertTrue(all(primitive.get("mode", 4) == 4 for primitive in self.primitives))
        triangle_count = sum(
            int(self.document["accessors"][primitive["indices"]]["count"]) // 3
            for primitive in self.primitives
        )
        self.assertEqual(triangle_count, 3584)

    def test_every_batch_has_one_uv_and_baked_vertex_color(self) -> None:
        for primitive in self.primitives:
            attributes = primitive["attributes"]
            self.assertIn("POSITION", attributes)
            self.assertIn("NORMAL", attributes)
            self.assertIn("TEXCOORD_0", attributes)
            self.assertIn("COLOR_0", attributes)
            self.assertFalse(any(
                name.startswith("TEXCOORD_") and name != "TEXCOORD_0"
                for name in attributes
            ))

    def test_fast64_materials_bind_exact_three_candidate_textures(self) -> None:
        expected = {
            "MAT_Annex_Architecture_CI4": "tex_annex_architecture_ci4_64x64.png",
            "MAT_Annex_TrimGlyph_CI4": "tex_annex_trim_resonance_ci4_64x32.png",
            "mat.annex.screen_ia8": "tex_annex_resonance_mask_ia8_32x32.png",
        }
        observed: dict[str, str] = {}
        for material in self.materials:
            f3d = material.get("extras", {}).get("f3d_mat")
            self.assertIsNotNone(f3d, material["name"])
            self.assertEqual(f3d["rdp_settings"]["g_mdsft_cycletype"], 0)
            self.assertEqual(f3d["rdp_settings"]["g_mdsft_text_filt"], 0)
            self.assertEqual(f3d["rdp_settings"]["g_fog"], 0)
            self.assertEqual(f3d["rdp_settings"]["g_tex_gen"], 0)
            combiner = f3d["combiner1"]
            if "tex0" in f3d:
                observed[material["name"]] = f3d["tex0"]["tex"]["name"]
                self.assertEqual(
                    (combiner["A"], combiner["B"], combiner["C"], combiner["D"]),
                    (1, 5, 4, 5),
                )
            else:
                self.assertEqual(
                    (combiner["A"], combiner["B"], combiner["C"], combiner["D"]),
                    (3, 5, 4, 5),
                )
        self.assertEqual(observed, expected)

    def test_trim_atlas_has_authored_uv_variation(self) -> None:
        primitive = self.primitive_by_material["MAT_Annex_TrimGlyph_CI4"]
        values = accessor_values(
            self.document, self.binary, primitive["attributes"]["TEXCOORD_0"]
        )
        unique = {(round(float(u), 6), round(float(v), 6)) for u, v in values}
        self.assertGreaterEqual(len(unique), 4)
        self.assertAlmostEqual(min(u for u, _ in unique), 0.0, places=5)
        self.assertAlmostEqual(max(u for u, _ in unique), 1.0, places=5)
        self.assertGreater(max(v for _, v in unique) - min(v for _, v in unique), 0.20)

    def test_prop_state_colors_survive_instance_consolidation(self) -> None:
        expected_variants = {
            "mat.annex.state": 6,
            "mat.annex.screen_ia8": 2,
        }
        for material_name, minimum in expected_variants.items():
            primitive = self.primitive_by_material[material_name]
            values = accessor_values(
                self.document, self.binary, primitive["attributes"]["COLOR_0"]
            )
            unique = set(values)
            self.assertGreaterEqual(len(unique), minimum, material_name)

    def test_source_png_profiles_are_exact(self) -> None:
        expected = {
            "tex_annex_architecture_ci4_64x64.png": (64, 64, 8, 3),
            "tex_annex_trim_resonance_ci4_64x32.png": (64, 32, 4, 3),
            "tex_annex_resonance_mask_ia8_32x32.png": (32, 32, 8, 4),
        }
        for filename, identity in expected.items():
            payload = (CANDIDATE / filename).read_bytes()
            self.assertEqual(payload[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(payload[12:16], b"IHDR")
            self.assertEqual(struct.unpack(">IIBB", payload[16:26]), identity)

    def test_every_direct_runtime_texture_fits_one_tmem_upload(self) -> None:
        # Libdragon reserves half of TMEM for a CI palette. This exact budget
        # guards the native assertion that a CI8 64x64 candidate exposed.
        specs = (
            ("CI4", 64, 64),
            ("CI4", 64, 32),
            ("IA8", 32, 32),
        )
        bits_per_pixel = {"CI4": 4, "IA8": 8}
        for format_name, width, height in specs:
            row_bytes = (width * bits_per_pixel[format_name] + 7) // 8
            aligned_row_bytes = (row_bytes + 7) & ~7
            palette_bytes = 2048 if format_name == "CI4" else 0
            tmem_bytes = aligned_row_bytes * height + palette_bytes
            self.assertLessEqual(tmem_bytes, 4096, format_name)


if __name__ == "__main__":
    unittest.main()
