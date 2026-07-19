#!/usr/bin/env python3
"""Deterministically author the first Quarrune Blender source candidate.

Run with the pinned Blender build:

    "$HOME/Applications/Blender-4.5.11.app/Contents/MacOS/Blender" \
      --background --factory-startup --python tools/n64game_quarrune_author.py

The ignored output includes the unchanged hero, a distinct distance model, an
animation-only rig, and role-separated GLBs.  This is an authoring candidate
only.  It deliberately does not write canonical ``assets-src`` or review/gate
material and does not invoke the Gate-5 exporter.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "build" / "generated" / "quarrune_authoring"
BLEND_PATH = OUTPUT_DIR / "quarrune_source_candidate.blend"
MODEL_BLEND_PATH = OUTPUT_DIR / "quarrune_model_source_candidate.blend"
ANIMATION_BLEND_PATH = OUTPUT_DIR / "quarrune_animation_source_candidate.blend"
RENDER_PATH = OUTPUT_DIR / "quarrune_neutral.png"
DISTANCE_RENDER_PATH = OUTPUT_DIR / "quarrune_distance_neutral.png"
HERO_GLB_PATH = OUTPUT_DIR / "quarrune_hero.glb"
DISTANCE_GLB_PATH = OUTPUT_DIR / "quarrune_distance.glb"
ANIMATION_GLB_PATH = OUTPUT_DIR / "anm_echo_quarrune.glb"

ACTION_ORDER = (
    "brace_relay",
    "entrance",
    "hit",
    "horizon_break",
    "idle_a",
    "idle_b",
    "knockout",
    "reposition",
    "ridge_ram",
)

FAST64_ACCENT_TEXTURE_PATH = (
    "filesystem/echo/echo.quarrune/tex_quarrune_accent_ci4_32x32.png"
)
FAST64_BODY_TOP_REFERENCE = "0x51554230"
FAST64_BODY_BOTTOM_REFERENCE = "0x51554231"

BONE_SPECS = (
    ("root", None, (0.00, 0.00, 0.02), (0.00, 0.00, 0.22)),
    ("body", "root", (0.00, 0.00, 0.34), (0.00, 0.00, 0.72)),
    ("resonator", "body", (-0.34, 0.00, 0.68), (-0.70, 0.00, 0.68)),
    ("horn_l", "resonator", (-0.60, 0.10, 0.73), (-0.64, 0.24, 1.14)),
    ("horn_r", "resonator", (-0.60, -0.10, 0.73), (-0.64, -0.24, 1.14)),
    ("tail", "body", (0.48, 0.00, 0.61), (0.82, 0.00, 0.57)),
    ("leg_fl_hip", "body", (-0.43, 0.25, 0.58), (-0.47, 0.33, 0.35)),
    ("leg_fl_foot", "leg_fl_hip", (-0.47, 0.33, 0.35), (-0.48, 0.36, 0.10)),
    ("leg_ml_hip", "body", (0.00, 0.29, 0.57), (0.00, 0.36, 0.34)),
    ("leg_ml_foot", "leg_ml_hip", (0.00, 0.36, 0.34), (0.00, 0.39, 0.10)),
    ("leg_rl_hip", "body", (0.43, 0.25, 0.57), (0.48, 0.33, 0.34)),
    ("leg_rl_foot", "leg_rl_hip", (0.48, 0.33, 0.34), (0.48, 0.36, 0.10)),
    ("leg_fr_hip", "body", (-0.43, -0.25, 0.58), (-0.47, -0.33, 0.35)),
    ("leg_fr_foot", "leg_fr_hip", (-0.47, -0.33, 0.35), (-0.48, -0.36, 0.10)),
    ("leg_mr_hip", "body", (0.00, -0.29, 0.57), (0.00, -0.36, 0.34)),
    ("leg_mr_foot", "leg_mr_hip", (0.00, -0.36, 0.34), (0.00, -0.39, 0.10)),
    ("leg_rr_hip", "body", (0.43, -0.25, 0.57), (0.48, -0.33, 0.34)),
    ("leg_rr_foot", "leg_rr_hip", (0.48, -0.33, 0.34), (0.48, -0.36, 0.10)),
    ("brace_core", "body", (-0.03, 0.00, 0.69), (-0.03, 0.00, 0.93)),
    ("keel", "resonator", (-0.59, 0.00, 0.56), (-0.67, 0.00, 0.35)),
)


class MeshBuilder:
    def __init__(self) -> None:
        self.verts: list[tuple[float, float, float]] = []
        self.faces: list[tuple[int, int, int]] = []
        self.materials: list[int] = []
        self.bones: list[str] = []
        self.smooth: list[bool] = []

    def add_vertex(self, value: Vector | tuple[float, float, float], bone: str) -> int:
        vec = Vector(value)
        self.verts.append((vec.x, vec.y, vec.z))
        self.bones.append(bone)
        return len(self.verts) - 1

    def tri(self, a: int, b: int, c: int, material: int, smooth: bool = False) -> None:
        self.faces.append((a, b, c))
        self.materials.append(material)
        self.smooth.append(smooth)

    def quad(self, a: int, b: int, c: int, d: int, material: int, smooth: bool = False) -> None:
        self.tri(a, b, c, material, smooth)
        self.tri(a, c, d, material, smooth)

    def cylinder(
        self,
        start: tuple[float, float, float],
        end: tuple[float, float, float],
        radius_a: float,
        radius_b: float,
        sides: int,
        material: int,
        bone: str,
        phase: float = 0.0,
    ) -> None:
        p0, p1 = Vector(start), Vector(end)
        axis = (p1 - p0).normalized()
        reference = Vector((0.0, 0.0, 1.0))
        if abs(axis.dot(reference)) > 0.92:
            reference = Vector((0.0, 1.0, 0.0))
        u = axis.cross(reference).normalized()
        v = axis.cross(u).normalized()
        ring_a, ring_b = [], []
        for index in range(sides):
            angle = phase + 2.0 * math.pi * index / sides
            radial = math.cos(angle) * u + math.sin(angle) * v
            ring_a.append(self.add_vertex(p0 + radial * radius_a, bone))
            ring_b.append(self.add_vertex(p1 + radial * radius_b, bone))
        ca = self.add_vertex(p0, bone)
        cb = self.add_vertex(p1, bone)
        for index in range(sides):
            nxt = (index + 1) % sides
            self.quad(ring_a[index], ring_a[nxt], ring_b[nxt], ring_b[index], material, True)
            self.tri(ca, ring_a[nxt], ring_a[index], material)
            self.tri(cb, ring_b[index], ring_b[nxt], material)

    def box(
        self,
        center: tuple[float, float, float],
        size: tuple[float, float, float],
        material: int,
        bone: str,
        shear_x: float = 0.0,
    ) -> None:
        cx, cy, cz = center
        sx, sy, sz = (value * 0.5 for value in size)
        coords = []
        for x, y, z in (
            (-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
            (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz),
        ):
            coords.append(self.add_vertex((cx + x + shear_x * z, cy + y, cz + z), bone))
        for a, b, c, d in (
            (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
            (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
        ):
            self.quad(coords[a], coords[b], coords[c], coords[d], material)

    def ellipsoid_body(self) -> None:
        rings = (
            (-0.60, 0.20, 0.22, 0.67),
            (-0.49, 0.34, 0.33, 0.69),
            (-0.28, 0.39, 0.37, 0.70),
            (0.00, 0.40, 0.38, 0.70),
            (0.28, 0.35, 0.34, 0.69),
            (0.49, 0.27, 0.28, 0.66),
            (0.62, 0.15, 0.18, 0.62),
        )
        sides = 12
        built: list[list[int]] = []
        for x, ry, rz, zc in rings:
            ring = []
            for index in range(sides):
                angle = 2.0 * math.pi * index / sides
                ring.append(self.add_vertex((x, math.cos(angle) * ry, zc + math.sin(angle) * rz), "body"))
            built.append(ring)
        for ring_index in range(len(built) - 1):
            for index in range(sides):
                nxt = (index + 1) % sides
                self.quad(
                    built[ring_index][index], built[ring_index + 1][index],
                    built[ring_index + 1][nxt], built[ring_index][nxt], 2, True,
                )
        front = self.add_vertex((-0.62, 0.0, 0.67), "body")
        rear = self.add_vertex((0.64, 0.0, 0.62), "body")
        for index in range(sides):
            nxt = (index + 1) % sides
            self.tri(front, built[0][index], built[0][nxt], 2, True)
            self.tri(rear, built[-1][nxt], built[-1][index], 2, True)

    def distance_ellipsoid_body(self) -> None:
        """Build the silhouette-retaining eight-sided distance body."""
        rings = (
            (-0.60, 0.20, 0.22, 0.67),
            (-0.42, 0.35, 0.34, 0.70),
            (-0.14, 0.40, 0.38, 0.70),
            (0.16, 0.38, 0.36, 0.70),
            (0.43, 0.30, 0.30, 0.67),
            (0.62, 0.15, 0.18, 0.62),
        )
        sides = 8
        built: list[list[int]] = []
        for x, ry, rz, zc in rings:
            ring = []
            for index in range(sides):
                angle = 2.0 * math.pi * index / sides
                ring.append(self.add_vertex((x, math.cos(angle) * ry, zc + math.sin(angle) * rz), "body"))
            built.append(ring)
        for ring_index in range(len(built) - 1):
            for index in range(sides):
                nxt = (index + 1) % sides
                self.quad(
                    built[ring_index][index], built[ring_index + 1][index],
                    built[ring_index + 1][nxt], built[ring_index][nxt], 2, True,
                )
        front = self.add_vertex((-0.62, 0.0, 0.67), "body")
        rear = self.add_vertex((0.64, 0.0, 0.62), "body")
        for index in range(sides):
            nxt = (index + 1) % sides
            self.tri(front, built[0][index], built[0][nxt], 2, True)
            self.tri(rear, built[-1][nxt], built[-1][index], 2, True)

    def annulus_x(self) -> None:
        x_front, x_back = -0.735, -0.615
        outer, inner, sides = 0.335, 0.235, 12
        rings: dict[str, list[int]] = {name: [] for name in ("of", "ob", "if", "ib")}
        for index in range(sides):
            angle = 2.0 * math.pi * index / sides
            y, z = math.cos(angle), math.sin(angle)
            rings["of"].append(self.add_vertex((x_front, y * outer, 0.69 + z * outer), "resonator"))
            rings["ob"].append(self.add_vertex((x_back, y * outer, 0.69 + z * outer), "resonator"))
            rings["if"].append(self.add_vertex((x_front, y * inner, 0.69 + z * inner), "resonator"))
            rings["ib"].append(self.add_vertex((x_back, y * inner, 0.69 + z * inner), "resonator"))
        for index in range(sides):
            nxt = (index + 1) % sides
            self.quad(rings["of"][index], rings["ob"][index], rings["ob"][nxt], rings["of"][nxt], 1)
            self.quad(rings["if"][nxt], rings["ib"][nxt], rings["ib"][index], rings["if"][index], 2)
            self.quad(rings["of"][index], rings["of"][nxt], rings["if"][nxt], rings["if"][index], 1)
            self.quad(rings["ob"][nxt], rings["ob"][index], rings["ib"][index], rings["ib"][nxt], 1)
        # Tapered, visibly hollow cavity ending in a dark polygonal diaphragm.
        rear_ring = []
        for index in range(sides):
            angle = 2.0 * math.pi * index / sides
            rear_ring.append(self.add_vertex((-0.48, math.cos(angle) * 0.115, 0.69 + math.sin(angle) * 0.115), "resonator"))
        diaphragm = self.add_vertex((-0.465, 0.0, 0.69), "resonator")
        for index in range(sides):
            nxt = (index + 1) % sides
            self.quad(rings["ib"][index], rings["ib"][nxt], rear_ring[nxt], rear_ring[index], 2, True)
            self.tri(diaphragm, rear_ring[index], rear_ring[nxt], 2)

    def distance_annulus_x(self) -> None:
        """Keep the open tuning cavity at distance with fewer radial segments."""
        x_front, x_back = -0.735, -0.615
        outer, inner, sides = 0.335, 0.235, 8
        rings: dict[str, list[int]] = {name: [] for name in ("of", "ob", "if", "ib")}
        for index in range(sides):
            angle = 2.0 * math.pi * index / sides
            y, z = math.cos(angle), math.sin(angle)
            rings["of"].append(self.add_vertex((x_front, y * outer, 0.69 + z * outer), "resonator"))
            rings["ob"].append(self.add_vertex((x_back, y * outer, 0.69 + z * outer), "resonator"))
            rings["if"].append(self.add_vertex((x_front, y * inner, 0.69 + z * inner), "resonator"))
            rings["ib"].append(self.add_vertex((x_back, y * inner, 0.69 + z * inner), "resonator"))
        for index in range(sides):
            nxt = (index + 1) % sides
            self.quad(rings["of"][index], rings["ob"][index], rings["ob"][nxt], rings["of"][nxt], 1)
            self.quad(rings["if"][nxt], rings["ib"][nxt], rings["ib"][index], rings["if"][index], 2)
            self.quad(rings["of"][index], rings["of"][nxt], rings["if"][nxt], rings["if"][index], 1)
            self.quad(rings["ob"][nxt], rings["ob"][index], rings["ib"][index], rings["ib"][nxt], 1)
        rear_ring = []
        for index in range(sides):
            angle = 2.0 * math.pi * index / sides
            rear_ring.append(self.add_vertex((-0.48, math.cos(angle) * 0.115, 0.69 + math.sin(angle) * 0.115), "resonator"))
        diaphragm = self.add_vertex((-0.465, 0.0, 0.69), "resonator")
        for index in range(sides):
            nxt = (index + 1) % sides
            self.quad(rings["ib"][index], rings["ib"][nxt], rear_ring[nxt], rear_ring[index], 2, True)
            self.tri(diaphragm, rear_ring[index], rear_ring[nxt], 2)


def build_quarrune_mesh() -> tuple[bpy.types.Object, MeshBuilder]:
    builder = MeshBuilder()
    builder.ellipsoid_body()
    builder.annulus_x()

    # The two asymmetric open triangles and their inner braces make the horn
    # lattice readable as negative space instead of a solid helmet or mammal ear.
    horn_sets = (
        ("horn_l", ((-0.66, 0.12, 0.88), (-0.64, 0.25, 1.19), (-0.61, 0.02, 1.00))),
        ("horn_r", ((-0.66, -0.12, 0.88), (-0.64, -0.25, 1.19), (-0.61, -0.02, 1.00))),
    )
    for bone, points in horn_sets:
        for start, end in ((points[0], points[1]), (points[1], points[2]), (points[2], points[0])):
            builder.cylinder(start, end, 0.033, 0.030, 4, 1, bone, math.pi / 4.0)
        midpoint = tuple((points[0][axis] + points[1][axis]) * 0.5 for axis in range(3))
        builder.cylinder(points[2], midpoint, 0.020, 0.020, 4, 1, bone, math.pi / 4.0)

    # Overlapping ceramic armor bands deliberately expose the dark resonator
    # between them.  Their taper and offset follow the concept turnaround.
    plates = (
        ((-0.39, 0.00, 1.000), (0.26, 0.47, 0.075), -0.08, "brace_core"),
        ((-0.12, 0.00, 1.045), (0.28, 0.50, 0.075), -0.04, "brace_core"),
        ((0.16, 0.00, 1.015), (0.29, 0.46, 0.075), 0.02, "body"),
        ((0.41, 0.00, 0.925), (0.25, 0.37, 0.070), 0.07, "body"),
        ((-0.22, 0.333, 0.760), (0.40, 0.065, 0.24), -0.04, "body"),
        ((0.22, 0.310, 0.735), (0.38, 0.060, 0.22), 0.04, "body"),
        ((-0.22, -0.333, 0.760), (0.40, 0.065, 0.24), -0.04, "body"),
        ((0.22, -0.310, 0.735), (0.38, 0.060, 0.22), 0.04, "body"),
        ((-0.55, 0.00, 0.455), (0.15, 0.20, 0.26), -0.12, "keel"),
        ((0.54, 0.00, 0.675), (0.16, 0.24, 0.18), 0.08, "body"),
    )
    for center, size, shear, bone in plates:
        builder.box(center, size, 0, bone, shear)

    # Six deliberately separated two-joint supports and broad wedge footpads.
    leg_data = (
        (-0.48, 0.34, "leg_fl_hip", "leg_fl_foot"),
        (0.00, 0.37, "leg_ml_hip", "leg_ml_foot"),
        (0.48, 0.34, "leg_rl_hip", "leg_rl_foot"),
        (-0.48, -0.34, "leg_fr_hip", "leg_fr_foot"),
        (0.00, -0.37, "leg_mr_hip", "leg_mr_foot"),
        (0.48, -0.34, "leg_rr_hip", "leg_rr_foot"),
    )
    for x, y, hip_bone, foot_bone in leg_data:
        side = 1.0 if y > 0.0 else -1.0
        attach = (x * 0.92, y * 0.72, 0.63)
        knee = (x, y * 0.94, 0.38)
        ankle = (x, y, 0.15)
        builder.cylinder(attach, knee, 0.105, 0.085, 6, 2, hip_bone)
        builder.cylinder(knee, ankle, 0.090, 0.075, 6, 0, foot_bone, math.pi / 6.0)
        builder.cylinder((x, y, 0.19), (x, y + side * 0.012, 0.105), 0.080, 0.090, 6, 2, foot_bone)
        builder.box((x, y + side * 0.025, 0.068), (0.29, 0.12, 0.105), 0, foot_bone, 0.20)

    # Short counterweight tail with cobalt collar; total body length is 1.65 m.
    builder.cylinder((0.56, 0.0, 0.63), (0.72, 0.0, 0.59), 0.105, 0.080, 6, 2, "tail")
    builder.cylinder((0.72, 0.0, 0.59), (0.835, 0.0, 0.575), 0.095, 0.090, 6, 0, "tail")
    builder.cylinder((0.835, 0.0, 0.575), (0.915, 0.0, 0.57), 0.095, 0.075, 6, 1, "tail")

    mesh = bpy.data.meshes.new("Quarrune_Hero_SourceCandidate")
    mesh.from_pydata(builder.verts, [], builder.faces)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new("Quarrune_Hero", mesh)
    bpy.context.collection.objects.link(obj)
    for polygon, material, smooth in zip(mesh.polygons, builder.materials, builder.smooth):
        polygon.material_index = material
        polygon.use_smooth = smooth

    # Every loop receives authored, non-collapsed normalized UV coordinates.
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            u = max(0.0, min(1.0, (vertex.x + 0.75) / 1.67))
            v = max(0.0, min(1.0, vertex.z / 1.24))
            uv_layer.data[loop_index].uv = (u, v)

    obj["production_id"] = "echo.quarrune"
    obj["source_status"] = "candidate_not_gate_evidence"
    obj["shoulder_height_m"] = 0.95
    obj["body_length_m"] = 1.65
    obj["footprint_length_m"] = 1.25
    obj["footprint_width_m"] = 0.80
    obj["triangle_count"] = len(builder.faces)
    obj["one_influence_rigid_weights"] = True
    obj["concept_sha256"] = "5d113e68848f3a2f5ac3735111a96acf625c9db47fe8545f3d71a9fb46f9beab"
    obj["design_note"] = "six-legged ceramic resonator; open cobalt horn lattice; hollow tuning cavity"
    return obj, builder


def build_quarrune_distance_mesh() -> tuple[bpy.types.Object, MeshBuilder]:
    """Build a distinct distance mesh that preserves the hero's gameplay read."""
    builder = MeshBuilder()
    builder.distance_ellipsoid_body()
    builder.distance_annulus_x()

    horn_sets = (
        ("horn_l", ((-0.66, 0.12, 0.88), (-0.64, 0.25, 1.19), (-0.61, 0.02, 1.00))),
        ("horn_r", ((-0.66, -0.12, 0.88), (-0.64, -0.25, 1.19), (-0.61, -0.02, 1.00))),
    )
    for bone, points in horn_sets:
        segments = [(points[0], points[1]), (points[1], points[2]), (points[2], points[0])]
        midpoint = tuple((points[0][axis] + points[1][axis]) * 0.5 for axis in range(3))
        segments.append((points[2], midpoint))
        for start, end in segments:
            builder.cylinder(start, end, 0.036, 0.031, 3, 1, bone, math.pi / 6.0)

    # Six broad plates retain the layered ceramic silhouette without spending
    # distance-model triangles on the hero mesh's smaller overlapping facets.
    plates = (
        ((-0.39, 0.00, 1.000), (0.26, 0.47, 0.075), -0.08, "brace_core"),
        ((-0.12, 0.00, 1.045), (0.28, 0.50, 0.075), -0.04, "brace_core"),
        ((0.16, 0.00, 1.015), (0.29, 0.46, 0.075), 0.02, "body"),
        ((0.41, 0.00, 0.925), (0.25, 0.37, 0.070), 0.07, "body"),
        ((-0.18, 0.333, 0.750), (0.55, 0.065, 0.24), -0.02, "body"),
        ((-0.18, -0.333, 0.750), (0.55, 0.065, 0.24), -0.02, "body"),
    )
    for center, size, shear, bone in plates:
        builder.box(center, size, 0, bone, shear)

    leg_data = (
        (-0.48, 0.34, "leg_fl_hip", "leg_fl_foot"),
        (0.00, 0.37, "leg_ml_hip", "leg_ml_foot"),
        (0.48, 0.34, "leg_rl_hip", "leg_rl_foot"),
        (-0.48, -0.34, "leg_fr_hip", "leg_fr_foot"),
        (0.00, -0.37, "leg_mr_hip", "leg_mr_foot"),
        (0.48, -0.34, "leg_rr_hip", "leg_rr_foot"),
    )
    for x, y, hip_bone, foot_bone in leg_data:
        side = 1.0 if y > 0.0 else -1.0
        attach = (x * 0.92, y * 0.72, 0.63)
        knee = (x, y * 0.94, 0.38)
        ankle = (x, y, 0.13)
        builder.cylinder(attach, knee, 0.115, 0.090, 3, 2, hip_bone, math.pi / 6.0)
        builder.cylinder(knee, ankle, 0.095, 0.078, 3, 0, foot_bone, math.pi / 6.0)
        builder.box((x, y + side * 0.025, 0.068), (0.29, 0.12, 0.105), 0, foot_bone, 0.20)

    builder.cylinder((0.56, 0.0, 0.63), (0.76, 0.0, 0.585), 0.110, 0.090, 3, 2, "tail", math.pi / 6.0)
    builder.cylinder((0.76, 0.0, 0.585), (0.915, 0.0, 0.57), 0.100, 0.075, 3, 1, "tail", math.pi / 6.0)

    mesh = bpy.data.meshes.new("Quarrune_Distance_SourceCandidate")
    mesh.from_pydata(builder.verts, [], builder.faces)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new("Quarrune_Distance", mesh)
    bpy.context.collection.objects.link(obj)
    for polygon, material, smooth in zip(mesh.polygons, builder.materials, builder.smooth):
        polygon.material_index = material
        polygon.use_smooth = smooth

    uv_layer = mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            u = max(0.0, min(1.0, (vertex.x + 0.75) / 1.67))
            v = max(0.0, min(1.0, vertex.z / 1.24))
            uv_layer.data[loop_index].uv = (u, v)

    obj["production_id"] = "echo.quarrune"
    obj["model_role"] = "distance"
    obj["source_status"] = "candidate_not_gate_evidence"
    obj["triangle_count"] = len(builder.faces)
    obj["one_influence_rigid_weights"] = True
    obj["design_note"] = "distance-preserved cavity, cobalt lattice, six-leg silhouette"
    return obj, builder


