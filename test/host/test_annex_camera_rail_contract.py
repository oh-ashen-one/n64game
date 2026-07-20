from __future__ import annotations

import math
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RENDER_SOURCE = ROOT / "src" / "n64game_render.c"
RENDER_HEADER = ROOT / "src" / "n64game_render.h"
ANNEX_SOURCE = ROOT / "src" / "n64game_annex.c"

BOOM_DISTANCE = 18.0
LOOK_LEAD = 5.0
SAFE_HALF_EXTENT = 20.0
SWITCH_LOCAL_Z = SAFE_HALF_EXTENT - BOOM_DISTANCE
NEAR_PLANE = 8.0
CAMERA_Y = -4.0
TARGET_Y = -12.0

# These values intentionally duplicate the authored world contract instead of
# deriving expected geometry from the renderer under test.
PRIMARY_ROOMS = {
    "atrium": {
        "bounds": (-44.0, 20.0, -40.0, 24.0),
        "anchor": (-12.0, -8.0),
        "yaw": 0.0,
    },
    "simulation": {
        "bounds": (-116.0, -52.0, -40.0, 24.0),
        "anchor": (-84.0, -8.0),
        "yaw": math.pi / 2.0,
    },
    "workshop": {
        "bounds": (28.0, 92.0, -20.0, 44.0),
        "anchor": (60.0, 12.0),
        "yaw": -math.pi / 2.0,
    },
    "overlook": {
        "bounds": (84.0, 148.0, 36.0, 100.0),
        "anchor": (116.0, 68.0),
        "yaw": math.pi,
    },
}

CONNECTORS = {
    "simulation_connector": {
        "bounds": (-54.0, -42.0, -20.0, 20.0),
        "sector": "simulation",
    },
    "workshop_connector": {
        "bounds": (18.0, 30.0, 0.0, 24.0),
        "sector": "workshop",
    },
    "overlook_connector": {
        "bounds": (82.0, 94.0, 34.0, 56.0),
        "sector": "overlook",
    },
}

INTERACTIONS = {
    "sera": ("atrium", -38.0, -8.0),
    "field_relay": ("workshop", 52.0, 18.0),
    "tavi": ("atrium", 5.0, -34.0),
    "beacon": ("overlook", 100.0, 50.0),
    "simulation_ring": ("simulation", -66.0, 10.0),
    "atrium_map": ("atrium", 0.0, 24.0),
    "workshop_log": ("workshop", 58.0, -6.0),
    "overlook_scope": ("overlook", 86.0, 56.0),
}


def function_body(source: str, name: str) -> str:
    match = re.search(rf"\b{name}\s*\([^;]*?\)\s*\{{", source, re.DOTALL)
    if match is None:
        raise AssertionError(f"missing function: {name}")
    depth = 1
    cursor = match.end()
    while cursor < len(source) and depth:
        depth += (source[cursor] == "{") - (source[cursor] == "}")
        cursor += 1
    if depth != 0:
        raise AssertionError(f"unterminated function: {name}")
    return source[match.end():cursor - 1]


def compact(source: str) -> str:
    return " ".join(source.split())


def world_to_sector_local(
    world_x: float,
    world_z: float,
    anchor: tuple[float, float],
    yaw: float,
) -> tuple[float, float]:
    delta_x = world_x - anchor[0]
    delta_z = world_z - anchor[1]
    sine = math.sin(yaw)
    cosine = math.cos(yaw)
    return (
        cosine * delta_x + sine * delta_z,
        -sine * delta_x + cosine * delta_z,
    )


def initial_boom_side(player_local_z: float) -> int:
    return -1 if player_local_z > 0.0 else 1


def update_boom_side(side: int, player_local_z: float) -> tuple[int, int]:
    if side > 0 and player_local_z > SWITCH_LOCAL_Z:
        return -1, 8
    if side < 0 and player_local_z < -SWITCH_LOCAL_Z:
        return 1, 8
    return side, 0


def clamp_camera_local(value: float) -> float:
    return max(-SAFE_HALF_EXTENT, min(SAFE_HALF_EXTENT, value))


