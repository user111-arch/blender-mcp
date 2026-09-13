# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for rendering the scene and returning the image inline.

Runs inside Blender. `main` returns a NamedTuple, or a callable for the deferred
protocol (the calling-convention footer converts the final dict via `._asdict()`
only for the NamedTuple form, so the deferred path returns plain dicts).

Rendering in the interactive session is asynchronous: the operator is invoked
with `INVOKE_DEFAULT` and completes over following timer ticks, so Blender's main
thread is not blocked. The result is therefore produced by a deferred checker
rather than by `main` itself.

The output path is confined to Blender's scratch directory on purpose. That
mirrors the existing render tools: letting a caller name an arbitrary path would
turn every render into an arbitrary-file-write primitive.
"""

__all__ = (
    "Params",
    "Result",
    "main",
)

import base64
import os
from collections.abc import Callable
from typing import NamedTuple

# MCP messages are limited to 1,048,576 bytes and base64 expands by 4/3, so
# reserve 2 KiB of headroom for the JSON envelope.
_IMAGE_SIZE_LIMIT_IN_BYTES = ((1_048_576 - 2048) * 3) // 4


class Params(NamedTuple):
    resolution_x: int = 0
    resolution_y: int = 0
    size_limit_in_bytes: int = 0


class Result(NamedTuple):
    status: str
    image_base64: str | None = None
    filepath: str | None = None
    message: str | None = None


# @include_begin: _template_image_downscale_to_size_limit.py
def _image_downscale_to_size_limit(
        tmpdir: str, filepath: str, size_limit_in_bytes: int, size_tolerance_in_bytes: int = 0,
) -> bytes:
    return b''
# @include_end

# @include_begin: _template_deferred_tool_check_for_file_output.py
def _deferred_tool_check_for_file_output(
        job_type: str,
        output_path: str,
        restore_attrs: list[tuple[object, str, object]] | None = None,
) -> Callable[[], dict[str, object] | None]:
    return lambda: None
# @include_end


def _scratch_path(filename: str) -> str:
    """
    Resolve *filename* inside the MCP scratch directory, creating it if needed.
    """
    import bpy  # pylint: disable=import-error,no-name-in-module

    out_dir = os.path.join(bpy.app.tempdir, "blender_mcp")
    os.makedirs(out_dir, exist_ok=True)
    return os.path.join(out_dir, os.path.basename(filename))


def main(params: Params) -> Result | Callable[[], dict[str, object] | None]:
    import bpy  # pylint: disable=import-error,no-name-in-module

    output_path = _scratch_path("render_to_image.png")
    out_dir = os.path.dirname(output_path)

    scene = bpy.context.scene
    rd = scene.render

    # `filepath` is assigned directly rather than through a context manager:
    # `write_still` reads it after the render finishes, and a context manager
    # would restore it too early.
    orig_filepath = rd.filepath
    orig_x = rd.resolution_x
    orig_y = rd.resolution_y
    rd.filepath = output_path
    if params.resolution_x > 0:
        rd.resolution_x = params.resolution_x
    if params.resolution_y > 0:
        rd.resolution_y = params.resolution_y

    use_deferred = not bpy.app.background
    render_args = ('INVOKE_DEFAULT',) if use_deferred else ()
    try:
        bpy.ops.render.render(*render_args, write_still=True)
    except RuntimeError as ex:
        rd.filepath = orig_filepath
        rd.resolution_x = orig_x
        rd.resolution_y = orig_y
        return Result(status="error", message=str(ex))

    size_limit = params.size_limit_in_bytes if params.size_limit_in_bytes > 0 else _IMAGE_SIZE_LIMIT_IN_BYTES
    checker = _deferred_tool_check_for_file_output(
        'RENDER',
        output_path,
        restore_attrs=[
            (rd, "filepath", orig_filepath),
            (rd, "resolution_x", orig_x),
            (rd, "resolution_y", orig_y),
        ],
    )

    def encode() -> dict[str, object]:
        data = _image_downscale_to_size_limit(
            out_dir, output_path,
            size_limit_in_bytes=size_limit,
            size_tolerance_in_bytes=size_limit // 16,
        )
        return {
            "status": "ok",
            "image_base64": base64.b64encode(data).decode("ascii"),
            "filepath": output_path,
        }

    def check_is_finished() -> dict[str, object] | None:
        done = checker()
        if done is None:
            # Still rendering.
            return None
        if done.get("status") != "ok":
            return done
        return encode()

    if use_deferred:
        return check_is_finished

    # Background mode renders synchronously, so the file is already complete.
    finished = check_is_finished()
    if finished is None:
        return Result(status="error", message="Render did not complete")
    if finished.get("status") != "ok":
        return Result(status="error", message=str(finished.get("message", "Unknown error")))
    return Result(
        status="ok",
        image_base64=str(finished["image_base64"]),
        filepath=str(finished["filepath"]),
    )