def fast64_axis(high: int) -> dict[str, float | int]:
    return {
        "low": 0.0,
        "high": float(high),
        "mask": 0,
        "shift": 0,
        "mirror": 0,
        "clamp": 1,
    }


def fast64_dynamic_body_texture(reference: str) -> dict[str, object]:
    return {
        "use_tex_reference": 1,
        "tex_reference": reference,
        "tex_reference_size": [64, 32],
        "S": fast64_axis(63),
        "T": fast64_axis(31),
    }


def fast64_accent_texture() -> dict[str, object]:
    return {
        "use_tex_reference": 0,
        "tex": {"name": FAST64_ACCENT_TEXTURE_PATH},
        "S": fast64_axis(31),
        "T": fast64_axis(31),
    }


def fast64_material_payload(tex0: dict[str, object]) -> dict[str, object]:
    combiner = {
        "A": 1,
        "B": 8,
        "C": 4,
        "D": 7,
        "A_alpha": 1,
        "B_alpha": 7,
        "C_alpha": 4,
        "D_alpha": 7,
    }
    return {
        "combiner1": combiner,
        "combiner2": dict(combiner),
        "set_blend": 0,
        "blend_color": [0.0, 0.0, 0.0, 0.0],
        "rdp_settings": {
            "g_mdsft_cycletype": 0,
            "g_cull_back": 0,
            "g_cull_front": 0,
            "g_fog": 0,
            "g_mdsft_text_filt": 0,
            "g_tex_gen": 0,
            "set_rendermode": 0,
        },
        "draw_layer": {"oot": 0, "sm64": 1},
        "tex0": tex0,
    }


