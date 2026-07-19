from __future__ import annotations

import base64
import copy
import hashlib
import json
import struct
import subprocess
import unittest
from pathlib import Path

from test_libdragon_sprite_contract import accent_sprite, body_sprite, ext_offset, shadow_sprite


ROOT = Path(__file__).resolve().parents[2]
RUBY = "/usr/bin/ruby"
BUILD_ID = "n64game-g5-fixture-001"
TINY3D_COMMIT = "e84172f29f719680ac3213a7f408c2f721ef7b24"
MODEL_PATHS = [
    "review/echo.quarrune/g5/quarrune_distance.t3dm",
    "review/echo.quarrune/g5/quarrune_hero.t3dm",
]
ANIMATION_HEADER_PATH = "review/anm.echo.quarrune/g5/anm_echo_quarrune.t3dm"
BINDING_PATH = "review/anm.echo.quarrune/g5/SKELETON_BINDING.tsv"
BODY_TEXTURE_PATH = "review/echo.quarrune/g5/tex_quarrune_body_ci8_64x64.sprite"
ACCENT_TEXTURE_PATH = "review/echo.quarrune/g5/tex_quarrune_accent_ci4_32x32.sprite"
BLOB_SHADOW_PATH = "review/echo.quarrune/g5/tex_quarrune_blob_shadow_ia8_32x32.sprite"
RUNTIME_BINDING_PATH = "review/echo.quarrune/g5/RUNTIME_BINDING.tsv"
BODY_TEXTURE_ROM_PATH = "rom:/echo/echo.quarrune/tex_quarrune_body_ci8_64x64.sprite"
ACCENT_TEXTURE_ROM_PATH = "rom:/echo/echo.quarrune/tex_quarrune_accent_ci4_32x32.sprite"
BLOB_SHADOW_ROM_PATH = "rom:/echo/echo.quarrune/tex_quarrune_blob_shadow_ia8_32x32.sprite"
BODY_TOP_REFERENCE = 0x51554230
BODY_BOTTOM_REFERENCE = 0x51554231
QUARRUNE_TEX_SHADE_COMBINER = 0x001218248833FFFF
QUARRUNE_OTHER_MODE_VALUE = 0x0000000000000000
QUARRUNE_OTHER_MODE_MASK = 0x0000300000000000
ANIMATION_NAMES = [
    "brace_relay",
    "entrance",
    "hit",
    "horizon_break",
    "idle_a",
    "idle_b",
    "knockout",
    "reposition",
    "ridge_ram",
]
STREAM_PATHS = [
    f"review/anm.echo.quarrune/g5/anm_echo_quarrune.{index}.sdata"
    for index in range(9)
]
ROM_PATHS = [
    f"rom:/anm/anm.echo.quarrune/anm_echo_quarrune.{index}.sdata"
    for index in range(9)
]
BINDING_KEYS = [
    "schema",
    "tiny3d_commit",
    "model_production_id",
    "animation_production_id",
    "hero_model_path",
    "hero_model_sha256",
    "distance_model_path",
    "distance_model_sha256",
    "animation_header_path",
    "animation_header_sha256",
    "animation_stream_set_sha256",
    "skeleton_signature_sha256",
    "bone_count",
    "animation_names",
    "build_id",
]
RUNTIME_BINDING_KEYS = [
    "schema", "libdragon_commit", "tiny3d_commit", "runtime_helper_paths",
    "runtime_helper_bundle_sha256", "production_id", "body_sprite_path",
    "body_sprite_sha256", "body_rom_path", "body_top_reference", "body_top_rect_px",
    "body_bottom_reference", "body_bottom_rect_px", "body_reference_size_px", "body_upload_mode",
    "material_profile", "accent_sprite_path", "accent_sprite_sha256",
    "accent_rom_path", "blob_shadow_sprite_path", "blob_shadow_sprite_sha256", "blob_shadow_rom_path",
    "blob_shadow_format", "blob_shadow_size_px", "footprint_mm", "footprint_offset_mm",
    "base_opacity_q8", "build_id",
]


def align(value: int, alignment: int) -> int:
    return (value + alignment - 1) // alignment * alignment


def chunk_offsets(data: bytes, chunk_type: str) -> list[int]:
    count = struct.unpack_from(">I", data, 4)[0]
    return [
        int.from_bytes(data[0x2D + index * 4:0x30 + index * 4], "big")
        for index in range(count)
        if data[0x2C + index * 4] == ord(chunk_type)
    ]


