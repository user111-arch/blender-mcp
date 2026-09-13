# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

# pylint: disable=C0114  # See tool doc-string.

__all__ = (
    "register",
)

from blmcp.tools_helpers import (
    toolcode_format_call,
    toolcode_load_from_filepath,
    toolcode_wrap_with_calling_convention,
)
from blmcp.tools_helpers.connection import send_code
from blmcp.tools.setup_camera_toolcode import Params
from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error,no-name-in-module
from mcp.types import ToolAnnotations  # pylint: disable=import-error,no-name-in-module

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="Setup Camera",
            readOnlyHint=False,
        )
    )
    def setup_camera(
        location: list[float] | None = None,
        aim_at: list[float] | None = None,
        lens: float = 50.0,
        camera_name: str = "Camera",
        make_active: bool = True,
    ) -> dict[str, object]:
        """
        Position a camera, creating it when it does not exist yet.

        *location* is a 3-element list for the camera position and *aim_at* a
        3-element target point. Aiming at a point is far more reliable than
        supplying Euler angles by hand, and it is what makes a render frame the
        subject rather than the empty space beside it.

        *lens* is the focal length in millimetres; larger values are more
        telephoto and flatten the perspective, which suits product-style shots
        of a small model.

        *camera_name* selects which camera object to configure, and
        *make_active* also assigns it as the scene camera used for rendering.
        """
        p = Params(
            location=location,
            aim_at=aim_at,
            lens=lens,
            camera_name=camera_name,
            make_active=make_active,
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
