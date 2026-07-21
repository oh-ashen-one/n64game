from __future__ import annotations

import json
import math
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "runtime-candidates" / "chr" / "chr.player.ari"
MODEL = CANDIDATE / "player_ari.glb"
EXPECTED_JOINTS = (
    "b_root_c",
    "b_pelvis_c",
    "b_spine_a_c",
    "b_spine_b_c",
    "b_chest_c",
    "b_neck_c",
    "b_head_c",
    "b_ponytail_c",
    "b_clavicle_l",
    "b_upperarm_l",
    "b_forearm_l",
    "b_hand_l",
    "b_clavicle_r",
    "b_upperarm_r",
    "b_forearm_r",
    "b_hand_r",
    "b_thigh_l",
    "b_shin_l",
    "b_foot_l",
    "b_toe_l",
    "b_thigh_r",
    "b_shin_r",
    "b_foot_r",
    "b_toe_r",
)


def load_glb() -> tuple[dict[str, object], bytes]:
    payload = MODEL.read_bytes()
    if len(payload) < 28 or payload[:4] != b"glTF":
        raise AssertionError("Ari candidate is not one GLB")
    version, total = struct.unpack_from("<II", payload, 4)
    if version != 2 or total != len(payload):
        raise AssertionError("Ari candidate GLB header is malformed")
    json_length, json_type = struct.unpack_from("<II", payload, 12)
    if json_type != 0x4E4F534A:
        raise AssertionError("Ari candidate GLB JSON chunk is missing")
    document = json.loads(
        payload[20:20 + json_length].decode("utf-8").rstrip(" \t\r\n\x00")
    )
    binary_header = 20 + json_length
    binary_length, binary_type = struct.unpack_from("<II", payload, binary_header)
    if binary_type != 0x004E4942:
        raise AssertionError("Ari candidate GLB binary chunk is missing")
    binary = payload[binary_header + 8:binary_header + 8 + binary_length]
    if len(binary) != binary_length:
        raise AssertionError("Ari candidate GLB binary chunk is truncated")
    return document, binary


def accessor_values(
    document: dict[str, object], binary: bytes, accessor_index: int
) -> list[tuple[int | float, ...]]:
    accessor = document["accessors"][accessor_index]
    if "sparse" in accessor:
        raise AssertionError("Ari candidate accessors must not be sparse")
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
        raise AssertionError("Ari candidate accessor escapes its binary chunk")
    return [record.unpack_from(binary, offset + index * stride) for index in range(count)]


def png_dimensions(path: Path) -> tuple[int, int, int, int]:
    payload = path.read_bytes()
    if payload[:8] != b"\x89PNG\r\n\x1a\n" or payload[12:16] != b"IHDR":
        raise AssertionError(f"{path.name} is not a canonical PNG")
    width, height, depth, color_type = struct.unpack_from(">IIBB", payload, 16)
    return width, height, depth, color_type


class PlayerRuntimeCandidateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document, cls.binary = load_glb()
        cls.mesh = cls.document["meshes"][0]
        cls.materials = cls.document["materials"]

    def test_candidate_has_exact_reduced_native_iteration_package(self) -> None:
        self.assertEqual(len(self.document["meshes"]), 1)
        self.assertEqual(len(self.document["skins"]), 1)
        self.assertEqual(
            tuple(animation["name"] for animation in self.document["animations"]),
            ("idle_a", "walk", "run"),
        )
        expected_duration = {"idle_a": 3.0, "walk": 0.8, "run": 0.6}
        for animation in self.document["animations"]:
            input_accessors = {
                sampler["input"] for sampler in animation["samplers"]
            }
            starts = {
                float(self.document["accessors"][index]["min"][0])
                for index in input_accessors
            }
            ends = {
                float(self.document["accessors"][index]["max"][0])
                for index in input_accessors
            }
            self.assertEqual(starts, {0.0})
            self.assertEqual(len(ends), 1)
            self.assertTrue(
                math.isclose(ends.pop(), expected_duration[animation["name"]], abs_tol=1e-6)
            )

    def test_skin_keeps_exact_one_weight_24_joint_contract(self) -> None:
        skin = self.document["skins"][0]
        joint_names = tuple(self.document["nodes"][index]["name"] for index in skin["joints"])
        self.assertEqual(joint_names, EXPECTED_JOINTS)
        for primitive in self.mesh["primitives"]:
            attributes = primitive["attributes"]
            self.assertEqual(
                set(attributes),
                {"COLOR_0", "JOINTS_0", "NORMAL", "POSITION", "TEXCOORD_0", "WEIGHTS_0"},
            )
            joints = accessor_values(self.document, self.binary, attributes["JOINTS_0"])
            weights = accessor_values(self.document, self.binary, attributes["WEIGHTS_0"])
            self.assertEqual(len(joints), len(weights))
            for vertex_joints, vertex_weights in zip(joints, weights):
                self.assertLess(int(vertex_joints[0]), len(EXPECTED_JOINTS))
                self.assertEqual(tuple(int(value) for value in vertex_joints[1:]), (0, 0, 0))
                self.assertEqual(tuple(float(value) for value in vertex_weights), (1.0, 0.0, 0.0, 0.0))

    def test_geometry_and_materials_match_the_candidate_budget(self) -> None:
        self.assertEqual(
            tuple(material["name"] for material in self.materials),
            (
                "mat_player_ari_body_top",
                "mat_player_ari_body_bottom",
                "mat_player_ari_face",
            ),
        )
        triangle_count = sum(
            int(self.document["accessors"][primitive["indices"]]["count"]) // 3
            for primitive in self.mesh["primitives"]
        )
        self.assertEqual(triangle_count, 1146)
        minimum_y = min(
            float(self.document["accessors"][primitive["attributes"]["POSITION"]]["min"][1])
            for primitive in self.mesh["primitives"]
        )
        maximum_y = max(
            float(self.document["accessors"][primitive["attributes"]["POSITION"]]["max"][1])
            for primitive in self.mesh["primitives"]
        )
        self.assertTrue(math.isclose(minimum_y, 0.0, abs_tol=1e-7))
        self.assertTrue(math.isclose(maximum_y, 1.72, abs_tol=1e-6))

        top = self.materials[0]["extras"]["f3d_mat"]["tex0"]
        bottom = self.materials[1]["extras"]["f3d_mat"]["tex0"]
        face = self.materials[2]["extras"]["f3d_mat"]["tex0"]
        self.assertEqual(top["tex_reference"], "0x41524930")
        self.assertEqual(bottom["tex_reference"], "0x41524931")
        self.assertEqual(top["tex_reference_size"], [64, 32])
        self.assertEqual(bottom["tex_reference_size"], [64, 32])
        self.assertEqual(
            face["tex"]["name"],
            "filesystem/chr/chr.player.ari/tex_player_ari_face_ci4_32x32.png",
        )

    def test_source_textures_have_exact_dimensions(self) -> None:
        self.assertEqual(
            png_dimensions(CANDIDATE / "tex_player_ari_body_ci8_64x64.png"),
            (64, 64, 8, 2),
        )
        self.assertEqual(
            png_dimensions(CANDIDATE / "tex_player_ari_face_ci4_32x32.png"),
            (32, 32, 8, 2),
        )


if __name__ == "__main__":
    unittest.main()
