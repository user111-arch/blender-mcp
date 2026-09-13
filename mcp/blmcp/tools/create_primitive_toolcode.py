# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for creating a primitive mesh object.

Runs inside Blender. `main` must return a NamedTuple (or a callable for the
deferred protocol); the calling-convention footer converts it via `._asdict()`.

The new object is captured by diffing `bpy.data.objects` before and after the
operator call rather than by looking up a guessed name, because Blender
silently de-duplicates colliding names with a `.001` suffix.
"""

__all__ = (
    "Params",
    "Result",
    "main",
)

from typing import NamedTuple

_PRIMITIVE_TYPES = ("cube", "sphere", "cylinder", "plane", "cone", "torus")


class Params(NamedTuple):
    primitive_type: str
    name: str | None = None
    size: float = 2.0
    location: list[float] | None = None
    rotation: list[float] | None = None
    scale: list[float] | None = None


class Result(NamedTuple):
    status: str
    name: str | None = None
    type: str | None = None
    data_name: str | None = None
    location: list[float] | None = None
    rotation: list[float] | None = None
    scale: list[float] | None = None
    dimensions: list[float] | None = None
    vertex_count: int | None = None
    message: str | None = None


def _vec3(value: list[float] | None, label: str) -> list[float] | None:
    if value is None:
        return None
    if len(value) != 3:
        raise ValueError("{:s} must have exactly 3 elements, got {:d}".format(label, len(value)))
    return [float(v) for v in value]


def _add_primitive(primitive_type: str, size: float, location, rotation) -> None:
    import bpy  # pylint: disable=import-error,no-name-in-module

    ops = bpy.ops.mesh
    if primitive_type == "cube":
        ops.primitive_cube_add(size=size, location=location, rotation=rotation)
    elif primitive_type == "plane":
        ops.primitive_plane_add(size=size, location=location, rotation=rotation)
    elif primitive_type == "sphere":
        ops.primitive_uv_sphere_add(radius=size * 0.5, location=location, rotation=rotation)
    elif primitive_type == "cylinder":
        ops.primitive_cylinder_add(radius=size * 0.5, depth=size, location=location, rotation=rotation)
    elif primitive_type == "cone":
        ops.primitive_cone_add(radius1=size * 0.5, depth=size, location=location, rotation=rotation)
    elif primitive_type == "torus":
        # major + minor radii are chosen so the outer diameter equals *size*.
        ops.primitive_torus_add(
            major_radius=size * 0.4,
            minor_radius=size * 0.1,
            location=location,
            rotation=rotation,
        )
    else:
        raise ValueError("unsupported primitive type: {!r}".format(primitive_type))


def main(params: Params) -> Result:
    import bpy  # pylint: disable=import-error,no-name-in-module

    primitive_type = str(params.primitive_type).lower()
    if primitive_type not in _PRIMITIVE_TYPES:
        return Result(
            status="error",
            message="primitive_type must be one of {:s}; got {!r}".format(
                ", ".join(_PRIMITIVE_TYPES), params.primitive_type,
            ),
        )

    try:
        size = float(params.size)
    except (TypeError, ValueError):
        return Result(status="error", message="size must be a number, got {!r}".format(params.size))

    if not size > 0.0:
        return Result(status="error", message="size must be greater than 0, got {!r}".format(params.size))

    try:
        location = _vec3(params.location, "location")
        rotation = _vec3(params.rotation, "rotation")
        scale = _vec3(params.scale, "scale")
    except ValueError as ex:
        return Result(status="error", message=str(ex))

    before = set(bpy.data.objects.keys())

    try:
        _add_primitive(
            primitive_type,
            size,
            tuple(location) if location is not None else (0.0, 0.0, 0.0),
            tuple(rotation) if rotation is not None else (0.0, 0.0, 0.0),
        )
    except RuntimeError as ex:
        return Result(
            status="error",
            message="Blender refused to add the primitive ({:s}): {:s}".format(
                primitive_type, str(ex),
            ),
        )

    created = [key for key in bpy.data.objects.keys() if key not in before]
    if len(created) != 1:
        return Result(
            status="error",
            message="expected exactly one new object, found {:d}: {:s}".format(
                len(created), ", ".join(created) if created else "(none)",
            ),
        )

    obj = bpy.data.objects[created[0]]

    if params.name:
        obj.name = str(params.name)
    if scale is not None:
        obj.scale = scale

    view_layer = bpy.context.view_layer
    if view_layer is not None:
        view_layer.update()

    return Result(
        status="ok",
        name=obj.name,
        type=obj.type,
        data_name=obj.data.name if obj.data is not None else None,
        location=[float(v) for v in obj.location],
        rotation=[float(v) for v in obj.rotation_euler],
        scale=[float(v) for v in obj.scale],
        dimensions=[float(v) for v in obj.dimensions],
        vertex_count=len(obj.data.vertices) if obj.type == 'MESH' and obj.data is not None else None,
    )