def expected_fast64_materials() -> dict[str, dict[str, object]]:
    return {
        "QR_Ceramic": fast64_material_payload(
            fast64_dynamic_body_texture(FAST64_BODY_TOP_REFERENCE)
        ),
        "QR_CobaltLattice": fast64_material_payload(fast64_accent_texture()),
        "QR_Resonator": fast64_material_payload(
            fast64_dynamic_body_texture(FAST64_BODY_BOTTOM_REFERENCE)
        ),
    }


def make_material(
    name: str,
    color: tuple[float, float, float, float],
    roughness: float,
    metallic: float,
    *,
    fast64_tex0: dict[str, object] | None = None,
) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if fast64_tex0 is not None:
        # Blender's glTF exporter writes material custom properties under
        # ``extras``. This is the exact Fast64-shaped payload consumed by the
        # pinned Tiny3D importer; the two body regions intentionally stay
        # pathless dynamic references while the cobalt material resolves the
        # deterministic accent PNG below the exporter's filesystem/ root.
        material["f3d_mat"] = fast64_material_payload(fast64_tex0)
    return material


def create_armature() -> bpy.types.Object:
    armature = bpy.data.armatures.new("Quarrune_Rig")
    rig = bpy.data.objects.new("Quarrune_Rig", armature)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    created = {}
    for name, parent, head, tail in BONE_SPECS:
        bone = armature.edit_bones.new(name)
        bone.head = head
        bone.tail = tail
        bone.use_deform = True
        if parent:
            bone.parent = created[parent]
        created[name] = bone
    bpy.ops.object.mode_set(mode="POSE")
    for pose_bone in rig.pose.bones:
        pose_bone.rotation_mode = "XYZ"
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.select_set(False)
    rig["deform_bone_count"] = len(BONE_SPECS)
    rig["action_order"] = json.dumps(ACTION_ORDER)
    return rig