def rail_geometry(
    player_local_x: float,
    player_local_z: float,
    side: int,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    if side not in (-1, 1):
        raise AssertionError(f"invalid rail side: {side}")
    eye = (
        clamp_camera_local(player_local_x),
        CAMERA_Y,
        clamp_camera_local(player_local_z + side * BOOM_DISTANCE),
    )
    target = (
        player_local_x,
        TARGET_Y,
        player_local_z - side * LOOK_LEAD,
    )
    return eye, target


class AnnexCameraRailContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.render = RENDER_SOURCE.read_text(encoding="utf-8")
        cls.header = RENDER_HEADER.read_text(encoding="utf-8")
        cls.annex = ANNEX_SOURCE.read_text(encoding="utf-8")

    def assert_safe_view(
        self,
        label: str,
        player_local_x: float,
        player_local_z: float,
    ) -> None:
        selected_sides = [
            ("initial", initial_boom_side(player_local_z)),
        ]
        for incoming_side in (-1, 1):
            selected_side, _ = update_boom_side(incoming_side, player_local_z)
            selected_sides.append((f"incoming {incoming_side:+d}", selected_side))
        for path, side in selected_sides:
            eye, target = rail_geometry(player_local_x, player_local_z, side)
            state = f"{label}, {path}, selected {side:+d}"
            self.assertAlmostEqual(
                eye[0], clamp_camera_local(player_local_x), places=6, msg=state
            )
            self.assertGreaterEqual(
                eye[0], -SAFE_HALF_EXTENT - 1e-6, msg=state
            )
            self.assertLessEqual(
                eye[0], SAFE_HALF_EXTENT + 1e-6, msg=state
            )
            self.assertGreaterEqual(
                eye[2], -SAFE_HALF_EXTENT - 1e-6, msg=state
            )
            self.assertLessEqual(
                eye[2], SAFE_HALF_EXTENT + 1e-6, msg=state
            )
            self.assertAlmostEqual(target[0], player_local_x, places=6, msg=state)
            distance = math.dist(eye, target)
            self.assertGreater(distance, NEAR_PLANE, msg=state)

    def test_source_contract_is_exact_two_sided_sector_local_rail(self) -> None:
        for expression in (
            r"ANNEX_CAMERA_FADE_FRAMES\s*=\s*8",
            r"ANNEX_CAMERA_BOOM_DISTANCE\s*=\s*18",
            r"ANNEX_CAMERA_LOOK_LEAD\s*=\s*5",
            r"ANNEX_CAMERA_SAFE_HALF_EXTENT\s*=\s*20",
            r"ANNEX_CAMERA_SWITCH_LOCAL_Z\s*=\s*"
            r"ANNEX_CAMERA_SAFE_HALF_EXTENT\s*-\s*"
            r"ANNEX_CAMERA_BOOM_DISTANCE",
        ):
            self.assertRegex(self.render, expression)
        self.assertIn("int8_t annex_camera_boom_side;", self.header)

        annex = compact(self.annex)
        for token in (
            "{ Q8(-44), Q8(20), Q8(-40), Q8(24), "
            "N64GAME_ANNEX_ATRIUM, true }",
            "{ Q8(-116), Q8(-52), Q8(-40), Q8(24), "
            "N64GAME_ANNEX_SIMULATION, true }",
            "{ Q8(28), Q8(92), Q8(-20), Q8(44), "
            "N64GAME_ANNEX_WORKSHOP, true }",
            "{ Q8(84), Q8(148), Q8(36), Q8(100), "
            "N64GAME_ANNEX_OVERLOOK, true }",
            "{ Q8(-54), Q8(-42), Q8(-20), Q8(20), "
            "N64GAME_ANNEX_SIMULATION, false }",
            "{ Q8(18), Q8(30), Q8(0), Q8(24), "
            "N64GAME_ANNEX_WORKSHOP, false }",
            "{ Q8(82), Q8(94), Q8(34), Q8(56), "
            "N64GAME_ANNEX_OVERLOOK, false }",
            "[N64GAME_ANNEX_ATRIUM] = { Q8(-12), Q8(-8) }",
            "[N64GAME_ANNEX_SIMULATION] = { Q8(-84), Q8(-8) }",
            "[N64GAME_ANNEX_WORKSHOP] = { Q8(60), Q8(12) }",
            "[N64GAME_ANNEX_OVERLOOK] = { Q8(116), Q8(68) }",
        ):
            self.assertIn(token, annex)
        render = compact(self.render)
        for token in (
            "[N64GAME_ANNEX_ATRIUM] = 0.0f",
            "[N64GAME_ANNEX_SIMULATION] = 1.5707963f",
            "[N64GAME_ANNEX_WORKSHOP] = -1.5707963f",
            "[N64GAME_ANNEX_OVERLOOK] = 3.1415927f",
        ):
            self.assertIn(token, render)

        local_position = compact(
            function_body(self.render, "annex_camera_player_local_position")
        )
        self.assertIn("n64game_annex_safe_anchor(sector", local_position)
        self.assertIn(
            "*player_local_x = cosine * delta_x + sine * delta_z;",
            local_position,
        )
        self.assertIn(
            "*player_local_z = -sine * delta_x + cosine * delta_z;",
            local_position,
        )

        clamp = compact(function_body(self.render, "clamp_annex_camera_local"))
        self.assertIn("value < -(float)ANNEX_CAMERA_SAFE_HALF_EXTENT", clamp)
        self.assertIn("value > (float)ANNEX_CAMERA_SAFE_HALF_EXTENT", clamp)
        self.assertIn("return -(float)ANNEX_CAMERA_SAFE_HALF_EXTENT;", clamp)
        self.assertIn("return (float)ANNEX_CAMERA_SAFE_HALF_EXTENT;", clamp)

        rail = compact(function_body(self.render, "update_annex_camera_rail"))
        for token in (
            "renderer->annex_camera_boom_side = "
            "player_local_z > 0.0f ? -1 : 1;",
            "next_side > 0 && player_local_z > "
            "(float)ANNEX_CAMERA_SWITCH_LOCAL_Z",
            "next_side = -1;",
            "next_side < 0 && player_local_z < "
            "-(float)ANNEX_CAMERA_SWITCH_LOCAL_Z",
            "next_side = 1;",
            "next_side != renderer->annex_camera_boom_side",
        ):
            self.assertIn(token, rail)
        self.assertEqual(
            rail.count(
                "renderer->annex_camera_fade_ticks = "
                "ANNEX_CAMERA_FADE_FRAMES;"
            ),
            2,
        )

        draw = compact(function_body(self.render, "draw_annex"))
        for token in (
            "renderer->annex_camera_boom_side == -1 || "
            "renderer->annex_camera_boom_side == 1",
            "renderer->annex_camera_boom_side * "
            "ANNEX_CAMERA_BOOM_DISTANCE",
            "-renderer->annex_camera_boom_side * ANNEX_CAMERA_LOOK_LEAD",
            "camera_local_x = clamp_annex_camera_local(player_local_x)",
            "camera_local_z = clamp_annex_camera_local( "
            "player_local_z + camera_boom_z )",
            "camera_offset_local_x = camera_local_x - player_local_x",
            "camera_offset_local_z = camera_local_z - player_local_z",
            "rotate_annex_local_offset( yaw, camera_offset_local_x, "
            "camera_offset_local_z",
            "rotate_annex_local_offset(yaw, 0.0f, target_lead_z",
            "{{player_x + camera_x, -4.0f, player_z + camera_z}}",
            "{{player_x + target_x, -12.0f, player_z + target_z}}",
        ):
            self.assertIn(token, draw)
        projection = compact(function_body(self.render, "begin_world_render"))
        self.assertIn(
            "T3D_DEG_TO_RAD(68.0f), 8.0f, 300.0f",
            projection,
        )

    def test_strict_two_unit_hysteresis_switches_with_eight_frame_fade(self) -> None:
        self.assertEqual(SWITCH_LOCAL_Z, 2.0)
        self.assertEqual(update_boom_side(1, 2.0), (1, 0))
        self.assertEqual(update_boom_side(1, math.nextafter(2.0, math.inf)), (-1, 8))
        self.assertEqual(update_boom_side(-1, -2.0), (-1, 0))
        self.assertEqual(
            update_boom_side(-1, math.nextafter(-2.0, -math.inf)),
            (1, 8),
        )
        for side in (-1, 1):
            for local_z in (-2.0, 0.0, 2.0):
                selected, fade_frames = update_boom_side(side, local_z)
                eye, _ = rail_geometry(0.0, local_z, selected)
                self.assertGreaterEqual(eye[2], -SAFE_HALF_EXTENT)
                self.assertLessEqual(eye[2], SAFE_HALF_EXTENT)
                self.assertEqual(fade_frames, 0)

    def test_all_primary_room_boundary_extrema_keep_eye_inside_rail(self) -> None:
        samples = 0
        for room_name, room in PRIMARY_ROOMS.items():
            min_x, max_x, min_z, max_z = room["bounds"]
            for world_x in (min_x, max_x):
                for world_z in (min_z, max_z):
                    local_x, local_z = world_to_sector_local(
                        world_x,
                        world_z,
                        room["anchor"],
                        room["yaw"],
                    )
                    self.assertAlmostEqual(abs(local_x), 32.0, places=5)
                    self.assertAlmostEqual(abs(local_z), 32.0, places=5)
                    self.assert_safe_view(
                        f"{room_name} boundary ({world_x}, {world_z})",
                        local_x,
                        local_z,
                    )
                    samples += 1
        self.assertEqual(samples, 16)

    def test_every_connector_boundary_stays_inside_both_local_axes(self) -> None:
        samples = 0
        for connector_name, connector in CONNECTORS.items():
            room = PRIMARY_ROOMS[connector["sector"]]
            min_x, max_x, min_z, max_z = connector["bounds"]
            for world_x in (min_x, max_x):
                for world_z in (min_z, max_z):
                    local_x, local_z = world_to_sector_local(
                        world_x,
                        world_z,
                        room["anchor"],
                        room["yaw"],
                    )
                    self.assert_safe_view(
                        f"{connector_name} boundary ({world_x}, {world_z})",
                        local_x,
                        local_z,
                    )
                    samples += 1
        self.assertEqual(samples, 12)

    def test_all_eight_interactions_keep_eye_inside_rail_and_clear_near_plane(self) -> None:
        self.assertEqual(len(INTERACTIONS), 8)
        for interaction, (room_name, world_x, world_z) in INTERACTIONS.items():
            room = PRIMARY_ROOMS[room_name]
            min_x, max_x, min_z, max_z = room["bounds"]
            self.assertGreaterEqual(world_x, min_x, msg=interaction)
            self.assertLessEqual(world_x, max_x, msg=interaction)
            self.assertGreaterEqual(world_z, min_z, msg=interaction)
            self.assertLessEqual(world_z, max_z, msg=interaction)
            local_x, local_z = world_to_sector_local(
                world_x,
                world_z,
                room["anchor"],
                room["yaw"],
            )
            self.assert_safe_view(interaction, local_x, local_z)


if __name__ == "__main__":
    unittest.main()
