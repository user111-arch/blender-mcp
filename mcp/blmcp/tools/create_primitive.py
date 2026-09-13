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
from blmcp.tools.create_primitive_toolcode import Params
from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error,no-name-in-module
from mcp.types import ToolAnnotations  # pylint: disable=import-error,no-name-in-module

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="Create Primitive",
            readOnlyHint=False,
        )
    )
    def create_primitive(
        primitive_type: str,
        name: str | None = None,
        size: float = 2.0,
        location: list[float] | None = None,
        rotation: list[float] | None = None,
        scale: list[float] | None = None,
    ) -> dict[str, object]:
        """
        Create a primitive mesh object in the connected Blender scene.

        *primitive_type* is one of ``"cube"``, ``"sphere"``, ``"cylinder"``,
        ``"plane"``, ``"cone"``, ``"torus"``.

        *size* is the object's principal extent in meters, applied
        consistently across types, so ``size=2.0`` yields a 2m cube, a
        2m-diameter sphere, and so on. It must be greater than zero.

        *location* and *rotation* are optional 3-element lists; rotation is
        in radians and uses the XYZ Euler mode. *scale* is an optional
        3-element list applied after creation.

        *name* is a requested object name - Blender de-duplicates collisions
        by appending ``.001``, so the response reports the name actually
        assigned. The new object is linked to the active collection.
        """
        p = Params(
            primitive_type=primitive_type,
            name=name,
            size=size,
            location=location,
            rotation=rotation,
            scale=scale,
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
