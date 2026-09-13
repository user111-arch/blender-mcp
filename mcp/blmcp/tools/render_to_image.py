# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

# pylint: disable=C0114  # See tool doc-string.

__all__ = (
    "register",
)

import base64

from blmcp.tools_helpers import (
    toolcode_format_call,
    toolcode_load_from_filepath,
    toolcode_wrap_with_calling_convention,
)
from blmcp.tools_helpers.connection import send_code
from blmcp.tools.render_to_image_toolcode import Params
from mcp.server.fastmcp import FastMCP, Image  # pylint: disable=import-error,no-name-in-module
from mcp.types import ToolAnnotations  # pylint: disable=import-error,no-name-in-module

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="Render To Image",
            readOnlyHint=True,
        )
    )
    def render_to_image(
        resolution_x: int = 0,
        resolution_y: int = 0,
        size_limit_in_bytes: int = 0,
    ) -> Image:
        """
        Render the current scene and return the result as a PNG image.

        ``render_viewport_to_path`` only hands back a path inside Blender's
        scratch directory, which is useless to a client that cannot read that
        filesystem. This returns the image itself so the render can actually be
        looked at.

        *resolution_x* and *resolution_y* optionally override the scene
        resolution for this render only, and are restored afterwards. Zero (the
        default) keeps the current setting.

        *size_limit_in_bytes* caps the returned image size; zero (the default)
        uses the MCP message size limit and downscales the image if needed.

        The render uses the scene's current engine, camera and settings. Scene
        data is not modified, but a temporary PNG is written to Blender's
        scratch directory.
        """
        p = Params(
            resolution_x=resolution_x,
            resolution_y=resolution_y,
            size_limit_in_bytes=size_limit_in_bytes,
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        response = send_code(code, strict_json=True)
        if response.get("status") != "ok":
            raise RuntimeError(str(response.get("message", "Unknown error")))
        result = response["result"]
        assert isinstance(result, dict)
        if result.get("status") != "ok":
            raise RuntimeError(str(result.get("message", "Unknown error")))
        return Image(data=base64.b64decode(str(result["image_base64"])), format="png")