def bind_rigid(obj: bpy.types.Object, builder: MeshBuilder, rig: bpy.types.Object) -> None:
    groups = {name: obj.vertex_groups.new(name=name) for name, *_ in BONE_SPECS}
    by_bone: dict[str, list[int]] = {name: [] for name in groups}
    for vertex_index, bone_name in enumerate(builder.bones):
        by_bone[bone_name].append(vertex_index)
    for bone_name, indices in by_bone.items():
        if indices:
            groups[bone_name].add(indices, 1.0, "REPLACE")
    modifier = obj.modifiers.new("Quarrune_Rigid_Armature", "ARMATURE")
    modifier.object = rig
    obj.parent = rig


def reset_pose(rig: bpy.types.Object) -> None:
    for bone in rig.pose.bones:
        bone.location = (0.0, 0.0, 0.0)
        bone.rotation_euler = (0.0, 0.0, 0.0)
        bone.scale = (1.0, 1.0, 1.0)


def key(rig: bpy.types.Object, bone_name: str, frame: int, *, location=None, rotation=None, scale=None) -> None:
    bone = rig.pose.bones[bone_name]
    if location is not None:
        bone.location = location
        bone.keyframe_insert("location", frame=frame, group=bone_name)
    if rotation is not None:
        bone.rotation_euler = rotation
        bone.keyframe_insert("rotation_euler", frame=frame, group=bone_name)
    if scale is not None:
        bone.scale = scale
        bone.keyframe_insert("scale", frame=frame, group=bone_name)


