#!/usr/bin/env python3
"""Bind deterministic Fast64/Tiny3D material records into a Blender GLB.

Blender's generic glTF exporter preserves the project's material metadata but
does not emit the nested ``f3d_mat`` structure consumed by Tiny3D's pinned
importer. This tool adds that structure from an explicit per-material map and,
when requested, remaps an authored half of a 64x64 atlas into region-local
64x32 UV coordinates for safe CI8 split uploads.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Sequence, Tuple


SCHEMA = "n64game-tiny3d-material-map-v1"
GLB_MAGIC = b"glTF"
GLB_VERSION = 2
JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942
REFERENCE = re.compile(r"^0x[0-9A-Fa-f]{8}$")
STATIC_PNG = re.compile(r"^\.\./filesystem/[A-Za-z0-9][A-Za-z0-9._/-]*\.png$")


class MaterialBindingError(RuntimeError):
    """Raised when a GLB or material map cannot be proven safe."""


def _read_glb(path: Path) -> Tuple[MutableMapping[str, Any], bytearray]:
    data = path.read_bytes()
    if len(data) < 20 or data[:4] != GLB_MAGIC:
        raise MaterialBindingError("input is not a GLB file")
    version, declared = struct.unpack_from("<II", data, 4)
    if version != GLB_VERSION or declared != len(data):
        raise MaterialBindingError("GLB version or declared length is invalid")

    offset = 12
    chunks: List[Tuple[int, bytes]] = []
    while offset < len(data):
        if offset + 8 > len(data):
            raise MaterialBindingError("GLB has a truncated chunk header")
        length, kind = struct.unpack_from("<II", data, offset)
        offset += 8
        if length % 4 or offset + length > len(data):
            raise MaterialBindingError("GLB chunk length is invalid")
        chunks.append((kind, data[offset:offset + length]))
        offset += length
    if len(chunks) != 2 or chunks[0][0] != JSON_CHUNK or chunks[1][0] != BIN_CHUNK:
        raise MaterialBindingError("GLB must contain exactly one JSON and one BIN chunk")
    try:
        document = json.loads(chunks[0][1].rstrip(b" \t\r\n\0"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MaterialBindingError("GLB JSON is malformed") from exc
    if not isinstance(document, dict):
        raise MaterialBindingError("GLB JSON root is not an object")
    return document, bytearray(chunks[1][1])


def _read_spec(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MaterialBindingError("material map is not canonical readable JSON") from exc
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise MaterialBindingError("material map schema is invalid")
    materials = value.get("materials")
    if not isinstance(materials, dict) or not materials:
        raise MaterialBindingError("material map has no material records")
    if any(not isinstance(name, str) or not name for name in materials):
        raise MaterialBindingError("material map contains an invalid material name")
    return value


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MaterialBindingError(f"{label} is not numeric")
    result = float(value)
    if not (-1.0e9 < result < 1.0e9):
        raise MaterialBindingError(f"{label} is outside the finite contract")
    return result


def _binding_record(name: str, record: Any) -> Tuple[Mapping[str, Any], Tuple[float, float], bool]:
    if not isinstance(record, dict):
        raise MaterialBindingError(f"material {name} record is not an object")
    if set(record) != {"binding", "source_v_range", "cull_back"}:
        raise MaterialBindingError(f"material {name} record keys are not exact")
    binding = record["binding"]
    source_range = record["source_v_range"]
    cull_back = record["cull_back"]
    if not isinstance(binding, dict) or not isinstance(source_range, list) or len(source_range) != 2:
        raise MaterialBindingError(f"material {name} binding or UV range is invalid")
    if not isinstance(cull_back, bool):
        raise MaterialBindingError(f"material {name} cull_back is not boolean")
    low = _number(source_range[0], f"material {name} UV low")
    high = _number(source_range[1], f"material {name} UV high")
    if low < 0.0 or high > 1.0 or high - low < 0.01:
        raise MaterialBindingError(f"material {name} UV range is outside 0..1")
    return binding, (low, high), cull_back


def _axis(high: int) -> Dict[str, Any]:
    return {
        "low": 0.0,
        "high": float(high),
        "mask": 0,
        "shift": 0,
        "mirror": 0,
        "clamp": 1,
    }


def _texture(binding: Mapping[str, Any], label: str) -> Mapping[str, Any]:
    kind = binding.get("kind")
    if kind == "dynamic_reference":
        if set(binding) != {"kind", "reference", "width", "height"}:
            raise MaterialBindingError(f"{label} dynamic binding keys are not exact")
        reference = binding["reference"]
        if not isinstance(reference, str) or not REFERENCE.fullmatch(reference):
            raise MaterialBindingError(f"{label} dynamic reference is invalid")
        width = binding["width"]
        height = binding["height"]
        if width != 64 or height != 32:
            raise MaterialBindingError(f"{label} dynamic CI8 region must be 64x32")
        result: Dict[str, Any] = {
            "use_tex_reference": 1,
            "tex_reference": reference,
            "tex_reference_size": [width, height],
        }
    elif kind == "static_png":
        if set(binding) != {"kind", "path", "width", "height"}:
            raise MaterialBindingError(f"{label} static binding keys are not exact")
        path = binding["path"]
        width = binding["width"]
        height = binding["height"]
        if not isinstance(path, str) or not STATIC_PNG.fullmatch(path) or "//" in path:
            raise MaterialBindingError(f"{label} static PNG path is invalid")
        if (width, height) not in {(32, 32), (64, 64), (128, 64), (128, 128)}:
            raise MaterialBindingError(f"{label} static texture dimensions are unsupported")
        result = {
            "use_tex_reference": 0,
            "tex": {"name": path},
        }
    else:
        raise MaterialBindingError(f"{label} has an unknown binding kind")
    result["S"] = _axis(int(width) - 1)
    result["T"] = _axis(int(height) - 1)
    return result


def _f3d_material(binding: Mapping[str, Any], cull_back: bool, label: str) -> Mapping[str, Any]:
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
        "combiner2": combiner,
        "set_blend": 0,
        "blend_color": [0.0, 0.0, 0.0, 0.0],
        "rdp_settings": {
            "g_mdsft_cycletype": 0,
            "g_cull_back": 1 if cull_back else 0,
            "g_cull_front": 0,
            "g_fog": 0,
            "g_mdsft_text_filt": 0,
            "g_tex_gen": 0,
            "set_rendermode": 0,
        },
        "draw_layer": {"oot": 0, "sm64": 1},
        "tex0": _texture(binding, label),
    }


def _remap_uv_accessor(
    document: MutableMapping[str, Any],
    binary: bytearray,
    accessor_index: int,
    source_range: Tuple[float, float],
) -> None:
    accessors = document.get("accessors")
    views = document.get("bufferViews")
    if not isinstance(accessors, list) or not isinstance(views, list):
        raise MaterialBindingError("GLB lacks accessor tables")
    if accessor_index < 0 or accessor_index >= len(accessors):
        raise MaterialBindingError("TEXCOORD_0 accessor index is invalid")
    accessor = accessors[accessor_index]
    if not isinstance(accessor, dict) or accessor.get("componentType") != 5126 or accessor.get("type") != "VEC2":
        raise MaterialBindingError("TEXCOORD_0 must be float VEC2")
    if accessor.get("sparse") is not None or accessor.get("normalized") not in {None, False}:
        raise MaterialBindingError("sparse or normalized TEXCOORD_0 is unsupported")
    count = accessor.get("count")
    view_index = accessor.get("bufferView")
    if not isinstance(count, int) or count <= 0 or not isinstance(view_index, int):
        raise MaterialBindingError("TEXCOORD_0 count or view is invalid")
    if view_index < 0 or view_index >= len(views):
        raise MaterialBindingError("TEXCOORD_0 buffer view index is invalid")
    view = views[view_index]
    if not isinstance(view, dict) or view.get("buffer", 0) != 0:
        raise MaterialBindingError("TEXCOORD_0 must use GLB buffer zero")
    stride = view.get("byteStride", 8)
    if not isinstance(stride, int) or stride < 8 or stride % 4:
        raise MaterialBindingError("TEXCOORD_0 byte stride is invalid")
    view_offset = view.get("byteOffset", 0)
    accessor_offset = accessor.get("byteOffset", 0)
    view_length = view.get("byteLength")
    if not all(isinstance(value, int) and value >= 0 for value in (view_offset, accessor_offset)):
        raise MaterialBindingError("TEXCOORD_0 byte offset is invalid")
    if not isinstance(view_length, int) or view_length <= 0:
        raise MaterialBindingError("TEXCOORD_0 view length is invalid")
    start = view_offset + accessor_offset
    end = start + (count - 1) * stride + 8
    if end > view_offset + view_length or end > len(binary):
        raise MaterialBindingError("TEXCOORD_0 bytes leave their buffer view")

    low, high = source_range
    epsilon = 1.0e-5
    minimum_u = float("inf")
    maximum_u = float("-inf")
    minimum_v = float("inf")
    maximum_v = float("-inf")
    for index in range(count):
        offset = start + index * stride
        u, v = struct.unpack_from("<ff", binary, offset)
        if not (-epsilon <= u <= 1.0 + epsilon and low - epsilon <= v <= high + epsilon):
            raise MaterialBindingError(
                f"TEXCOORD_0 accessor {accessor_index} leaves its declared atlas region"
            )
        local_v = (v - low) / (high - low)
        local_v = min(1.0, max(0.0, local_v))
        u = min(1.0, max(0.0, u))
        struct.pack_into("<ff", binary, offset, u, local_v)
        minimum_u = min(minimum_u, u)
        maximum_u = max(maximum_u, u)
        minimum_v = min(minimum_v, local_v)
        maximum_v = max(maximum_v, local_v)
    accessor["min"] = [minimum_u, minimum_v]
    accessor["max"] = [maximum_u, maximum_v]


def bind_materials(
    document: MutableMapping[str, Any],
    binary: bytearray,
    spec: Mapping[str, Any],
) -> None:
    materials = document.get("materials")
    meshes = document.get("meshes")
    if not isinstance(materials, list) or not materials or not isinstance(meshes, list):
        raise MaterialBindingError("GLB has no materials or meshes")
    names: List[str] = []
    for material in materials:
        if not isinstance(material, dict) or not isinstance(material.get("name"), str):
            raise MaterialBindingError("GLB material name is missing")
        names.append(material["name"])
    if len(names) != len(set(names)):
        raise MaterialBindingError("GLB material names are not unique")
    spec_materials = spec["materials"]
    if set(names) != set(spec_materials):
        raise MaterialBindingError("material map does not exactly cover the GLB materials")

    records: Dict[int, Tuple[Mapping[str, Any], Tuple[float, float], bool]] = {}
    by_name = {name: index for index, name in enumerate(names)}
    for name, record in spec_materials.items():
        records[by_name[name]] = _binding_record(name, record)

    accessor_ranges: Dict[int, Tuple[float, float]] = {}
    used_materials = set()
    for mesh in meshes:
        if not isinstance(mesh, dict) or not isinstance(mesh.get("primitives"), list):
            raise MaterialBindingError("GLB mesh primitives are invalid")
        for primitive in mesh["primitives"]:
            if not isinstance(primitive, dict) or primitive.get("mode", 4) != 4:
                raise MaterialBindingError("only triangle-list primitives are supported")
            material_index = primitive.get("material")
            attributes = primitive.get("attributes")
            if not isinstance(material_index, int) or material_index not in records:
                raise MaterialBindingError("primitive material index is invalid")
            if not isinstance(attributes, dict) or not isinstance(attributes.get("TEXCOORD_0"), int):
                raise MaterialBindingError("textured primitive lacks TEXCOORD_0")
            accessor_index = attributes["TEXCOORD_0"]
            source_range = records[material_index][1]
            prior = accessor_ranges.get(accessor_index)
            if prior is not None and prior != source_range:
                raise MaterialBindingError("one TEXCOORD_0 accessor has conflicting atlas regions")
            accessor_ranges[accessor_index] = source_range
            used_materials.add(material_index)
    if used_materials != set(records):
        raise MaterialBindingError("one or more mapped materials are unused")

    for accessor_index, source_range in sorted(accessor_ranges.items()):
        _remap_uv_accessor(document, binary, accessor_index, source_range)

    for index, material in enumerate(materials):
        binding, _source_range, cull_back = records[index]
        extras = material.get("extras")
        if extras is None:
            extras = {}
            material["extras"] = extras
        if not isinstance(extras, dict):
            raise MaterialBindingError(f"material {names[index]} extras are invalid")
        extras["f3d_mat"] = _f3d_material(binding, cull_back, names[index])


def _write_glb(path: Path, document: Mapping[str, Any], binary: bytes) -> None:
    json_bytes = json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    json_bytes += b" " * ((-len(json_bytes)) % 4)
    binary += b"\0" * ((-len(binary)) % 4)
    output = bytearray(GLB_MAGIC + struct.pack("<II", GLB_VERSION, 0))
    output.extend(struct.pack("<II", len(json_bytes), JSON_CHUNK))
    output.extend(json_bytes)
    output.extend(struct.pack("<II", len(binary), BIN_CHUNK))
    output.extend(binary)
    struct.pack_into("<I", output, 8, len(output))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(output)


def run(input_path: Path, spec_path: Path, output_path: Path) -> None:
    if input_path.resolve() == output_path.resolve():
        raise MaterialBindingError("input and output GLB paths must differ")
    document, binary = _read_glb(input_path)
    bind_materials(document, binary, _read_spec(spec_path))
    _write_glb(output_path, document, bytes(binary))


def main(argv: Sequence[str] = ()) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_glb", type=Path)
    parser.add_argument("material_map", type=Path)
    parser.add_argument("output_glb", type=Path)
    arguments = parser.parse_args(list(argv) if argv else None)
    try:
        run(arguments.input_glb, arguments.material_map, arguments.output_glb)
    except (OSError, MaterialBindingError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
