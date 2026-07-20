from __future__ import annotations

import json
import math
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_ROOT = ROOT / "runtime-candidates" / "echo"
ATTRIBUTE_SET = {
    "COLOR_0",
    "JOINTS_0",
    "NORMAL",
    "POSITION",
    "TEXCOORD_0",
    "WEIGHTS_0",
}

SPECS = {
    "ayselor": {
        "model": "ayselor_distance.glb",
        "triangles": 382,
        "triangle_ceiling": 600,
        "joints": 18,
        "materials": (
            "mat_ayselor_body_top",
            "mat_ayselor_body_bottom",
            "mat_ayselor_accent",
        ),
        "dynamic_references": ("0x41595330", "0x41595331"),
        "accent_path": "filesystem/echo/echo.ayselor/tex_ayselor_accent_ci4_32x32.png",
        "textures": {
            "tex_ayselor_body_ci8_64x64.png": (64, 64, 8, "RGB"),
            "tex_ayselor_accent_ci4_32x32.png": (32, 32, 8, "RGB"),
            "tex_ayselor_blob_shadow_ia8_32x32.png": (32, 32, 8, "LA"),
        },
    },
    "gyreclast": {
        "model": "gyreclast_distance.glb",
        "triangles": 620,
        "triangle_ceiling": 620,
        "joints": 18,
        "materials": (
            "mat_gyreclast_body_top",
            "mat_gyreclast_body_bottom",
            "mat_gyreclast_accent",
        ),
        "dynamic_references": ("0x47595230", "0x47595231"),
        "accent_path": "filesystem/echo/echo.gyreclast/tex_gyreclast_accent_ci4_32x32.png",
        "textures": {
            "tex_gyreclast_body_ci8_64x64.png": (64, 64, 8, "P"),
            "tex_gyreclast_accent_ci4_32x32.png": (32, 32, 8, "P"),
            "tex_gyreclast_blob_shadow_ia8_32x32.png": (32, 32, 8, "LA"),
        },
    },
    "kivarrax": {
        "model": "kivarrax_distance.glb",
        "triangles": 528,
        "triangle_ceiling": 540,
        "joints": 20,
        "materials": (
            "mat_kivarrax_body_top",
            "mat_kivarrax_body_bottom",
            "mat_kivarrax_accent",
        ),
        "dynamic_references": ("0x4B495630", "0x4B495631"),
        "accent_path": "filesystem/echo/echo.kivarrax/tex_kivarrax_accent_ci4_32x32.png",
        "textures": {
            "tex_kivarrax_body_ci8_64x64.png": (64, 64, 8, "RGBA"),
            "tex_kivarrax_accent_ci4_32x32.png": (32, 32, 8, "RGBA"),
            "tex_kivarrax_blob_shadow_ia8_32x32.png": (32, 32, 8, "RGBA"),
        },
    },
}


def load_glb(path: Path) -> tuple[dict[str, object], bytes]:
    payload = path.read_bytes()
    if len(payload) < 28 or payload[:4] != b"glTF":
        raise AssertionError(f"{path.name} is not one GLB")
    version, total_length = struct.unpack_from("<II", payload, 4)
    if version != 2 or total_length != len(payload):
        raise AssertionError(f"{path.name} has a malformed GLB header")

    json_length, json_type = struct.unpack_from("<II", payload, 12)
    if json_type != 0x4E4F534A:
        raise AssertionError(f"{path.name} has no JSON chunk")
    json_end = 20 + json_length
    document = json.loads(
        payload[20:json_end].decode("utf-8").rstrip(" \t\r\n\x00")
    )

    if json_end + 8 > len(payload):
        raise AssertionError(f"{path.name} has no binary chunk header")
    binary_length, binary_type = struct.unpack_from("<II", payload, json_end)
    if binary_type != 0x004E4942:
        raise AssertionError(f"{path.name} has no binary chunk")
    binary_end = json_end + 8 + binary_length
    if binary_end != len(payload):
        raise AssertionError(f"{path.name} has a malformed binary chunk")
    return document, payload[json_end + 8:binary_end]


def accessor_values(
    document: dict[str, object], binary: bytes, accessor_index: int
) -> list[tuple[int | float, ...]]:
    accessor = document["accessors"][accessor_index]
    if "sparse" in accessor or "bufferView" not in accessor:
        raise AssertionError("support candidate accessors must be dense")
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
        raise AssertionError("support candidate accessor escapes its binary chunk")
    return [record.unpack_from(binary, offset + index * stride) for index in range(count)]


def png_profile(path: Path) -> tuple[int, int, int, str]:
    payload = path.read_bytes()
    if payload[:8] != b"\x89PNG\r\n\x1a\n" or payload[12:16] != b"IHDR":
        raise AssertionError(f"{path.name} is not a canonical PNG")
    width, height, depth, color_type, compression, filtering, interlace = struct.unpack_from(
        ">IIBBBBB", payload, 16
    )
    if (compression, filtering, interlace) != (0, 0, 0):
        raise AssertionError(f"{path.name} has an unsupported PNG profile")
    modes = {0: "L", 2: "RGB", 3: "P", 4: "LA", 6: "RGBA"}
    if color_type not in modes:
        raise AssertionError(f"{path.name} has an unsupported PNG color type")
    return width, height, depth, modes[color_type]


class SupportEchoRuntimeCandidateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.candidates: dict[str, tuple[dict[str, object], bytes]] = {}
        for name, spec in SPECS.items():
            model_path = CANDIDATE_ROOT / f"echo.{name}" / spec["model"]
            cls.candidates[name] = load_glb(model_path)

    def test_exact_geometry_material_and_skin_budgets(self) -> None:
        for name, spec in SPECS.items():
            with self.subTest(candidate=name):
                document, _binary = self.candidates[name]
                self.assertEqual(len(document["meshes"]), 1)
                self.assertEqual(len(document["skins"]), 1)
                self.assertEqual(len(document["materials"]), 3)
                self.assertEqual(
                    tuple(material["name"] for material in document["materials"]),
                    spec["materials"],
                )
                self.assertEqual(len(document["skins"][0]["joints"]), spec["joints"])

                primitives = document["meshes"][0]["primitives"]
                self.assertEqual({primitive["material"] for primitive in primitives}, {0, 1, 2})
                self.assertTrue(all(primitive.get("mode", 4) == 4 for primitive in primitives))
                index_counts = [
                    int(document["accessors"][primitive["indices"]]["count"])
                    for primitive in primitives
                ]
                self.assertTrue(all(count > 0 and count % 3 == 0 for count in index_counts))
                triangles = sum(index_counts) // 3
                self.assertEqual(triangles, spec["triangles"])
                self.assertLessEqual(triangles, spec["triangle_ceiling"])

    def test_exact_reduced_animation_set_and_no_embedded_images(self) -> None:
        expected_animations = {"idle_a", "reposition", "hit"}
        for name in SPECS:
            with self.subTest(candidate=name):
                document, _binary = self.candidates[name]
                animations = document["animations"]
                self.assertEqual(len(animations), 3)
                self.assertEqual({animation["name"] for animation in animations}, expected_animations)
                self.assertEqual(document.get("images", []), [])

    def test_every_exported_vertex_has_exactly_one_full_weight_influence(self) -> None:
        for name, spec in SPECS.items():
            with self.subTest(candidate=name):
                document, binary = self.candidates[name]
                joint_count = int(spec["joints"])
                for primitive in document["meshes"][0]["primitives"]:
                    attributes = primitive["attributes"]
                    self.assertEqual(set(attributes), ATTRIBUTE_SET)
                    positions = accessor_values(document, binary, attributes["POSITION"])
                    joints = accessor_values(document, binary, attributes["JOINTS_0"])
                    weights = accessor_values(document, binary, attributes["WEIGHTS_0"])
                    self.assertEqual(len(positions), len(joints))
                    self.assertEqual(len(positions), len(weights))
                    for vertex_joints, vertex_weights in zip(joints, weights):
                        weight_values = tuple(float(value) for value in vertex_weights)
                        nonzero_slots = [
                            index for index, value in enumerate(weight_values)
                            if not math.isclose(value, 0.0, abs_tol=1e-8)
                        ]
                        self.assertEqual(len(nonzero_slots), 1)
                        self.assertTrue(math.isclose(sum(weight_values), 1.0, abs_tol=1e-7))
                        self.assertLess(int(vertex_joints[nonzero_slots[0]]), joint_count)

    def test_exact_dynamic_body_references_and_direct_accent_path(self) -> None:
        for name, spec in SPECS.items():
            with self.subTest(candidate=name):
                document, _binary = self.candidates[name]
                texture_records = [
                    material["extras"]["f3d_mat"]["tex0"]
                    for material in document["materials"]
                ]
                dynamic = [
                    texture for texture in texture_records
                    if int(texture["use_tex_reference"]) == 1
                ]
                direct = [
                    texture for texture in texture_records
                    if int(texture["use_tex_reference"]) == 0
                ]
                self.assertEqual(
                    tuple(texture["tex_reference"] for texture in dynamic),
                    spec["dynamic_references"],
                )
                self.assertTrue(all(texture["tex_reference_size"] == [64, 32] for texture in dynamic))
                self.assertTrue(all("tex" not in texture for texture in dynamic))
                self.assertEqual(len(direct), 1)
                self.assertEqual(direct[0]["tex"]["name"], spec["accent_path"])
                self.assertNotIn("tex_reference", direct[0])

    def test_source_texture_dimensions_and_modes_are_exact(self) -> None:
        for name, spec in SPECS.items():
            candidate_dir = CANDIDATE_ROOT / f"echo.{name}"
            for filename, expected_profile in spec["textures"].items():
                with self.subTest(candidate=name, texture=filename):
                    self.assertEqual(png_profile(candidate_dir / filename), expected_profile)


if __name__ == "__main__":
    unittest.main()