def create_actions(rig: bpy.types.Object) -> None:
    rig.animation_data_create()
    for ordinal, name in enumerate(ACTION_ORDER):
        reset_pose(rig)
        action = bpy.data.actions.new(name)
        action.use_fake_user = True
        action["stream_ordinal"] = ordinal
        rig.animation_data.action = action
        # Every performance owns a distinct silhouette-changing phrase.
        if name == "brace_relay":
            key(rig, "root", 1, location=(0, 0, 0)); key(rig, "root", 10, location=(0, 0, -0.07)); key(rig, "root", 24, location=(0, 0, 0))
            for bone in ("leg_fl_hip", "leg_ml_hip", "leg_rl_hip"):
                key(rig, bone, 10, rotation=(0.13, 0.0, -0.12))
            for bone in ("leg_fr_hip", "leg_mr_hip", "leg_rr_hip"):
                key(rig, bone, 10, rotation=(-0.13, 0.0, 0.12))
            key(rig, "brace_core", 1, scale=(1, 1, 1)); key(rig, "brace_core", 10, scale=(1.0, 1.18, 1.22)); key(rig, "brace_core", 24, scale=(1, 1, 1))
        elif name == "entrance":
            key(rig, "root", 1, location=(0.55, 0, 0.28), rotation=(0, -0.18, 0)); key(rig, "root", 14, location=(0.05, 0, 0.05), rotation=(0, 0.08, 0)); key(rig, "root", 28, location=(0, 0, 0), rotation=(0, 0, 0))
            key(rig, "horn_l", 1, rotation=(0, 0.18, 0)); key(rig, "horn_r", 1, rotation=(0, -0.18, 0))
        elif name == "hit":
            key(rig, "body", 1, rotation=(0, 0, 0)); key(rig, "body", 4, rotation=(0.05, 0.18, -0.32)); key(rig, "body", 12, rotation=(0, -0.04, 0.06)); key(rig, "body", 20, rotation=(0, 0, 0))
            key(rig, "resonator", 4, scale=(0.82, 1.08, 1.08)); key(rig, "resonator", 20, scale=(1, 1, 1))
        elif name == "horizon_break":
            key(rig, "root", 1, location=(0, 0, 0)); key(rig, "root", 16, location=(0, 0, 0.18)); key(rig, "root", 28, location=(-0.18, 0, -0.05)); key(rig, "root", 40, location=(0, 0, 0))
            key(rig, "horn_l", 16, rotation=(0, -0.28, 0.14)); key(rig, "horn_r", 16, rotation=(0, 0.28, -0.14)); key(rig, "resonator", 28, scale=(1.22, 1.18, 1.18)); key(rig, "resonator", 40, scale=(1, 1, 1))
        elif name == "idle_a":
            key(rig, "resonator", 1, scale=(1, 1, 1)); key(rig, "resonator", 16, scale=(1.0, 1.035, 1.035)); key(rig, "resonator", 32, scale=(1, 1, 1))
            key(rig, "brace_core", 1, scale=(1, 1, 1)); key(rig, "brace_core", 16, scale=(1.0, 1.02, 1.045)); key(rig, "brace_core", 32, scale=(1, 1, 1))
        elif name == "idle_b":
            key(rig, "body", 1, rotation=(0, 0, -0.04)); key(rig, "body", 18, rotation=(0, 0, 0.055)); key(rig, "body", 36, rotation=(0, 0, -0.04))
            key(rig, "tail", 1, rotation=(0, -0.10, 0)); key(rig, "tail", 18, rotation=(0, 0.12, 0)); key(rig, "tail", 36, rotation=(0, -0.10, 0))
        elif name == "knockout":
            key(rig, "root", 1, location=(0, 0, 0), rotation=(0, 0, 0)); key(rig, "root", 12, location=(0.08, 0, -0.24), rotation=(0.35, 0.10, 0.75)); key(rig, "root", 30, location=(0.12, 0, -0.31), rotation=(0.55, 0.12, 1.16))
            for bone in ("leg_fl_foot", "leg_fr_foot", "leg_rl_foot", "leg_rr_foot"):
                key(rig, bone, 30, rotation=(0.0, 0.65, 0.0))
        elif name == "reposition":
            key(rig, "root", 1, location=(-0.38, 0, 0)); key(rig, "root", 12, location=(0, 0, 0.05)); key(rig, "root", 24, location=(0.38, 0, 0)); key(rig, "root", 32, location=(0, 0, 0))
            key(rig, "leg_fl_foot", 8, rotation=(0, -0.55, 0)); key(rig, "leg_mr_foot", 16, rotation=(0, 0.55, 0)); key(rig, "leg_rl_foot", 24, rotation=(0, -0.55, 0))
        elif name == "ridge_ram":
            key(rig, "root", 1, location=(0.18, 0, 0)); key(rig, "root", 10, location=(0.38, 0, -0.08)); key(rig, "root", 18, location=(-0.48, 0, 0.03)); key(rig, "root", 30, location=(0, 0, 0))
            key(rig, "body", 10, rotation=(0, -0.20, 0)); key(rig, "body", 18, rotation=(0, 0.14, 0)); key(rig, "body", 30, rotation=(0, 0, 0))
            key(rig, "horn_l", 18, rotation=(0, -0.16, 0)); key(rig, "horn_r", 18, rotation=(0, 0.16, 0))
        for fcurve in action.fcurves:
            for point in fcurve.keyframe_points:
                point.interpolation = "BEZIER"
        action["performance_signature"] = f"quarrune-{ordinal + 1:02d}-{name}"
    rig.animation_data.action = bpy.data.actions["idle_a"]


