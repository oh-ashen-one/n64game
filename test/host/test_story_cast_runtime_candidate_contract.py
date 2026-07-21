from __future__ import annotations

import json
import math
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

SPECS = {
    "sera": {
        "directory": ROOT / "runtime-candidates" / "chr" / "chr.sera_venn",
        "model": "sera_venn_distance.glb",
        "triangles": 1182,
        "joints": 22,
        "materials": (
            "mat_sera_clinic_cream",
            "mat_sera_diagnostic_teal",
            "mat_sera_face_skin",
            "mat_sera_signal_amber",
        ),
        "material_textures": (
            "filesystem/chr/chr.sera_venn/tex_sera_venn_body_ci4_64x64.png",
            "filesystem/chr/chr.sera_venn/tex_sera_venn_body_ci4_64x64.png",
            "filesystem/chr/chr.sera_venn/tex_sera_venn_face_ci4_32x32.png",
            "filesystem/chr/chr.sera_venn/tex_sera_venn_accent_ci4_32x32.png",
        ),
        "animations": (
            "idle_a",
            "diagnostic_scan",
            "explain_starter",
            "react_fracture",
        ),
        "textures": {
            "tex_sera_venn_body_ci4_64x64.png": (64, 64, 3),
            "tex_sera_venn_face_ci4_32x32.png": (32, 32, 3),
            "tex_sera_venn_accent_ci4_32x32.png": (32, 32, 3),
        },
    },
    "tavi": {
        "directory": ROOT / "runtime-candidates" / "chr" / "chr.tavi",
        "model": "tavi_distance.glb",
        "triangles": 780,
        "joints": 20,
        "materials": (
            "mat_tavi_indigo",
            "mat_tavi_sun_cloth",
            "mat_tavi_coral_scarf",
            "mat_tavi_face_accent",
        ),
        "material_textures": (
            "filesystem/chr/chr.tavi/tex_tavi_body_ci4_64x64.png",
            "filesystem/chr/chr.tavi/tex_tavi_body_ci4_64x64.png",
            "filesystem/chr/chr.tavi/tex_tavi_body_ci4_64x64.png",
            "filesystem/chr/chr.tavi/tex_tavi_face_accent_ci4_32x32.png",
        ),
        "animations": ("idle_a", "greet", "listen", "reaction"),
        "textures": {
            "tex_tavi_body_ci4_64x64.png": (64, 64, 3),
            "tex_tavi_face_accent_ci4_32x32.png": (32, 32, 3),
        },
    },
    "beacon": {
        "directory": (
            ROOT
            / "runtime-candidates"
            / "prop"
            / "prop.annex.beacon_decoder"
        ),
        "model": "annex_beacon_decoder.glb",
        "triangles": 766,
        "joints": 10,
        "materials": (
            "mat_annex_beacon_teal",
            "mat_annex_beacon_cream",
            "mat_annex_beacon_brass",
            "mat_annex_beacon_signal",
        ),
        "material_textures": (
            "filesystem/prop/prop.annex.beacon_decoder/tex_annex_beacon_body_ci4_64x64.png",
            "filesystem/prop/prop.annex.beacon_decoder/tex_annex_beacon_body_ci4_64x64.png",
            "filesystem/prop/prop.annex.beacon_decoder/tex_annex_beacon_body_ci4_64x64.png",
            "filesystem/prop/prop.annex.beacon_decoder/tex_annex_beacon_signal_ci4_32x32.png",
        ),
        "animations": ("idle_aim", "beacon_acquire", "fracture"),
        "textures": {
            "tex_annex_beacon_body_ci4_64x64.png": (64, 64, 3),
            "tex_annex_beacon_signal_ci4_32x32.png": (32, 32, 3),
            "tex_annex_beacon_shadow_ia8_32x32.png": (32, 32, 4),
        },
    },
}


def load_glb(path: Path) -> tuple[dict[str, object], bytes]:
    payload = path.read_bytes()
    if len(payload) < 28 or payload[:4] != b"glTF":
        raise AssertionError(f"{path.name} is not a GLB")
    version, total_length = struct.unpack_from("<II", payload, 4)
    if version != 2 or total_length != len(payload):
        raise AssertionError(f"{path.name} has a malformed header")
    json_length, json_type = struct.unpack_from("<II", payload, 12)
    if json_type != 0x4E4F534A:
        raise AssertionError(f"{path.name} has no JSON chunk")
    json_end = 20 + json_length
    document = json.loads(
        payload[20:json_end].decode("utf-8").rstrip(" \t\r\n\x00")
    )
    binary_length, binary_type = struct.unpack_from("<II", payload, json_end)
    if binary_type != 0x004E4942:
        raise AssertionError(f"{path.name} has no binary chunk")
    binary = payload[json_end + 8 : json_end + 8 + binary_length]
    if json_end + 8 + binary_length != len(payload):
        raise AssertionError(f"{path.name} has malformed binary data")
    return document, binary