def packed_vertices(total_vertices: int, marker: int,
                    minimum: tuple[int, int, int] = (-8, -4, -8),
                    maximum: tuple[int, int, int] = (8, 12, 8),
                    uvs: list[tuple[int, int]] | None = None) -> bytes:
    assert total_vertices >= 2 and total_vertices % 2 == 0
    positions = [minimum, maximum] + [minimum] * (total_vertices - 2)
    output = bytearray(total_vertices * 16)
    uvs = uvs or [(0, 0)] * total_vertices
    assert len(uvs) == total_vertices
    for index, position in enumerate(positions):
        pair = (index // 2) * 32
        struct.pack_into(">3h", output, pair + (8 if index % 2 else 0), *position)
        struct.pack_into(">I", output, pair + (20 if index % 2 else 16),
                         ((0x90 + marker) & 0xFF) << 24 | 0xA0B0FF)
        struct.pack_into(">2h", output, pair + (28 if index % 2 else 24), *uvs[index])
    return bytes(output)


def tiny3d_string_hash(value: str) -> int:
    result = 0x7E81C0E9
    for byte in value.encode():
        result = ((result >> 8) ^ ((result << 24) & 0xFFFFFFFF) ^ byte) & 0xFFFFFFFF
    return result


class StringTable:
    def __init__(self) -> None:
        self.data = bytearray(b"S")

    def add(self, value: str) -> int:
        encoded = value.encode() + b"\0"
        found = bytes(self.data).find(encoded)
        if found >= 0:
            return found
        offset = len(self.data)
        self.data.extend(encoded)
        return offset


def skeleton_payload(strings: StringTable) -> tuple[bytes, str]:
    bones = bytearray(struct.pack(">HH", 20, 0))
    signature = bytearray(b"n64game-tiny3d-skeleton-v1\n")
    signature.extend(struct.pack(">H", 20))
    for index in range(20):
        name = "q_root" if index == 0 else f"q_bone_{index:02d}"
        parent = 0xFFFF if index == 0 else index - 1
        depth = index
        transform = struct.pack(">10f", 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, float(index), 0.0)
        bones.extend(struct.pack(">IHH", strings.add(name), parent, depth))
        bones.extend(transform)
        name_bytes = name.encode()
        signature.extend(struct.pack(">HH", index, len(name_bytes)))
        signature.extend(name_bytes)
        signature.extend(struct.pack(">HH", parent, depth))
        signature.extend(transform)
    return bytes(bones), hashlib.sha256(signature).hexdigest()


def model_file(
    variant: str,
    *,
    with_bvh: bool = False,
    load_only_prefix: bool = False,
    sequence_only: bool = False,
    with_strip: bool = False,
    with_texture: bool = False,
) -> tuple[bytes, str]:
    assert not (sequence_only and with_strip)
    strings = StringTable()
    skeleton, signature = skeleton_payload(strings)
    material_name = f"quarrune_{variant}_mat"
    object_name = f"quarrune_{variant}"
    material_ref = strings.add(material_name)
    object_ref = strings.add(object_name)

    part_count = 2 if load_only_prefix else 1
    triangle_count = 3 if sequence_only else (4 if with_strip else 1)
    total_vertices = 10 if sequence_only else (8 if with_strip else 4)
    obj = bytearray()
    obj.extend(struct.pack(">IHHIII", object_ref, part_count, triangle_count, 0, 0, 0))
    obj.extend(struct.pack(">3h3h", -8, -4, -8, 8, 12, 8))
    if load_only_prefix:
        obj.extend(struct.pack(">IHHIHH4BBB2B", 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
    sequence_count = 3 if sequence_only else 0
    main_index_count = 0 if sequence_only else 3
    vertex_offset = 32 if load_only_prefix else 0
    vertex_count = 2 if load_only_prefix else total_vertices
    vertex_destination = 2 if load_only_prefix else 0
    strip_counts = (7, 0, 0, 0) if with_strip else (0, 0, 0, 0)
    obj.extend(
        struct.pack(">IHHIHH4BBB2B", vertex_offset, vertex_count, vertex_destination,
                    0, main_index_count, 1 if load_only_prefix else 0,
                    *strip_counts, 0, sequence_count, 0, 0)
    )
    assert len(obj) == 32 + part_count * 24

    vertex_marker = 0x11 if variant == "distance" else 0x22
    vertices = packed_vertices(total_vertices, vertex_marker)
    if sequence_only:
        indices = b""
        total_index_count = 0
    elif with_strip:
        strip_words = (0, 2, 3, 0x8004, 5, 6, 7)
        indices = bytes((0, 1, 2)) + bytes(5) + struct.pack(">7H", *strip_words) + bytes(2)
        total_index_count = 3
    else:
        indices = bytes((0, 1, 2))
        total_index_count = 3
    material = bytearray(0x8C)
    struct.pack_into(">I", material, 0x30, material_ref)
    if with_texture:
        texture_path = "rom:/echo/echo.quarrune/quarrune_test_ci8.sprite"
        struct.pack_into(">IIIIHH", material, 0x34, 0, strings.add(texture_path),
                         tiny3d_string_hash(texture_path), 0, 64, 64)

    bvh = struct.pack(">HH3h3hHH", 1, 1, -8, -4, -8, 8, 12, 8, 1, 0) if with_bvh else b""
    chunk_count = 6 if with_bvh else 5
    table_end = 0x2C + chunk_count * 4
    object_offset = align(table_end, 8)
    bvh_offset = align(object_offset + len(obj), 8) if with_bvh else None
    vertex_offset = align((bvh_offset + len(bvh)) if bvh_offset is not None else object_offset + len(obj), 16)
    index_offset = align(vertex_offset + len(vertices), 4)
    material_offset = align(index_offset + len(indices), 8)
    skeleton_offset = align(material_offset + len(material), 8)
    string_offset = align(skeleton_offset + len(skeleton), 4)
    output = bytearray(string_offset)
    output[0:4] = b"T3M\x04"
    vertex_index = 2 if with_bvh else 1
    struct.pack_into(">IHHIIIII3h3h", output, 4, chunk_count, total_vertices, total_index_count,
                     vertex_index, vertex_index + 1, vertex_index + 2, string_offset, 0,
                     -8, -4, -8, 8, 12, 8)
    chunks = [(b"O", object_offset)]
    if bvh_offset is not None:
        chunks.append((b"B", bvh_offset))
    chunks.extend([(b"V", vertex_offset), (b"I", index_offset),
                   (b"M", material_offset), (b"S", skeleton_offset)])
    for index, (chunk_type, offset) in enumerate(chunks):
        table = 0x2C + index * 4
        output[table] = chunk_type[0]
        output[table + 1:table + 4] = offset.to_bytes(3, "big")
    output[object_offset:object_offset + len(obj)] = obj
    if bvh_offset is not None:
        output[bvh_offset:bvh_offset + len(bvh)] = bvh
    output[vertex_offset:vertex_offset + len(vertices)] = vertices
    output[index_offset:index_offset + len(indices)] = indices
    output[material_offset:material_offset + len(material)] = material
    output[skeleton_offset:skeleton_offset + len(skeleton)] = skeleton
    output.extend(strings.data)
    return bytes(output), signature


def production_model_file(variant: str, triangle_total: int | None = None) -> tuple[bytes, str]:
    strings = StringTable()
    skeleton, signature = skeleton_payload(strings)
    triangle_total = triangle_total if triangle_total is not None else (500 if variant == "distance" else 900)
    assert triangle_total >= 3
    triangle_counts = [triangle_total // 3, triangle_total // 3, triangle_total - 2 * (triangle_total // 3)]
    bounds = [((-8, -4, -8), (-3, 4, -3)), ((-2, -2, -2), (2, 12, 2)), ((3, -3, 3), (8, 6, 8))]

    materials: list[bytes] = []
    texture_specs = (
        (BODY_TOP_REFERENCE, None, 64, 32),
        (BODY_BOTTOM_REFERENCE, None, 64, 32),
        (0, ACCENT_TEXTURE_ROM_PATH, 32, 32),
    )
    for index, (reference, path, width, height) in enumerate(texture_specs):
        material = bytearray(0x8C)
        struct.pack_into(">QQQII", material, 0, QUARRUNE_TEX_SHADE_COMBINER,
                         QUARRUNE_OTHER_MODE_VALUE, QUARRUNE_OTHER_MODE_MASK, 0, 0x07)
        struct.pack_into(">I", material, 0x30, strings.add(f"quarrune_{variant}_mat_{index}"))
        path_offset = strings.add(path) if path else 0
        texture_hash = tiny3d_string_hash(path) if path else reference
        struct.pack_into(">IIIIHH", material, 0x34, reference, path_offset, texture_hash, 0, width, height)
        struct.pack_into(">ffbbBB", material, 0x34 + 20, 0.0, float(width - 1), 0, 0, 0, 1)
        struct.pack_into(">ffbbBB", material, 0x34 + 32, 0.0, float(height - 1), 0, 0, 0, 1)
        materials.append(bytes(material))

    objects: list[bytes] = []
    vertices = bytearray()
    indices = bytearray()
    for index, (minimum, maximum) in enumerate(bounds):
        texture_width = texture_specs[index][2]
        texture_height = texture_specs[index][3]
        triangle_count = triangle_counts[index]
        obj = bytearray()
        obj.extend(struct.pack(">IHHIII", strings.add(f"quarrune_{variant}_part_{index}"),
                               1, triangle_count, index, 0, 0))
        obj.extend(struct.pack(">3h3h", *minimum, *maximum))
        obj.extend(struct.pack(">IHHIHH4BBB2B", index * 64, 4, 0, len(indices), triangle_count * 3,
                               index, 0, 0, 0, 0, 0, 0, 0, 0))
        objects.append(bytes(obj))
        vertices.extend(packed_vertices(
            4, 0x41 + index + (4 if variant == "hero" else 0), minimum, maximum,
            [
                (0, 0), (texture_width * 32, 0), (0, texture_height * 32),
                (texture_width * 32, texture_height * 32),
            ],
        ))
        triangle_patterns = ((0, 1, 2), (0, 2, 3))
        for triangle_index in range(triangle_count):
            indices.extend(triangle_patterns[triangle_index % len(triangle_patterns)])

    chunk_count = 9
    table_end = 0x2C + chunk_count * 4
    object_offsets: list[int] = []
    cursor = table_end
    for obj in objects:
        cursor = align(cursor, 8)
        object_offsets.append(cursor)
        cursor += len(obj)
    vertex_offset = align(cursor, 16)
    index_offset = align(vertex_offset + len(vertices), 4)
    material_offsets: list[int] = []
    cursor = index_offset + len(indices)
    for material in materials:
        cursor = align(cursor, 8)
        material_offsets.append(cursor)
        cursor += len(material)
    skeleton_offset = align(cursor, 8)
    string_offset = align(skeleton_offset + len(skeleton), 4)
    output = bytearray(string_offset)
    output[0:4] = b"T3M\x04"
    struct.pack_into(">IHHIIIII3h3h", output, 4, chunk_count, 12, len(indices), 3, 4, 5,
                     string_offset, 0, -8, -4, -8, 8, 12, 8)
    chunks = [(b"O", offset) for offset in object_offsets]
    chunks.extend([(b"V", vertex_offset), (b"I", index_offset)])
    chunks.extend((b"M", offset) for offset in material_offsets)
    chunks.append((b"S", skeleton_offset))
    for index, (chunk_type, offset) in enumerate(chunks):
        table = 0x2C + index * 4
        output[table] = chunk_type[0]
        output[table + 1:table + 4] = offset.to_bytes(3, "big")
    for obj, offset in zip(objects, object_offsets):
        output[offset:offset + len(obj)] = obj
    output[vertex_offset:vertex_offset + len(vertices)] = vertices
    output[index_offset:index_offset + len(indices)] = indices
    for material, offset in zip(materials, material_offsets):
        output[offset:offset + len(material)] = material
    output[skeleton_offset:skeleton_offset + len(skeleton)] = skeleton
    output.extend(strings.data)
    return bytes(output), signature


def two_object_bvh_file() -> tuple[bytes, str]:
    strings = StringTable()
    skeleton, signature = skeleton_payload(strings)
    material_ref = strings.add("quarrune_bvh_mat")
    bounds = [((-8, -4, -8), (0, 4, 0)), ((1, -2, 1), (8, 12, 8))]
    objects: list[bytes] = []
    vertices = bytearray()
    indices = bytearray()
    for index, (minimum, maximum) in enumerate(bounds):
        obj = bytearray()
        obj.extend(struct.pack(">IHHIII", strings.add(f"quarrune_bvh_{index}"), 1, 1, 0, 0, 0))
        obj.extend(struct.pack(">3h3h", *minimum, *maximum))
        obj.extend(struct.pack(">IHHIHH4BBB2B", index * 64, 4, 0, index * 3, 3,
                               index, 0, 0, 0, 0, 0, 0, 0, 0))
        objects.append(bytes(obj))
        vertices.extend(packed_vertices(4, 0x31 + index, minimum, maximum))
        indices.extend((0, 1, 2))

    material = bytearray(0x8C)
    struct.pack_into(">I", material, 0x30, material_ref)
    bvh = bytearray(struct.pack(">HH", 3, 2))
    bvh.extend(struct.pack(">3h3hH", -8, -4, -8, 8, 12, 8, 0x10))
    bvh.extend(struct.pack(">3h3hH", *bounds[0][0], *bounds[0][1], 0x01))
    bvh.extend(struct.pack(">3h3hH", *bounds[1][0], *bounds[1][1], 0x11))
    bvh.extend(struct.pack(">2H", 0, 1))

    chunk_count = 7
    table_end = 0x2C + chunk_count * 4
    object_offsets: list[int] = []
    cursor = table_end
    for obj in objects:
        cursor = align(cursor, 8)
        object_offsets.append(cursor)
        cursor += len(obj)
    bvh_offset = align(cursor, 8)
    vertex_offset = align(bvh_offset + len(bvh), 16)
    index_offset = align(vertex_offset + len(vertices), 4)
    material_offset = align(index_offset + len(indices), 8)
    skeleton_offset = align(material_offset + len(material), 8)
    string_offset = align(skeleton_offset + len(skeleton), 4)
    output = bytearray(string_offset)
    output[0:4] = b"T3M\x04"
    struct.pack_into(">IHHIIIII3h3h", output, 4, chunk_count, 8, 6, 3, 4, 5,
                     string_offset, 0, -8, -4, -8, 8, 12, 8)
    chunks = [(b"O", offset) for offset in object_offsets]
    chunks.extend(((b"B", bvh_offset), (b"V", vertex_offset), (b"I", index_offset),
                   (b"M", material_offset), (b"S", skeleton_offset)))
    for index, (chunk_type, offset) in enumerate(chunks):
        table = 0x2C + index * 4
        output[table] = chunk_type[0]
        output[table + 1:table + 4] = offset.to_bytes(3, "big")
    for obj, offset in zip(objects, object_offsets):
        output[offset:offset + len(obj)] = obj
    output[bvh_offset:bvh_offset + len(bvh)] = bvh
    output[vertex_offset:vertex_offset + len(vertices)] = vertices
    output[index_offset:index_offset + len(indices)] = indices
    output[material_offset:material_offset + len(material)] = material
    output[skeleton_offset:skeleton_offset + len(skeleton)] = skeleton
    output.extend(strings.data)
    return bytes(output), signature


def stream_file(scalar_value: int = 0xFFFF) -> bytes:
    return b"".join(
        (
            struct.pack(">HHHH", 0, 0, 0xE008, 0x0200),
            struct.pack(">HHH", 0x8000, 1, 0),
            struct.pack(">HHHH", 60, 0, 0xE008, 0x0200),
            struct.pack(">HHH", 60, 1, scalar_value),
        )
    )


def animation_file() -> tuple[bytes, dict[str, bytes], str]:
    strings = StringTable()
    skeleton, signature = skeleton_payload(strings)
    animation_chunks: list[bytes] = []
    for index, name in enumerate(ANIMATION_NAMES):
        name_ref = strings.add(name)
        path_ref = strings.add(ROM_PATHS[index])
        chunk = bytearray(struct.pack(">IfIHHI", name_ref, 1.0, 4, 1, 1, path_ref))
        chunk.extend(struct.pack(">HBBII", 0, 3, 0, 0xFF800000, 0x7F800000))
        chunk.extend(struct.pack(">HBBff", 1, 0, 0, 1.0 / 65535.0, 0.0))
        assert len(chunk) == 44
        animation_chunks.append(bytes(chunk))

    chunk_count = 12
    table_end = 0x2C + chunk_count * 4
    cursor = align(table_end, 8)
    chunk_offsets: list[tuple[bytes, int]] = []
    for chunk in animation_chunks:
        cursor = align(cursor, 4)
        chunk_offsets.append((b"A", cursor))
        cursor += len(chunk)
    vertex_offset = align(cursor, 16)
    chunk_offsets.extend([(b"V", vertex_offset), (b"I", vertex_offset), (b"S", vertex_offset)])
    string_offset = align(vertex_offset + len(skeleton), 4)
    output = bytearray(string_offset)
    output[0:4] = b"T3M\x04"
    struct.pack_into(">IHHIIIII3h3h", output, 4, chunk_count, 0, 0, 9, 10, 11, string_offset, 0,
                     32767, 32767, 32767, -32768, -32768, -32768)
    for index, (chunk_type, offset) in enumerate(chunk_offsets):
        table = 0x2C + index * 4
        output[table] = chunk_type[0]
        output[table + 1:table + 4] = offset.to_bytes(3, "big")
    for chunk, (_, offset) in zip(animation_chunks, chunk_offsets):
        output[offset:offset + len(chunk)] = chunk
    output[vertex_offset:vertex_offset + len(skeleton)] = skeleton
    output.extend(strings.data)
    streams = {path: stream_file(index + 1) for index, path in enumerate(STREAM_PATHS)}
    return bytes(output), streams, signature


def entry(path: str, role: str, data: bytes, kind: str) -> dict[str, object]:
    return {
        "path": path,
        "role": role,
        "digest": hashlib.sha256(data).hexdigest(),
        "count": len(data),
        "build": BUILD_ID,
        "capture": "-",
        "kind": kind,
        "mode": "100644",
    }


def stream_set_digest(entries: list[dict[str, object]]) -> str:
    by_path = {str(value["path"]): value for value in entries}
    payload = bytearray(b"n64game-quarrune-animation-stream-set-v1\n")
    for path in STREAM_PATHS:
        digest = str(by_path[path]["digest"])
        payload.extend(struct.pack(">H", len(path.encode())))
        payload.extend(path.encode())
        payload.extend(struct.pack(">H", len(digest.encode())))
        payload.extend(digest.encode())
    return hashlib.sha256(payload).hexdigest()


def binding_bytes(model_entries: list[dict[str, object]], animation_entries: list[dict[str, object]],
                  signature: str, build_id: str = BUILD_ID) -> bytes:
    by_path = {str(value["path"]): value for value in model_entries + animation_entries}
    values = {
        "schema": "n64game-quarrune-skeleton-binding-v1",
        "tiny3d_commit": TINY3D_COMMIT,
        "model_production_id": "echo.quarrune",
        "animation_production_id": "anm.echo.quarrune",
        "hero_model_path": MODEL_PATHS[1],
        "hero_model_sha256": str(by_path[MODEL_PATHS[1]]["digest"]),
        "distance_model_path": MODEL_PATHS[0],
        "distance_model_sha256": str(by_path[MODEL_PATHS[0]]["digest"]),
        "animation_header_path": ANIMATION_HEADER_PATH,
        "animation_header_sha256": str(by_path[ANIMATION_HEADER_PATH]["digest"]),
        "animation_stream_set_sha256": stream_set_digest(animation_entries),
        "skeleton_signature_sha256": signature,
        "bone_count": "20",
        "animation_names": ",".join(ANIMATION_NAMES),
        "build_id": build_id,
    }
    return "".join(f"{key}\t{values[key]}\n" for key in BINDING_KEYS).encode()


def runtime_binding_bytes(model_entries: list[dict[str, object]], build_id: str = BUILD_ID) -> bytes:
    by_path = {str(value["path"]): value for value in model_entries}
    values = {
        "schema": "n64game-quarrune-runtime-binding-v1",
        "libdragon_commit": "f13b48985edbf4310f07779c76d9a68c7605037b",
        "tiny3d_commit": TINY3D_COMMIT,
        "runtime_helper_paths": "src/quarrune_render_assets.c,src/quarrune_render_assets.h",
        "runtime_helper_bundle_sha256": "b9125d3375842e75dc4d0227abbf2158126e1b9ba684842c9f9326071c7b7853",
        "production_id": "echo.quarrune",
        "body_sprite_path": BODY_TEXTURE_PATH,
        "body_sprite_sha256": str(by_path[BODY_TEXTURE_PATH]["digest"]),
        "body_rom_path": BODY_TEXTURE_ROM_PATH,
        "body_top_reference": f"0x{BODY_TOP_REFERENCE:08X}",
        "body_top_rect_px": "0,0,64,32",
        "body_bottom_reference": f"0x{BODY_BOTTOM_REFERENCE:08X}",
        "body_bottom_rect_px": "0,32,64,64",
        "body_reference_size_px": "64,32",
        "body_upload_mode": "surface_make_sub+rdpq_tex_upload+tlut_every_bind",
        "material_profile": "TILE0_TEX0_X_SHADE_POINT",
        "accent_sprite_path": ACCENT_TEXTURE_PATH,
        "accent_sprite_sha256": str(by_path[ACCENT_TEXTURE_PATH]["digest"]),
        "accent_rom_path": ACCENT_TEXTURE_ROM_PATH,
        "blob_shadow_sprite_path": BLOB_SHADOW_PATH,
        "blob_shadow_sprite_sha256": str(by_path[BLOB_SHADOW_PATH]["digest"]),
        "blob_shadow_rom_path": BLOB_SHADOW_ROM_PATH,
        "blob_shadow_format": "IA8",
        "blob_shadow_size_px": "32,32",
        "footprint_mm": "1250,800",
        "footprint_offset_mm": "0,0",
        "base_opacity_q8": "176",
        "build_id": build_id,
    }
    return "".join(f"{key}\t{values[key]}\n" for key in RUNTIME_BINDING_KEYS).encode()


def refresh_entry(values: dict[str, object], path: str) -> None:
    entries = values["model_entries"] + values["animation_entries"]  # type: ignore[operator]
    target = next(item for item in entries if item["path"] == path)
    data = values["bytes"][path]  # type: ignore[index]
    target["digest"] = hashlib.sha256(data).hexdigest()
    target["count"] = len(data)


def fixture(*, hero_triangles: int = 900, distance_triangles: int = 500) -> dict[str, object]:
    distance, signature = production_model_file("distance", distance_triangles)
    hero, hero_signature = production_model_file("hero", hero_triangles)
    animation, streams, animation_signature = animation_file()
    assert signature == hero_signature == animation_signature
    values: dict[str, bytes] = {
        MODEL_PATHS[0]: distance,
        MODEL_PATHS[1]: hero,
        BODY_TEXTURE_PATH: body_sprite(),
        ACCENT_TEXTURE_PATH: accent_sprite(),
        BLOB_SHADOW_PATH: shadow_sprite(),
        ANIMATION_HEADER_PATH: animation,
    }
    values.update(streams)
    model_entries = [entry(path, "output.tiny3d.model", values[path], "lfs") for path in MODEL_PATHS]
    model_entries.extend((
        entry(BODY_TEXTURE_PATH, "output.texture.body", values[BODY_TEXTURE_PATH], "lfs"),
        entry(ACCENT_TEXTURE_PATH, "output.texture.accent", values[ACCENT_TEXTURE_PATH], "lfs"),
        entry(BLOB_SHADOW_PATH, "output.blob_shadow.sprite", values[BLOB_SHADOW_PATH], "lfs"),
    ))
    runtime_binding = runtime_binding_bytes(model_entries)
    values[RUNTIME_BINDING_PATH] = runtime_binding
    model_entries.append(entry(RUNTIME_BINDING_PATH, "output.runtime_binding", runtime_binding, "git"))
    animation_entries = [entry(ANIMATION_HEADER_PATH, "output.tiny3d.animation_header", animation, "lfs")]
    animation_entries.extend(entry(path, "output.tiny3d.animation_stream", streams[path], "lfs") for path in STREAM_PATHS)
    binding = binding_bytes(model_entries, animation_entries, signature)
    values[BINDING_PATH] = binding
    animation_entries.append(entry(BINDING_PATH, "output.skeleton_binding", binding, "git"))
    return {
        "model_entries": model_entries,
        "animation_entries": animation_entries,
        "bytes": values,
        "signature": signature,
    }


def refresh_runtime_binding(values: dict[str, object]) -> None:
    binding = runtime_binding_bytes(values["model_entries"])  # type: ignore[arg-type]
    values["bytes"][RUNTIME_BINDING_PATH] = binding  # type: ignore[index]
    refresh_entry(values, RUNTIME_BINDING_PATH)


class Tiny3DPackageContractTests(unittest.TestCase):
    maxDiff = None

    def ruby(self, operation: str, payload: dict[str, object]) -> dict[str, object]:
        encoded = copy.deepcopy(payload)
        if "bytes" in encoded:
            encoded["bytes"] = {
                path: base64.b64encode(value).decode()  # type: ignore[arg-type]
                for path, value in encoded["bytes"].items()  # type: ignore[union-attr]
            }
        program = r"""
          require 'base64'
          require 'json'
          require 'n64game/tiny3d_package_contract'
          input = JSON.parse(STDIN.read)
          bytes = (input['bytes'] || {}).each_with_object({}) do |(path, value), values|
            values[path] = Base64.strict_decode64(value)
          end
          contract = N64Game::Tiny3DPackageContract
          case input['operation']
          when 'pair'
            issues = contract.validate_pair(
              model_entries: input['model_entries'], animation_entries: input['animation_entries'],
              bytes_by_path: bytes, model_build_id: input['model_build_id'],
              animation_build_id: input['animation_build_id']
            )
            result = {'issues' => issues}
            if issues.empty?
              model = contract.decode_model(bytes[contract::HERO_MODEL_PATH], contract::HERO_MODEL_PATH)
              streams = contract::ANIMATION_STREAM_PATHS.each_with_object({}) { |path, values| values[path] = bytes[path] }
              animation = contract.decode_animation(bytes[contract::ANIMATION_HEADER_PATH], streams, contract::ANIMATION_HEADER_PATH)
              result['model'] = model
              result['animation'] = animation
            end
          when 'model'
            begin
              result = {'issues' => [], 'decoded' => contract.decode_model(bytes['subject'], 'subject')}
            rescue N64Game::Tiny3DPackageContract::ParseError => error
              result = {'issues' => [error.message]}
            end
          when 'animation'
            begin
              streams = contract::ANIMATION_STREAM_PATHS.each_with_object({}) { |path, values| values[path] = bytes[path] if bytes.key?(path) }
              result = {'issues' => [], 'decoded' => contract.decode_animation(bytes['subject'], streams, 'subject')}
            rescue N64Game::Tiny3DPackageContract::ParseError => error
              result = {'issues' => [error.message]}
            end
          else
            raise 'unknown operation'
          end
          STDOUT.write(JSON.generate(result))
        """
        completed = subprocess.run(
            [RUBY, "--disable-gems", "-I", str(ROOT / "lib"), "-e", program],
            input=json.dumps({"operation": operation, **encoded}),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def pair_payload(self, values: dict[str, object]) -> dict[str, object]:
        return {
            "model_entries": values["model_entries"],
            "animation_entries": values["animation_entries"],
            "bytes": values["bytes"],
            "model_build_id": BUILD_ID,
            "animation_build_id": BUILD_ID,
        }

    def test_exact_two_model_nine_stream_pair_passes_and_reports_decoded_contract(self) -> None:
        values = fixture()
        result = self.ruby("pair", self.pair_payload(values))
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["model"]["bone_count"], 20)
        self.assertEqual(result["model"]["skeleton_signature"], values["signature"])
        self.assertEqual(result["model"]["objects"][0]["drawn_source_vertices"], [0, 1, 2, 3])
        self.assertEqual(result["animation"]["animation_names"], ANIMATION_NAMES)
        self.assertEqual(result["animation"]["stream_count"], 9)
        self.assertEqual(result["animation"]["skeleton_signature"], values["signature"])

    def test_writer_valid_optional_model_layouts_are_regression_bound(self) -> None:
        variants = {
            "single_leaf_bvh": model_file("hero", with_bvh=True)[0],
            "load_only_bone_prefix": model_file("hero", load_only_prefix=True)[0],
            "three_triangle_sequence": model_file("hero", sequence_only=True)[0],
            "strip_with_restart": model_file("hero", with_strip=True)[0],
            "bound_texture": model_file("hero", with_texture=True)[0],
            "two_object_internal_bvh": two_object_bvh_file()[0],
        }
        for name, data in variants.items():
            with self.subTest(layout=name):
                result = self.ruby("model", {"bytes": {"subject": data}})
                self.assertEqual(result["issues"], [], result)
        decoded = self.ruby("model", {"bytes": {"subject": variants["two_object_internal_bvh"]}})["decoded"]
        self.assertEqual(decoded["object_count"], 2)
        self.assertTrue(decoded["has_bvh"])
        expected_drawn_sources = {
            "load_only_bone_prefix": [0, 1, 2],
            "three_triangle_sequence": list(range(9)),
            "strip_with_restart": list(range(8)),
        }
        for name, expected in expected_drawn_sources.items():
            with self.subTest(drawn_sources=name):
                decoded = self.ruby("model", {"bytes": {"subject": variants[name]}})["decoded"]
                self.assertEqual(decoded["objects"][0]["drawn_source_vertices"], expected)

    def test_material_texture_binding_and_runtime_fields_are_checked(self) -> None:
        clean, _signature = model_file("hero", with_texture=True)
        material_offset = chunk_offsets(clean, "M")[0]
        cases: dict[str, tuple[callable, str]] = {
            "dynamic_reference_with_path": (
                lambda data: struct.pack_into(">I", data, material_offset + 0x34, 1),
                "dynamic reference",
            ),
            "path_hash": (lambda data: struct.pack_into(">I", data, material_offset + 0x34 + 8, 0), "path/hash"),
            "runtime_pointer": (lambda data: struct.pack_into(">I", data, material_offset + 0x34 + 12, 1), "runtime pointer"),
            "zero_width": (lambda data: struct.pack_into(">H", data, material_offset + 0x34 + 16, 0), "dimensions are invalid"),
            "unsupported_tile_shift": (
                lambda data: data.__setitem__(material_offset + 0x34 + 20 + 9, 11),
                "tile parameters",
            ),
        }
        for name, (mutate, expected) in cases.items():
            with self.subTest(mutation=name):
                mutated = bytearray(clean)
                mutate(mutated)
                result = self.ruby("model", {"bytes": {"subject": bytes(mutated)}})
                self.assertTrue(result["issues"], result)
                self.assertIn(expected, result["issues"][0])

        unbound, _signature = model_file("hero")
        mutated = bytearray(unbound)
        material_offset = chunk_offsets(unbound, "M")[0]
        struct.pack_into(">I", mutated, material_offset + 0x34, 1)
        result = self.ruby("model", {"bytes": {"subject": bytes(mutated)}})
        self.assertTrue(result["issues"], result)
        self.assertIn("unbound texture hash", result["issues"][0])

    def test_geometry_cache_and_source_bounds_are_exact(self) -> None:
        clean, _signature = model_file("hero")
        object_offset = chunk_offsets(clean, "O")[0]
        index_offset = chunk_offsets(clean, "I")[0]
        cases: dict[str, tuple[callable, str]] = {
            "unloaded_main_index": (
                lambda data: data.__setitem__(index_offset, 69), "unloaded Tiny3D vertex-cache slot"
            ),
            "degenerate_main_triangle": (
                lambda data: data.__setitem__(index_offset + 2, 1), "degenerate triangle"
            ),
            "forged_header_and_object_bounds": (
                lambda data: (struct.pack_into(">h", data, 0x20, -7),
                              struct.pack_into(">h", data, object_offset + 20, -7)),
                "AABB differs from its exact source vertices",
            ),
        }
        for name, (mutate, expected) in cases.items():
            with self.subTest(mutation=name):
                mutated = bytearray(clean)
                mutate(mutated)
                result = self.ruby("model", {"bytes": {"subject": bytes(mutated)}})
                self.assertTrue(result["issues"], result)
                self.assertIn(expected, result["issues"][0])

        load_only, _signature = model_file("hero", load_only_prefix=True)
        mutated = bytearray(load_only)
        object_offset = chunk_offsets(load_only, "O")[0]
        struct.pack_into(">I", mutated, object_offset + 32 + 24, 0)
        result = self.ruby("model", {"bytes": {"subject": bytes(mutated)}})
        self.assertTrue(result["issues"], result)
        self.assertIn("source ranges do not cover the exact V chunk", result["issues"][0])

        sequence, _signature = model_file("hero", sequence_only=True)
        mutated = bytearray(sequence)
        object_offset = chunk_offsets(sequence, "O")[0]
        mutated[object_offset + 32 + 20] = 2
        result = self.ruby("model", {"bytes": {"subject": bytes(mutated)}})
        self.assertTrue(result["issues"], result)
        self.assertIn("unloaded vertex-cache slot", result["issues"][0])

    def test_strip_payload_restart_padding_and_triangle_census_are_exact(self) -> None:
        clean, _signature = model_file("hero", with_strip=True)
        object_offset = chunk_offsets(clean, "O")[0]
        index_offset = chunk_offsets(clean, "I")[0]
        strip_offset = index_offset + 8
        cases: dict[str, tuple[callable, str]] = {
            "internal_padding": (lambda data: data.__setitem__(index_offset + 3, 1), "alignment padding is nonzero"),
            "first_restart": (lambda data: struct.pack_into(">H", data, strip_offset, 0x8000), "begins with a restart"),
            "short_segment": (lambda data: struct.pack_into(">H", data, strip_offset + 2, 0x8002), "fewer than three"),
            "unloaded_strip_index": (lambda data: struct.pack_into(">H", data, strip_offset + 12, 69), "unloaded Tiny3D vertex-cache slot"),
            "degenerate_strip": (lambda data: struct.pack_into(">H", data, strip_offset + 4, 0), "degenerate triangle"),
            "trailing_padding": (lambda data: data.__setitem__(index_offset + 22, 1), "nonzero padding"),
            "triangle_census": (lambda data: struct.pack_into(">H", data, object_offset + 6, 5), "exact draw commands"),
        }
        for name, (mutate, expected) in cases.items():
            with self.subTest(mutation=name):
                mutated = bytearray(clean)
                mutate(mutated)
                result = self.ruby("model", {"bytes": {"subject": bytes(mutated)}})
                self.assertTrue(result["issues"], result)
                self.assertIn(expected, result["issues"][0])

    def test_internal_bvh_graph_bounds_and_object_permutation_are_exact(self) -> None:
        clean, _signature = two_object_bvh_file()
        bvh_offset = chunk_offsets(clean, "B")[0]

        def overlap_leaf_ranges(data: bytearray) -> None:
            leaf = bvh_offset + 4 + 14
            struct.pack_into(">3h3hH", data, leaf, -8, -4, -8, 8, 12, 8, 0x02)

        cases: dict[str, tuple[callable, str]] = {
            "root_bounds": (lambda data: struct.pack_into(">h", data, bvh_offset + 4, -7), "exact descendants"),
            "leaf_bounds": (lambda data: struct.pack_into(">h", data, bvh_offset + 4 + 14, -7), "exact descendants"),
            "child_out_of_range": (lambda data: struct.pack_into(">H", data, bvh_offset + 16, 0x30), "child offset is invalid"),
            "duplicate_object": (lambda data: struct.pack_into(">H", data, bvh_offset + 4 + 3 * 14 + 2, 0), "exact object permutation"),
            "overlapping_leaf_ranges": (overlap_leaf_ranges, "leaf ranges overlap or omit data"),
        }
        for name, (mutate, expected) in cases.items():
            with self.subTest(mutation=name):
                mutated = bytearray(clean)
                mutate(mutated)
                result = self.ruby("model", {"bytes": {"subject": bytes(mutated)}})
                self.assertTrue(result["issues"], result)
                self.assertIn(expected, result["issues"][0])

    def test_model_parser_rejects_structural_runtime_and_rig_mutations(self) -> None:
        clean, _signature = model_file("hero")
        object_offset = chunk_offsets(clean, "O")[0]
        skeleton_offset = chunk_offsets(clean, "S")[0]
        cases: dict[str, tuple[callable, str]] = {
            "magic": (lambda data: data.__setitem__(3, 3), "magic/version"),
            "runtime_block": (lambda data: struct.pack_into(">I", data, 0x1C, 1), "runtime block"),
            "wrong_type": (lambda data: data.__setitem__(0x2C, ord("A")), "chunk sequence"),
            "decreasing_offset": (lambda data: data.__setitem__(slice(0x2D, 0x30), (140).to_bytes(3, "big")), "offsets decrease"),
            "vertex_count": (lambda data: struct.pack_into(">H", data, 8, 3), "positive and even"),
            "object_runtime": (lambda data: data.__setitem__(object_offset + 16, 1), "runtime/padding"),
            "part_bone": (lambda data: struct.pack_into(">H", data, object_offset + 32 + 14, 20), "exactly one joint"),
            "unweighted_part": (lambda data: struct.pack_into(">H", data, object_offset + 32 + 14, 0xFFFF), "exactly one joint"),
            "bone_count": (lambda data: struct.pack_into(">H", data, skeleton_offset, 19), "exactly 20 bones"),
            "skeleton_reserved": (lambda data: struct.pack_into(">H", data, skeleton_offset + 2, 1), "reserved"),
            "root_parent": (lambda data: struct.pack_into(">H", data, skeleton_offset + 4 + 4, 0), "sole depth-zero root"),
            "forward_parent": (lambda data: struct.pack_into(">H", data, skeleton_offset + 4 + 48 + 4, 2), "parent must precede"),
            "wrong_depth": (lambda data: struct.pack_into(">H", data, skeleton_offset + 4 + 48 + 6, 7), "depth"),
            "zero_scale": (lambda data: struct.pack_into(">f", data, skeleton_offset + 4 + 8, 0.0), "scale must be positive"),
            "nan_transform": (lambda data: struct.pack_into(">I", data, skeleton_offset + 4 + 8, 0x7FC00000), "non-finite"),
            "bad_quaternion": (lambda data: struct.pack_into(">4f", data, skeleton_offset + 4 + 20, 0.0, 0.0, 0.0, 0.0), "not normalized"),
        }
        for name, (mutate, expected) in cases.items():
            with self.subTest(mutation=name):
                mutated = bytearray(clean)
                mutate(mutated)
                result = self.ruby("model", {"bytes": {"subject": bytes(mutated)}})
                self.assertTrue(result["issues"], result)
                self.assertIn(expected, result["issues"][0])

    def test_animation_parser_rejects_header_mapping_and_stream_mutations(self) -> None:
        header, streams, _signature = animation_file()

        def run(mutated_header: bytes, mutated_streams: dict[str, bytes]) -> list[str]:
            result = self.ruby("animation", {"bytes": {"subject": mutated_header, **mutated_streams}})
            return result["issues"]

        header_cases: dict[str, tuple[callable, str]] = {
            "geometry_count": (lambda data: struct.pack_into(">H", data, 8, 2), "geometry counts"),
            "aabb": (lambda data: struct.pack_into(">h", data, 0x20, 0), "AABB sentinels"),
            "object_chunk": (lambda data: data.__setitem__(0x2C, ord("O")), "chunk sequence"),
            "wrong_vertex_index": (lambda data: struct.pack_into(">I", data, 0x0C, 8), "chunk indices"),
            "zero_duration": (lambda data: struct.pack_into(">f", data, 96 + 4, 0.0), "duration"),
            "unsupported_type": (lambda data: data.__setitem__(96 + 20 + 12 + 2, 2), "runtime-unsupported"),
            "bad_target": (lambda data: struct.pack_into(">H", data, 96 + 20, 20), "missing bone"),
            "quat_attr": (lambda data: data.__setitem__(96 + 20 + 3, 1), "quaternion channel"),
            "quat_quant": (lambda data: struct.pack_into(">I", data, 96 + 20 + 4, 0), "quaternion channel"),
        }
        for name, (mutate, expected) in header_cases.items():
            with self.subTest(mutation=name):
                mutated = bytearray(header)
                mutate(mutated)
                issues = run(bytes(mutated), streams)
                self.assertTrue(issues)
                self.assertIn(expected, issues[0])

        stream_cases: dict[str, tuple[callable, str]] = {
            "missing": (lambda values: values.pop(STREAM_PATHS[-1]), "stream file set"),
            "truncated": (lambda values: values.__setitem__(STREAM_PATHS[0], values[STREAM_PATHS[0]][:-1]), "out of bounds"),
            "trailing": (lambda values: values.__setitem__(STREAM_PATHS[0], values[STREAM_PATHS[0]] + b"\0"), "trailing bytes"),
            "channel": (lambda values: values.__setitem__(STREAM_PATHS[0], values[STREAM_PATHS[0]][:2] + struct.pack(">H", 2) + values[STREAM_PATHS[0]][4:]), "out of range"),
            "flag_chain": (lambda values: values.__setitem__(STREAM_PATHS[0], values[STREAM_PATHS[0]][:10] + struct.pack(">H", 0) + values[STREAM_PATHS[0]][12:]), "next-size bit"),
            "zero_quat": (lambda values: values.__setitem__(STREAM_PATHS[0], values[STREAM_PATHS[0]][:4] + b"\0\0\0\0" + values[STREAM_PATHS[0]][8:]), "zero quaternion"),
            "invalid_quat_radicand": (lambda values: values.__setitem__(STREAM_PATHS[0], values[STREAM_PATHS[0]][:4] + struct.pack(">I", 0x3FFFFFFF) + values[STREAM_PATHS[0]][8:]), "invalid runtime radicand"),
            "global_writer_order": (lambda values: values.__setitem__(STREAM_PATHS[0], struct.pack(">H", 1) + values[STREAM_PATHS[0]][2:]), "global timeline order"),
            "tick_coverage": (lambda values: values.__setitem__(STREAM_PATHS[0], values[STREAM_PATHS[0]][:14] + struct.pack(">H", 2) + values[STREAM_PATHS[0]][16:]), "tick coverage"),
        }
        for name, (mutate, expected) in stream_cases.items():
            with self.subTest(mutation=name):
                mutated_streams = dict(streams)
                mutate(mutated_streams)
                issues = run(header, mutated_streams)
                self.assertTrue(issues)
                self.assertIn(expected, issues[0])

    def test_pair_rejects_ownership_build_storage_and_binding_mutations(self) -> None:
        cases: dict[str, tuple[callable, str]] = {
            "missing_model": (lambda value: value["model_entries"].pop(0), "exactly the hero and distance"),
            "wrong_model_role": (lambda value: value["model_entries"][0].__setitem__("role", "output.texture"), "wrong model role"),
            "model_stream": (lambda value: value["model_entries"].append(entry(STREAM_PATHS[0], "output.tiny3d.animation_stream", value["bytes"][STREAM_PATHS[0]], "lfs")), "must not own animation streams"),
            "missing_stream": (lambda value: value["animation_entries"].pop(1), "exact nine canonical streams"),
            "wrong_stream_role": (lambda value: value["animation_entries"][1].__setitem__("role", "output.binary"), "wrong animation-stream role"),
            "ordinary_git_binary": (lambda value: value["animation_entries"][0].__setitem__("kind", "git"), "storage kind must be lfs"),
            "executable": (lambda value: value["animation_entries"][0].__setitem__("mode", "100755"), "mode 100644"),
            "capture": (lambda value: value["animation_entries"][0].__setitem__("capture", "preview"), "capture:-"),
            "entry_build": (lambda value: value["animation_entries"][0].__setitem__("build", "other-build"), "manifest build differs"),
            "extra_model_t3dm": (
                lambda value: value["model_entries"].append(
                    entry("review/echo.quarrune/g5/unreviewed.t3dm", "output.binary",
                          value["bytes"][MODEL_PATHS[0]], "lfs")
                ),
                "exactly the hero and distance",
            ),
            "extra_animation_stream": (
                lambda value: value["animation_entries"].append(
                    entry("review/anm.echo.quarrune/g5/unreviewed.sdata", "output.binary",
                          value["bytes"][STREAM_PATHS[0]], "lfs")
                ),
                "exact nine canonical streams",
            ),
            "reserved_role_wrong_path": (
                lambda value: value["animation_entries"].append(
                    entry("review/anm.echo.quarrune/g5/wrong.bin", "output.tiny3d.animation_header",
                          b"wrong", "git")
                ),
                "role may name only the canonical header",
            ),
            "binding_signature": (lambda value: value["bytes"].__setitem__(BINDING_PATH, value["bytes"][BINDING_PATH].replace(value["signature"].encode(), b"0" * 64)), "SHA-256 differs"),
            "missing_sprite": (
                lambda value: value["model_entries"].__delitem__(2),
                "exactly the body, accent, and blob-shadow sprites",
            ),
            "wrong_sprite_role": (
                lambda value: value["model_entries"][2].__setitem__("role", "output.binary"),
                "wrong sprite role",
            ),
            "ordinary_git_sprite": (
                lambda value: value["model_entries"][2].__setitem__("kind", "git"),
                "storage kind must be lfs",
            ),
            "executable_sprite": (
                lambda value: value["model_entries"][2].__setitem__("mode", "100755"),
                "mode 100644",
            ),
            "extra_sprite": (
                lambda value: value["model_entries"].append(
                    entry("review/echo.quarrune/g5/unreviewed.sprite", "output.binary",
                          value["bytes"][BODY_TEXTURE_PATH], "lfs")
                ),
                "exactly the body, accent, and blob-shadow sprites",
            ),
            "missing_runtime_binding": (
                lambda value: value["model_entries"].pop(),
                "exactly one canonical runtime binding",
            ),
            "wrong_runtime_binding_role": (
                lambda value: value["model_entries"][-1].__setitem__("role", "output.binary"),
                "wrong runtime-binding role",
            ),
        }
        for name, (mutate, expected) in cases.items():
            with self.subTest(mutation=name):
                values = fixture()
                mutate(values)
                result = self.ruby("pair", self.pair_payload(values))
                self.assertTrue(result["issues"], result)
                self.assertTrue(any(expected in issue for issue in result["issues"]), result["issues"])

        values = fixture()
        payload = self.pair_payload(values)
        payload["animation_build_id"] = "other-build"
        result = self.ruby("pair", payload)
        self.assertTrue(any("shared substantive build ID" in issue for issue in result["issues"]))

    def test_production_pair_enforces_budgets_material_use_and_dynamic_regions(self) -> None:
        budget_cases = (
            ("hero_low", {"hero_triangles": 849}, "850-1250 hero budget"),
            ("hero_high", {"hero_triangles": 1251}, "850-1250 hero budget"),
            ("distance_high", {"hero_triangles": 1100, "distance_triangles": 651}, "45-60 percent"),
            ("ratio_low", {"distance_triangles": 400}, "45-60 percent"),
            ("ratio_high", {"distance_triangles": 541}, "45-60 percent"),
        )
        for name, kwargs, expected in budget_cases:
            with self.subTest(case=name):
                result = self.ruby("pair", self.pair_payload(fixture(**kwargs)))
                self.assertTrue(any(expected in issue for issue in result["issues"]), result)

        def run_model_mutation(mutate: callable, expected: str) -> None:
            values = fixture()
            hero = bytearray(values["bytes"][MODEL_PATHS[1]])
            mutate(hero)
            values["bytes"][MODEL_PATHS[1]] = bytes(hero)
            refresh_entry(values, MODEL_PATHS[1])
            result = self.ruby("pair", self.pair_payload(values))
            self.assertTrue(any(expected in issue for issue in result["issues"]), result)

        clean = fixture()["bytes"][MODEL_PATHS[1]]
        object_offsets = chunk_offsets(clean, "O")
        material_offsets = chunk_offsets(clean, "M")
        vertex_offset = chunk_offsets(clean, "V")[0]

        def collapse_accent_uvs(data: bytearray) -> None:
            for vertex_index in range(8, 12):
                pair = vertex_offset + (vertex_index // 2) * 32
                uv = pair + (28 if vertex_index % 2 else 24)
                struct.pack_into(">2h", data, uv, 0, 0)

        def hide_uv_span_on_unindexed_vertex(data: bytearray) -> None:
            first_index_offset = chunk_offsets(data, "I")[0]
            first_index_count = struct.unpack_from(">H", data, object_offsets[0] + 32 + 12)[0]
            data[first_index_offset:first_index_offset + first_index_count] = (
                bytes((0, 1, 2)) * (first_index_count // 3)
            )
            for vertex_index in range(3):
                pair = vertex_offset + (vertex_index // 2) * 32
                uv = pair + (28 if vertex_index % 2 else 24)
                struct.pack_into(">2h", data, uv, 0, 0)

        def mutate_primitive_color(data: bytearray) -> None:
            data[material_offsets[0] + 0x22] = 1
            data[material_offsets[0] + 0x24:material_offsets[0] + 0x28] = b"\xFF\xFF\xFF\xFF"

        model_cases: dict[str, tuple[callable, str]] = {
            "unused_material": (
                lambda data: struct.pack_into(">I", data, object_offsets[2] + 8, 1),
                "exactly three materials and use every one",
            ),
            "unknown_body_reference": (
                lambda data: (
                    struct.pack_into(">I", data, material_offsets[1] + 0x34, 0x51554232),
                    struct.pack_into(">I", data, material_offsets[1] + 0x34 + 8, 0x51554232),
                ),
                "exact two pathless CI8 region references",
            ),
            "wrong_region_height": (
                lambda data: struct.pack_into(">H", data, material_offsets[0] + 0x34 + 18, 64),
                "dimensions/tile parameters are not canonical",
            ),
            "wrong_region_axis": (
                lambda data: struct.pack_into(">f", data, material_offsets[0] + 0x34 + 24, 62.0),
                "dimensions/tile parameters are not canonical",
            ),
            "second_active_texture": (
                lambda data: (
                    struct.pack_into(">I", data, material_offsets[0] + 0x60, 0x5155427F),
                    struct.pack_into(">I", data, material_offsets[0] + 0x60 + 8, 0x5155427F),
                    struct.pack_into(">HH", data, material_offsets[0] + 0x60 + 16, 16, 16),
                ),
                "exactly one texture",
            ),
            "blank_combiner": (
                lambda data: struct.pack_into(">Q", data, material_offsets[0], 0),
                "TEX0 x SHADE",
            ),
            "unshaded_draw_flags": (
                lambda data: struct.pack_into(">I", data, material_offsets[0] + 28, 0x03),
                "depth/textured/shaded",
            ),
            "bilinear_filter": (
                lambda data: struct.pack_into(">Q", data, material_offsets[0] + 8,
                                              0x0000200000000000),
                "point filtering",
            ),
            "texture_lod": (
                lambda data: struct.pack_into(">Q", data, material_offsets[0] + 8,
                                              0x0001000000000000),
                "point filtering",
            ),
            "unreviewed_other_mode_mask": (
                lambda data: struct.pack_into(">Q", data, material_offsets[0] + 16,
                                              QUARRUNE_OTHER_MODE_MASK | 1),
                "point filtering",
            ),
            "unknown_blend_mode": (
                lambda data: struct.pack_into(">I", data, material_offsets[0] + 24, 0xFFFFFFFF),
                "opaque blending",
            ),
            "active_fog": (
                lambda data: data.__setitem__(material_offsets[0] + 0x21, 2),
                "default fog/colors",
            ),
            "primitive_color": (
                mutate_primitive_color,
                "default fog/colors",
            ),
            "uv_out_of_region": (
                lambda data: struct.pack_into(">h", data, vertex_offset + 26, 1025),
                "packed UVs leave its region-local texture bounds",
            ),
            "negative_point_uv": (
                lambda data: struct.pack_into(">h", data, vertex_offset + 24, -1),
                "packed UVs leave its region-local texture bounds",
            ),
            "span_only_on_unindexed_vertex": (
                hide_uv_span_on_unindexed_vertex,
                "UV island is too collapsed",
            ),
            "collapsed_accent_uvs": (
                collapse_accent_uvs,
                "UV island is too collapsed",
            ),
        }
        for name, (mutate, expected) in model_cases.items():
            with self.subTest(case=name):
                run_model_mutation(mutate, expected)

    def test_sprite_content_and_runtime_binding_fail_closed_semantically(self) -> None:
        def run_sprite_mutation(path: str, mutate: callable, expected: str) -> None:
            values = fixture()
            sprite = bytearray(values["bytes"][path])
            mutate(sprite)
            values["bytes"][path] = bytes(sprite)
            refresh_entry(values, path)
            refresh_runtime_binding(values)
            result = self.ruby("pair", self.pair_payload(values))
            self.assertTrue(any(expected in issue for issue in result["issues"]), result)

        body = body_sprite()
        body_palette = ext_offset(body) + 128
        accent = accent_sprite()
        accent_ext = ext_offset(accent)
        accent_palette = accent_ext + 128
        sprite_cases: dict[str, tuple[str, callable, str]] = {
            "transparent_body_palette": (
                BODY_TEXTURE_PATH,
                lambda data: struct.pack_into(">H", data, body_palette,
                                              struct.unpack_from(">H", data, body_palette)[0] & 0xFFFE),
                "unique and opaque",
            ),
            "duplicate_body_palette": (
                BODY_TEXTURE_PATH,
                lambda data: data.__setitem__(slice(body_palette + 2, body_palette + 4),
                                              data[body_palette:body_palette + 2]),
                "unique and opaque",
            ),
            "blank_accent": (
                ACCENT_TEXTURE_PATH,
                lambda data: (
                    data.__setitem__(slice(8, accent_ext), bytes(accent_ext - 8)),
                    data.__setitem__(accent_ext + 66, 1),
                ),
                "at least 8 colors",
            ),
            "flat_accent_values": (
                ACCENT_TEXTURE_PATH,
                lambda data: [struct.pack_into(">H", data, accent_palette + index * 2,
                                                   (index << 1) | 1) for index in range(16)],
                "readable value range",
            ),
            "shadow_perimeter": (
                BLOB_SHADOW_PATH,
                lambda data: data.__setitem__(8, 15),
                "perimeter must be transparent",
            ),
            "shadow_island": (
                BLOB_SHADOW_PATH,
                lambda data: data.__setitem__(8 + 33, 15),
                "disconnected islands",
            ),
        }
        for name, (path, mutate, expected) in sprite_cases.items():
            with self.subTest(case=name):
                run_sprite_mutation(path, mutate, expected)

        binding_cases = (
            (
                "wrong_runtime_helper",
                lambda data: data.replace(
                    b"runtime_helper_bundle_sha256\tb9125d3375842e75dc4d0227abbf2158126e1b9ba684842c9f9326071c7b7853\n",
                    b"runtime_helper_bundle_sha256\t" + b"0" * 64 + b"\n",
                ),
                "runtime_helper_bundle_sha256 binding mismatch",
            ),
            (
                "wrong_rect",
                lambda data: data.replace(b"body_bottom_rect_px\t0,32,64,64\n",
                                          b"body_bottom_rect_px\t0,31,64,64\n"),
                "body_bottom_rect_px binding mismatch",
            ),
            (
                "wrong_opacity",
                lambda data: data.replace(b"base_opacity_q8\t176\n", b"base_opacity_q8\t177\n"),
                "base_opacity_q8 binding mismatch",
            ),
            (
                "key_order",
                lambda data: b"".join(
                    [data.splitlines(keepends=True)[1], data.splitlines(keepends=True)[0]]
                    + data.splitlines(keepends=True)[2:]
                ),
                "binding keys/order differ",
            ),
        )
        for name, mutate, expected in binding_cases:
            with self.subTest(case=name):
                values = fixture()
                values["bytes"][RUNTIME_BINDING_PATH] = mutate(values["bytes"][RUNTIME_BINDING_PATH])
                refresh_entry(values, RUNTIME_BINDING_PATH)
                result = self.ruby("pair", self.pair_payload(values))
                self.assertTrue(any(expected in issue for issue in result["issues"]), result)

    def test_pair_reaches_cross_file_skeleton_and_semantic_binding_checks(self) -> None:
        values = fixture()
        hero = bytearray(values["bytes"][MODEL_PATHS[1]])
        skeleton_offset = chunk_offsets(hero, "S")[0]
        struct.pack_into(">f", hero, skeleton_offset + 40, 1.0)
        values["bytes"][MODEL_PATHS[1]] = bytes(hero)
        refresh_entry(values, MODEL_PATHS[1])
        binding = binding_bytes(values["model_entries"], values["animation_entries"], values["signature"])
        values["bytes"][BINDING_PATH] = binding
        refresh_entry(values, BINDING_PATH)
        result = self.ruby("pair", self.pair_payload(values))
        self.assertTrue(any("skeleton signatures differ" in issue for issue in result["issues"]), result)

        semantic_cases: dict[str, tuple[callable, str]] = {
            "signature_field": (
                lambda data, value: data.replace(value["signature"].encode(), b"0" * 64),
                "skeleton_signature_sha256 binding mismatch",
            ),
            "build_field": (
                lambda data, _value: data.replace(
                    f"build_id\t{BUILD_ID}\n".encode(), b"build_id\tother-build\n"
                ),
                "build_id binding mismatch",
            ),
            "stream_set_field": (
                lambda data, _value: data.replace(
                    next(line for line in data.splitlines(keepends=True)
                         if line.startswith(b"animation_stream_set_sha256\t")),
                    b"animation_stream_set_sha256\t" + b"0" * 64 + b"\n",
                ),
                "animation_stream_set_sha256 binding mismatch",
            ),
            "key_order": (
                lambda data, _value: b"".join(
                    [data.splitlines(keepends=True)[1], data.splitlines(keepends=True)[0]]
                    + data.splitlines(keepends=True)[2:]
                ),
                "binding keys/order differ",
            ),
        }
        for name, (mutate, expected) in semantic_cases.items():
            with self.subTest(mutation=name):
                values = fixture()
                values["bytes"][BINDING_PATH] = mutate(values["bytes"][BINDING_PATH], values)
                refresh_entry(values, BINDING_PATH)
                result = self.ruby("pair", self.pair_payload(values))
                self.assertTrue(result["issues"], result)
                self.assertTrue(any(expected in issue for issue in result["issues"]), result["issues"])


if __name__ == "__main__":
    unittest.main()