def move_to_named_collection(obj: bpy.types.Object, name: str) -> None:
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    for current in tuple(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)


def export_selected_glb(
    path: Path,
    selected: tuple[bpy.types.Object, ...],
    rig: bpy.types.Object,
    *,
    animations: bool,
) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in selected:
        obj.hide_set(False)
        obj.hide_viewport = False
        obj.hide_render = False
        obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    result = bpy.ops.export_scene.gltf(
        filepath=str(path),
        check_existing=False,
        export_format="GLB",
        use_selection=True,
        export_extras=True,
        export_animations=animations,
        export_animation_mode="ACTIONS",
        export_merge_animation="ACTION",
        export_nla_strips=False,
        export_frame_range=True,
        export_frame_step=1,
        export_force_sampling=True,
        export_bake_animation=True,
        export_skins=True,
        export_def_bones=False,
        export_all_influences=False,
        export_influence_nb=4,
        export_morph=False,
        export_cameras=False,
        export_lights=False,
        export_materials="EXPORT",
        export_image_format="NONE",
        export_texcoords=True,
        export_normals=True,
        export_tangents=False,
        export_vertex_color="MATERIAL",
        export_yup=True,
        export_apply=False,
        export_shared_accessors=False,
        export_try_sparse_sk=False,
        export_try_omit_sparse_sk=False,
        export_draco_mesh_compression_enable=False,
        export_use_gltfpack=False,
        will_save_settings=False,
    )
    if "FINISHED" not in result or not path.is_file():
        raise RuntimeError(f"GLB export failed: {path}")