def accessor_values(
    document: dict[str, object], binary: bytes, accessor_index: int
) -> list[tuple[int | float, ...]]:
    accessor = document["accessors"][accessor_index]
    if "sparse" in accessor or "bufferView" not in accessor:
        raise AssertionError("story-cast accessors must be dense")
    view = document["bufferViews"][accessor["bufferView"]]
    formats = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
    widths = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
    record = struct.Struct(
        "<"
        + formats[accessor["componentType"]] * widths[accessor["type"]]
    )
    stride = int(view.get("byteStride", record.size))
    offset = int(view.get("byteOffset", 0)) + int(accessor.get("byteOffset", 0))
    count = int(accessor["count"])
    if stride < record.size or offset + (count - 1) * stride + record.size > len(binary):
        raise AssertionError("story-cast accessor escapes its binary chunk")
    return [record.unpack_from(binary, offset + index * stride) for index in range(count)]


def png_profile(path: Path) -> tuple[int, int, int, int]:
    payload = path.read_bytes()
    if payload[:8] != b"\x89PNG\r\n\x1a\n" or payload[12:16] != b"IHDR":
        raise AssertionError(f"{path.name} is not a canonical PNG")
    width, height, depth, color_type = struct.unpack_from(">IIBB", payload, 16)
    return width, height, depth, color_type


class StoryCastRuntimeCandidateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.candidates = {
            name: load_glb(spec["directory"] / spec["model"])
            for name, spec in SPECS.items()
        }

    def test_exact_authored_geometry_material_skin_and_animation_contracts(self) -> None:
        for name, spec in SPECS.items():
            with self.subTest(candidate=name):
                document, _binary = self.candidates[name]
                self.assertEqual(len(document["meshes"]), 1)
                self.assertEqual(len(document["skins"]), 1)
                self.assertEqual(document.get("images", []), [])
                self.assertEqual(
                    tuple(material["name"] for material in document["materials"]),
                    spec["materials"],
                )
                material_textures: list[str] = []
                for material in document["materials"]:
                    tex0 = material["extras"]["f3d_mat"]["tex0"]
                    self.assertEqual(tex0.get("use_tex_reference"), 0)
                    self.assertNotIn("tex_reference", tex0)
                    self.assertNotIn("tex_reference_size", tex0)
                    material_textures.append(tex0["tex"]["name"])
                self.assertEqual(
                    tuple(material_textures),
                    spec["material_textures"],
                )
                self.assertEqual(len(document["skins"][0]["joints"]), spec["joints"])
                self.assertEqual(
                    tuple(animation["name"] for animation in document["animations"]),
                    spec["animations"],
                )
                for animation in document["animations"]:
                    inputs = {sampler["input"] for sampler in animation["samplers"]}
                    ends = {
                        float(document["accessors"][index]["max"][0])
                        for index in inputs
                    }
                    self.assertEqual(len(ends), 1)
                    self.assertGreater(ends.pop(), 0.0)
                primitives = document["meshes"][0]["primitives"]
                triangle_count = sum(
                    int(document["accessors"][primitive["indices"]]["count"])
                    for primitive in primitives
                ) // 3
                self.assertEqual(triangle_count, spec["triangles"])

    def test_all_vertices_have_one_full_weight_and_each_triangle_one_bone(self) -> None:
        for name, spec in SPECS.items():
            with self.subTest(candidate=name):
                document, binary = self.candidates[name]
                for primitive in document["meshes"][0]["primitives"]:
                    attributes = primitive["attributes"]
                    joints = accessor_values(document, binary, attributes["JOINTS_0"])
                    weights = accessor_values(document, binary, attributes["WEIGHTS_0"])
                    indices = accessor_values(document, binary, primitive["indices"])
                    self.assertEqual(len(joints), len(weights))
                    dominant_joints: list[int] = []
                    for vertex_joints, vertex_weights in zip(joints, weights):
                        nonzero = [
                            index
                            for index, value in enumerate(vertex_weights)
                            if not math.isclose(float(value), 0.0, abs_tol=1e-8)
                        ]
                        self.assertEqual(len(nonzero), 1)
                        self.assertTrue(
                            math.isclose(
                                sum(float(value) for value in vertex_weights),
                                1.0,
                                abs_tol=1e-7,
                            )
                        )
                        joint = int(vertex_joints[nonzero[0]])
                        self.assertLess(joint, spec["joints"])
                        dominant_joints.append(joint)
                    flat_indices = [int(value[0]) for value in indices]
                    self.assertEqual(len(flat_indices) % 3, 0)
                    for offset in range(0, len(flat_indices), 3):
                        triangle_bones = {
                            dominant_joints[flat_indices[offset + corner]]
                            for corner in range(3)
                        }
                        self.assertEqual(len(triangle_bones), 1)

    def test_source_textures_are_exact_n64_profiles(self) -> None:
        for name, spec in SPECS.items():
            for filename, (width, height, color_type) in spec["textures"].items():
                with self.subTest(candidate=name, texture=filename):
                    self.assertEqual(
                        png_profile(spec["directory"] / filename),
                        (width, height, 8, color_type),
                    )


if __name__ == "__main__":
    unittest.main()
