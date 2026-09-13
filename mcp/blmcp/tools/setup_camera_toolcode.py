# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for positioning a camera.

Runs inside Blender. `main` must return a NamedTuple (or a callable for the
deferred protocol); the calling-convention footer converts it via `._asdict()`.

Aiming is done by building the rotation from a direction vector rather than by
setting Euler angles, so the caller can point the camera at a target without
doing trigonometry.
"""

__all__ = (
    "Params",
    "Result",
    "main",
)

from typing import NamedTuple


class Params(NamedTuple):
    location: list[float] | None = None
    aim_at: list[float] | None = None
    lens: float = 50.0
    camera_name: str = "Camera"
    make_active: bool = True


class Result(NamedTuple):
    status: str
    camera: str | None = None
    location: list[float] | None = None
    rotation: list[float] | None = None
    lens: float | None = None
    is_active: bool | None = None
    created: bool | None = None
    message: str | None = None


def _vec3(value: list[float] | None, label: str) -> list[float] | None:
    if value is None:
        return None
    if len(value) != 3:
        raise ValueError("{:s} must have exactly 3 elements".format(label))
    return [float(v) for v in value]


def main(params: Params) -> Result:
    import bpy  # pylint: disable=import-error,no-name-in-module
    from mathutils import Vector  # pylint: disable=import-error,no-name-in-module

    if params.lens <= 0.0:
        return Result(status="error", message="lens must be greater than zero")

    try:
        location = _vec3(params.location, "location")
        aim_at = _vec3(params.aim_at, "aim_at")
    except ValueError as ex:
        return Result(status="error", message=str(ex))

    name = (params.camera_name or "").strip() or "Camera"
    obj = bpy.data.objects.get(name)

    created = obj is None
    if obj is None:
        camera_data = bpy.data.cameras.new(name)
        obj = bpy.data.objects.new(name, camera_data)
        bpy.context.collection.objects.link(obj)
    elif obj.type != 'CAMERA':
        return Result(status="error", message="Object {!r} exists and is not a camera".format(name))

    if location is not None:
        obj.location = location

    if aim_at is not None:
        direction = Vector(aim_at) - Vector(obj.location)
        if direction.length_squared > 0.0:
            obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    obj.data.lens = float(params.lens)

    if params.make_active:
        bpy.context.scene.camera = obj

    return Result(
        status="ok",
        camera=obj.name,
        location=[round(float(v), 4) for v in obj.location],
        rotation=[round(float(v), 4) for v in obj.rotation_euler],
        lens=round(float(obj.data.lens), 4),
        is_active=bpy.context.scene.camera == obj,
        created=created,
        message=("Camera created" if created else "Camera updated"),
    )
