# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for adding or updating a light.

Runs inside Blender. `main` must return a NamedTuple (or a callable for the
deferred protocol); the calling-convention footer converts it via `._asdict()`.

Lights are matched by object name and updated in place when one already exists,
so calling this twice with the same name tweaks a light instead of stacking a
second one on top of it.
"""

__all__ = (
    "Params",
    "Result",
    "main",
)

from typing import NamedTuple

_LIGHT_TYPES = ("AREA", "POINT", "SUN", "SPOT")


class Params(NamedTuple):
    name: str | None = None
    light_type: str = "AREA"
    energy: float = 100.0
    size: float = 1.0
    location: list[float] | None = None
    aim_at: list[float] | None = None
    color: list[float] | None = None


class Result(NamedTuple):
    status: str
    name: str | None = None
    light_type: str | None = None
    energy: float | None = None
    size: float | None = None
    location: list[float] | None = None
    rotation: list[float] | None = None
    created: bool | None = None
    message: str | None = None


def _vec3(value: list[float] | None, label: str) -> list[float] | None:
    if value is None:
        return None
    if len(value) != 3:
        raise ValueError("{:s} must have exactly 3 elements".format(label))
    return [float(v) for v in value]


def _color4(value: list[float] | None) -> list[float] | None:
    if value is None:
        return None
    if len(value) not in (3, 4):
        raise ValueError("color must have 3 or 4 elements")
    out = [float(v) for v in value]
    if len(out) == 3:
        out.append(1.0)
    return out


def main(params: Params) -> Result:
    import bpy  # pylint: disable=import-error,no-name-in-module
    from mathutils import Vector  # pylint: disable=import-error,no-name-in-module

    light_type = params.light_type.upper()
    if light_type not in _LIGHT_TYPES:
        return Result(status="error", message="light_type must be one of " + ", ".join(_LIGHT_TYPES))
    if params.energy < 0.0:
        return Result(status="error", message="energy must not be negative")

    try:
        location = _vec3(params.location, "location")
        aim_at = _vec3(params.aim_at, "aim_at")
        color = _color4(params.color)
    except ValueError as ex:
        return Result(status="error", message=str(ex))

    name = (params.name or "").strip() or (light_type.capitalize() + "Light")
    obj = bpy.data.objects.get(name)

    created = obj is None
    if obj is None:
        light_data = bpy.data.lights.new(name, type=light_type)
        obj = bpy.data.objects.new(name, light_data)
        bpy.context.collection.objects.link(obj)
    elif obj.type != 'LIGHT':
        return Result(status="error", message="Object {!r} exists and is not a light".format(name))
    else:
        # Changing the type of an existing light is not possible, so replace the
        # data-block when the caller asks for a different type.
        if obj.data.type != light_type:
            obj.data = bpy.data.lights.new(name, type=light_type)

    light = obj.data
    light.energy = float(params.energy)
    # `size` means radius for area lights and cone angle for spots; other types
    # ignore it, so only set it where it has a meaning.
    if light_type == 'AREA':
        light.size = float(params.size)
    elif light_type == 'SPOT':
        light.spot_size = float(params.size)
    if color is not None:
        light.color = color[:3]

    if location is not None:
        obj.location = location
    elif created:
        # Give a sane default rather than leaving it at the world origin, where
        # it would sit inside the model.
        obj.location = (2.0, -2.0, 3.0)

    if aim_at is not None:
        direction = Vector(aim_at) - Vector(obj.location)
        if direction.length_squared > 0.0:
            obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    return Result(
        status="ok",
        name=obj.name,
        light_type=light.type,
        energy=round(float(light.energy), 4),
        size=round(float(light.size if light_type == 'AREA' else light.spot_size), 4),
        location=[round(float(v), 4) for v in obj.location],
        rotation=[round(float(v), 4) for v in obj.rotation_euler],
        created=created,
        message=("Light created" if created else "Light updated"),
    )
