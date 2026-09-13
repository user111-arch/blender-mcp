# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for setting or offsetting an object's transform.

Runs inside Blender. `main` must return a NamedTuple (or a callable for the
deferred protocol); the calling-convention footer converts it via `._asdict()`.

Rotation is always written to the XYZ Euler channels. Writing to
`rotation_euler` while `rotation_mode` is `QUATERNION` or `AXIS_ANGLE` is
silently ignored by Blender, so the object is switched to XYZ first - and the
orientation is carried across the switch via `matrix_basis`, because Blender
does not convert existing rotation channels when the mode changes.
"""

__all__ = (
    "Params",
    "Result",
    "main",
)

from typing import NamedTuple

_MODES = ("absolute", "relative")


class Params(NamedTuple):
    name: str
    location: list[float] | None = None
    rotation: list[float] | None = None
    scale: list[float] | None = None
    mode: str = "absolute"


class Result(NamedTuple):
    status: str
    name: str | None = None
    location: list[float] | None = None
    rotation: list[float] | None = None
    scale: list[float] | None = None
    dimensions: list[float] | None = None
    rotation_mode_before: str | None = None
    rotation_mode_after: str | None = None
    message: str | None = None


def _vec3(value: list[float] | None, label: str) -> list[float] | None:
    if value is None:
        return None
    if len(value) != 3:
        raise ValueError("{:s} must have exactly 3 elements, got {:d}".format(label, len(value)))
    return [float(v) for v in value]


def main(params: Params) -> Result:
    import bpy  # pylint: disable=import-error,no-name-in-module

    if params.mode not in _MODES:
        return Result(
            status="error",
            message="mode must be one of {:s}; got {!r}".format(", ".join(_MODES), params.mode),
        )

    if params.location is None and params.rotation is None and params.scale is None:
        return Result(
            status="error",
            message="at least one of location/rotation/scale is required",
        )

    obj = bpy.data.objects.get(params.name)
    if obj is None:
        available = sorted(bpy.data.objects.keys())
        return Result(
            status="error",
            message="object {!r} not found. Available objects: {:s}".format(
                params.name, ", ".join(available) if available else "(none)",
            ),
        )

    try:
        location = _vec3(params.location, "location")
        rotation = _vec3(params.rotation, "rotation")
        scale = _vec3(params.scale, "scale")
    except ValueError as ex:
        return Result(status="error", message=str(ex))

    rotation_mode_before = obj.rotation_mode

    if rotation is not None and obj.rotation_mode != 'XYZ':
        # Blender does not translate existing channels when the mode changes,
        # so capture the current orientation and re-apply it as XYZ Euler.
        preserved = obj.matrix_basis.to_quaternion()
        obj.rotation_mode = 'XYZ'
        obj.rotation_euler = preserved.to_euler('XYZ')

    relative = params.mode == "relative"

    if location is not None:
        if relative:
            obj.location = [float(obj.location[i]) + location[i] for i in range(3)]
        else:
            obj.location = location

    if rotation is not None:
        if relative:
            obj.rotation_euler = [float(obj.rotation_euler[i]) + rotation[i] for i in range(3)]
        else:
            obj.rotation_euler = rotation

    if scale is not None:
        if relative:
            obj.scale = [float(obj.scale[i]) * scale[i] for i in range(3)]
        else:
            obj.scale = scale

    view_layer = bpy.context.view_layer
    if view_layer is not None:
        view_layer.update()

    return Result(
        status="ok",
        name=obj.name,
        location=[float(v) for v in obj.location],
        rotation=[float(v) for v in obj.rotation_euler],
        scale=[float(v) for v in obj.scale],
        dimensions=[float(v) for v in obj.dimensions],
        rotation_mode_before=rotation_mode_before,
        rotation_mode_after=obj.rotation_mode,
    )
