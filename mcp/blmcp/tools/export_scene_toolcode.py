# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for exporting scene geometry.

Runs inside Blender. `main` must return a NamedTuple (or a callable for the
deferred protocol); the calling-convention footer converts it via `._asdict()`.

The destination is confined to Blender's scratch directory, matching the render
tools. Letting the caller choose an arbitrary path would turn every export into
a write-anywhere primitive, which matters because the add-on cannot tell a
legitimate caller from a hostile one.

Export operators are addressed defensively: their names and keyword arguments
have moved between Blender versions, so failures are reported instead of
crashing the tool.
"""

__all__ = (
    "Params",
    "Result",
    "main",
)

import os
from typing import NamedTuple

_FORMATS = ("glb", "gltf", "obj", "fbx", "stl")


class Params(NamedTuple):
    filename: str
    export_format: str = "glb"
    selected_only: bool = False


class Result(NamedTuple):
    status: str
    filepath: str | None = None
    export_format: str | None = None
    object_count: int | None = None
    bytes_written: int | None = None
    message: str | None = None


def _run_export(fmt: str, filepath: str, selected_only: bool) -> None:
    """
    Invoke the exporter for *fmt*, raising on unsupported formats.
    """
    import bpy  # pylint: disable=import-error,no-name-in-module

    if fmt in ("glb", "gltf"):
        export_format = "GLB" if fmt == "glb" else "GLTF_SEPARATE"
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            export_format=export_format,
            use_selection=selected_only,
        )
    elif fmt == "obj":
        bpy.ops.wm.obj_export(filepath=filepath, export_selected_objects=selected_only)
    elif fmt == "fbx":
        bpy.ops.export_scene.fbx(filepath=filepath, use_selection=selected_only)
    elif fmt == "stl":
        bpy.ops.wm.stl_export(filepath=filepath, export_selected_objects=selected_only)


def main(params: Params) -> Result:
    import bpy  # pylint: disable=import-error,no-name-in-module

    fmt = params.export_format.strip().lower()
    if fmt not in _FORMATS:
        return Result(status="error", message="export_format must be one of " + ", ".join(_FORMATS))

    # Strip any directory part: the destination is always the scratch directory.
    filename = os.path.basename(params.filename.strip())
    if not filename:
        return Result(status="error", message="filename must not be empty")

    out_dir = os.path.join(bpy.app.tempdir, "blender_mcp")
    os.makedirs(out_dir, exist_ok=True)
    filepath = os.path.join(out_dir, filename)

    try:
        _run_export(fmt, filepath, bool(params.selected_only))
    except (RuntimeError, AttributeError, TypeError) as ex:
        return Result(status="error", message="Export failed: {:s}".format(str(ex)))

    if not os.path.exists(filepath):
        return Result(status="error", message="Exporter reported success but wrote no file")

    return Result(
        status="ok",
        filepath=filepath,
        export_format=fmt,
        object_count=len(bpy.context.scene.objects),
        bytes_written=os.path.getsize(filepath),
        message="Written to Blender's scratch directory",
    )