def canonicalize_and_inspect_glb(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    if len(payload) < 20 or payload[:4] != b"glTF" or struct.unpack_from("<I", payload, 4)[0] != 2:
        raise RuntimeError(f"not one GLB v2 file: {path}")
    if struct.unpack_from("<I", payload, 8)[0] != len(payload):
        raise RuntimeError(f"GLB length mismatch: {path}")
    chunks: list[tuple[int, bytes]] = []
    offset = 12
    while offset < len(payload):
        if offset + 8 > len(payload):
            raise RuntimeError(f"truncated GLB chunk header: {path}")
        length, kind = struct.unpack_from("<II", payload, offset)
        offset += 8
        if offset + length > len(payload):
            raise RuntimeError(f"truncated GLB chunk: {path}")
        chunks.append((kind, payload[offset:offset + length]))
        offset += length
    if not chunks or chunks[0][0] != 0x4E4F534A:
        raise RuntimeError(f"GLB has no leading JSON chunk: {path}")
    document = json.loads(chunks[0][1].rstrip(b" \t\r\n\0"))
    materials = document.get("materials", [])
    if materials:
        observed_materials = {
            material.get("name"): material.get("extras", {}).get("f3d_mat")
            for material in materials
            if isinstance(material, dict)
        }
        expected_materials = expected_fast64_materials()
        if observed_materials != expected_materials:
            raise RuntimeError(
                f"model GLB Fast64 material payload differs from the pinned Tiny3D contract: {path}"
            )
    if document.get("animations"):
        by_name = {animation.get("name"): animation for animation in document["animations"]}
        if set(by_name) == set(ACTION_ORDER) and len(by_name) == len(ACTION_ORDER):
            document["animations"] = [by_name[name] for name in ACTION_ORDER]
    json_bytes = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    json_bytes += b" " * ((-len(json_bytes)) % 4)
    chunks[0] = (0x4E4F534A, json_bytes)
    output = bytearray(b"glTF" + struct.pack("<II", 2, 0))
    for kind, data in chunks:
        output.extend(struct.pack("<II", len(data), kind))
        output.extend(data)
    struct.pack_into("<I", output, 8, len(output))
    path.write_bytes(output)

    joint_names: list[str] = []
    skins = document.get("skins", [])
    if len(skins) == 1:
        nodes = document.get("nodes", [])
        joint_names = [nodes[index].get("name", "") for index in skins[0].get("joints", [])]
    return {
        "path": str(path),
        "sha256": hashlib.sha256(output).hexdigest(),
        "bytes": len(output),
        "mesh_count": len(document.get("meshes", [])),
        "skin_count": len(skins),
        "bone_count": len(joint_names),
        "bone_names": joint_names,
        "material_count": len(document.get("materials", [])),
        "animation_names": [animation.get("name") for animation in document.get("animations", [])],
    }


def export_split_glbs(hero: bpy.types.Object, distance: bpy.types.Object, rig: bpy.types.Object) -> list[dict[str, object]]:
    export_selected_glb(HERO_GLB_PATH, (hero, rig), rig, animations=False)
    export_selected_glb(DISTANCE_GLB_PATH, (distance, rig), rig, animations=False)
    export_selected_glb(ANIMATION_GLB_PATH, (rig,), rig, animations=True)
    summaries = [
        canonicalize_and_inspect_glb(HERO_GLB_PATH),
        canonicalize_and_inspect_glb(DISTANCE_GLB_PATH),
        canonicalize_and_inspect_glb(ANIMATION_GLB_PATH),
    ]
    expected_bones = {name for name, *_ in BONE_SPECS}
    reference_bone_order = summaries[0]["bone_names"]
    for summary in summaries:
        if summary["skin_count"] != 1 or summary["bone_count"] != 20:
            raise RuntimeError(f"split GLB does not contain one exact 20-bone skin: {summary['path']}")
        if set(summary["bone_names"]) != expected_bones or len(set(summary["bone_names"])) != 20:
            raise RuntimeError(f"split GLB bone set differs: {summary['path']}")
        if summary["bone_names"] != reference_bone_order:
            raise RuntimeError(f"split GLB bone order is not identical: {summary['path']}")
    for summary in summaries[:2]:
        if summary["mesh_count"] != 1 or summary["material_count"] != 3 or summary["animation_names"]:
            raise RuntimeError(f"model GLB split contract failed: {summary['path']}")
    animation = summaries[2]
    if animation["mesh_count"] != 0 or animation["material_count"] != 0:
        raise RuntimeError("animation-only GLB unexpectedly contains model data")
    if animation["animation_names"] != list(ACTION_ORDER):
        raise RuntimeError(f"animation-only GLB action contract failed: {animation['animation_names']!r}")
    return summaries


def write_role_source_blends(
    hero: bpy.types.Object,
    distance: bpy.types.Object,
    rig: bpy.types.Object,
) -> dict[str, dict[str, object]]:
    """Write distinct model and animation candidate authorities.

    The library writer follows only dependencies of the explicit role scene.
    This lets the model source own hero+distance+rig without action datablocks,
    while the animation source owns rig+all nine actions without either mesh.
    """
    hero_collection = bpy.data.collections["hero_model"]
    distance_collection = bpy.data.collections["distance_model"]
    rig_collection = bpy.data.collections["rig"]

    model_scene = bpy.data.scenes.new("Quarrune_Model_Source")
    model_scene["source_status"] = "candidate_not_gate_evidence"
    model_scene["source_role"] = "echo.quarrune:model"
    for collection in (hero_collection, distance_collection, rig_collection):
        model_scene.collection.children.link(collection)

    animation_scene = bpy.data.scenes.new("Quarrune_Animation_Source")
    animation_scene["source_status"] = "candidate_not_gate_evidence"
    animation_scene["source_role"] = "anm.echo.quarrune:animation"
    animation_scene.collection.children.link(rig_collection)

    active_action = rig.animation_data.action
    rig.animation_data.action = None
    bpy.data.libraries.write(str(MODEL_BLEND_PATH), {model_scene}, fake_user=False, compress=False)
    rig.animation_data.action = active_action

    animation_blocks: set[bpy.types.ID] = {animation_scene}
    animation_blocks.update(bpy.data.actions)
    bpy.data.libraries.write(
        str(ANIMATION_BLEND_PATH), animation_blocks, fake_user=False, compress=False,
    )

    return {
        "model": {
            "path": str(MODEL_BLEND_PATH),
            "sha256": hashlib.sha256(MODEL_BLEND_PATH.read_bytes()).hexdigest(),
            "bytes": MODEL_BLEND_PATH.stat().st_size,
            "collections": ["hero_model", "distance_model", "rig"],
            "expected_meshes": [hero.name, distance.name],
            "expected_action_count": 0,
        },
        "animation": {
            "path": str(ANIMATION_BLEND_PATH),
            "sha256": hashlib.sha256(ANIMATION_BLEND_PATH.read_bytes()).hexdigest(),
            "bytes": ANIMATION_BLEND_PATH.stat().st_size,
            "collections": ["rig"],
            "expected_meshes": [],
            "expected_actions": list(ACTION_ORDER),
        },
    }


def aim_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_review_scene(hero: bpy.types.Object) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.filepath = str(RENDER_PATH)
    scene.render.image_settings.color_depth = "8"
    scene.render.resolution_percentage = 100
    scene.world = bpy.data.worlds.new("REVIEW_World")
    scene.world.color = (0.025, 0.032, 0.045)
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.engine = "BLENDER_EEVEE_NEXT"

    ground_material = make_material("REVIEW_Ground", (0.085, 0.105, 0.125, 1.0), 0.72, 0.0)
    bpy.ops.mesh.primitive_plane_add(size=12.0, location=(0.0, 0.0, 0.005))
    ground = bpy.context.object
    ground.name = "REVIEW_Ground"
    ground.data.materials.append(ground_material)

    bpy.ops.object.camera_add(location=(-2.65, -3.25, 1.78))
    camera = bpy.context.object
    camera.name = "REVIEW_Camera"
    camera.data.lens = 61
    camera.data.sensor_width = 36
    aim_at(camera, (0.02, 0.0, 0.59))
    scene.camera = camera

    def area(name: str, location, energy: float, color, size: float) -> None:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.color = color
        light.data.shape = "DISK"
        light.data.size = size
        aim_at(light, (0.0, 0.0, 0.58))

    area("REVIEW_Key", (-2.8, -2.3, 4.2), 1050.0, (1.0, 0.78, 0.58), 3.2)
    area("REVIEW_Fill", (-0.6, 3.3, 2.1), 720.0, (0.42, 0.64, 1.0), 2.8)
    area("REVIEW_Rim", (3.1, 0.8, 3.0), 920.0, (0.32, 0.52, 1.0), 2.2)

    scene.frame_set(1)
    hero.select_set(True)
    bpy.context.view_layer.objects.active = hero


def normalize_render_png(path: Path) -> None:
    """Remove Blender's time/path text chunks while preserving rendered pixels."""
    payload = path.read_bytes()
    signature = b"\x89PNG\r\n\x1a\n"
    if not payload.startswith(signature):
        raise RuntimeError(f"render is not PNG: {path}")
    cursor = len(signature)
    normalized = bytearray(signature)
    while cursor < len(payload):
        length = int.from_bytes(payload[cursor:cursor + 4], "big")
        chunk_end = cursor + 12 + length
        chunk_type = payload[cursor + 4:cursor + 8]
        if chunk_end > len(payload):
            raise RuntimeError(f"truncated PNG chunk in {path}")
        # PNG critical chunks have an uppercase first type byte.  Blender's
        # variable Date, Time, RenderTime, and source-path records are all
        # ancillary and are intentionally omitted from this review render.
        if 65 <= chunk_type[0] <= 90:
            normalized.extend(payload[cursor:chunk_end])
        cursor = chunk_end
        if chunk_type == b"IEND":
            break
    path.write_bytes(normalized)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)

    hero, builder = build_quarrune_mesh()
    distance, distance_builder = build_quarrune_distance_mesh()
    materials = (
        make_material(
            "QR_Ceramic", (0.72, 0.62, 0.46, 1.0), 0.62, 0.02,
            fast64_tex0=fast64_dynamic_body_texture(FAST64_BODY_TOP_REFERENCE),
        ),
        make_material(
            "QR_CobaltLattice", (0.035, 0.12, 0.38, 1.0), 0.34, 0.26,
            fast64_tex0=fast64_accent_texture(),
        ),
        make_material(
            "QR_Resonator", (0.095, 0.072, 0.052, 1.0), 0.44, 0.20,
            fast64_tex0=fast64_dynamic_body_texture(FAST64_BODY_BOTTOM_REFERENCE),
        ),
    )
    for obj in (hero, distance):
        for material in materials:
            obj.data.materials.append(material)

    rig = create_armature()
    bind_rigid(hero, builder, rig)
    bind_rigid(distance, distance_builder, rig)
    move_to_named_collection(hero, "hero_model")
    move_to_named_collection(distance, "distance_model")
    move_to_named_collection(rig, "rig")
    create_actions(rig)
    split_glbs = export_split_glbs(hero, distance, rig)

    hero.hide_set(False)
    hero.hide_viewport = False
    hero.hide_render = False
    distance.hide_set(True)
    distance.hide_viewport = True
    distance.hide_render = True
    setup_review_scene(hero)

    triangle_count = len(hero.data.polygons)
    distance_triangle_count = len(distance.data.polygons)
    distance_ratio = distance_triangle_count / triangle_count
    deform_bones = sum(1 for bone in rig.data.bones if bone.use_deform)
    action_names = tuple(action.name for action in bpy.data.actions)
    material_count = len(hero.data.materials)
    weight_counts = [len(vertex.groups) for vertex in hero.data.vertices]
    distance_weight_counts = [len(vertex.groups) for vertex in distance.data.vertices]
    if not 900 <= triangle_count <= 1250:
        raise RuntimeError(f"hero triangle target failed: {triangle_count}")
    if distance_triangle_count > 650 or not 0.45 <= distance_ratio <= 0.60:
        raise RuntimeError(
            f"distance triangle target failed: {distance_triangle_count} ({distance_ratio:.6f} of hero)"
        )
    if deform_bones != 20:
        raise RuntimeError(f"deform bone target failed: {deform_bones}")
    if action_names != ACTION_ORDER:
        raise RuntimeError(f"action order failed: {action_names!r}")
    if material_count != 3 or set(p.material_index for p in hero.data.polygons) != {0, 1, 2}:
        raise RuntimeError("exact three-material family requirement failed")
    if len(distance.data.materials) != 3 or set(p.material_index for p in distance.data.polygons) != {0, 1, 2}:
        raise RuntimeError("distance exact three-material family requirement failed")
    if not weight_counts or min(weight_counts) != 1 or max(weight_counts) != 1:
        raise RuntimeError("one-influence rigid weighting requirement failed")
    if not distance_weight_counts or min(distance_weight_counts) != 1 or max(distance_weight_counts) != 1:
        raise RuntimeError("distance one-influence rigid weighting requirement failed")

    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.render.render(write_still=True)
    normalize_render_png(RENDER_PATH)
    hero.hide_render = True
    distance.hide_set(False)
    distance.hide_viewport = False
    distance.hide_render = False
    bpy.context.scene.render.filepath = str(DISTANCE_RENDER_PATH)
    bpy.ops.render.render(write_still=True)
    normalize_render_png(DISTANCE_RENDER_PATH)
    hero.hide_render = False
    distance.hide_set(True)
    distance.hide_viewport = True
    distance.hide_render = True
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)
    role_source_blends = write_role_source_blends(hero, distance, rig)

    report = {
        "status": "SOURCE_CANDIDATE_NOT_GATE_EVIDENCE",
        "blender_version": bpy.app.version_string,
        "blend_path": str(BLEND_PATH),
        "render_path": str(RENDER_PATH),
        "distance_render_path": str(DISTANCE_RENDER_PATH),
        "triangle_count": triangle_count,
        "hero_triangle_count": triangle_count,
        "distance_triangle_count": distance_triangle_count,
        "distance_triangle_ratio": round(distance_ratio, 9),
        "material_families": [material.name for material in materials],
        "deform_bone_count": deform_bones,
        "one_influence_vertex_count": len(weight_counts),
        "distance_one_influence_vertex_count": len(distance_weight_counts),
        "action_order": list(action_names),
        "render_size": [960, 720],
        "split_glbs": split_glbs,
        "role_source_blends": role_source_blends,
    }
    (OUTPUT_DIR / "candidate_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("QUARRUNE_CANDIDATE=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
