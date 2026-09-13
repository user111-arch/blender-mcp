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
from blmcp.tools.add_light_toolcode import Params
from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error,no-name-in-module
from mcp.types import ToolAnnotations  # pylint: disable=import-error,no-name-in-module

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="Add Light",
            readOnlyHint=False,
        )
    )
    def add_light(
        name: str | None = None,
        light_type: str = "AREA",
        energy: float = 100.0,
        size: float = 1.0,
        location: list[float] | None = None,
        aim_at: list[float] | None = None,
        color: list[float] | None = None,
    ) -> dict[str, object]:
        """
        Add a light, or update the existing light with the same *name*.

        *light_type* is one of ``"AREA"``, ``"POINT"``, ``"SUN"``, ``"SPOT"``.

        *energy* is in watts for point/area/spot lights and irradiance for sun
        lights. Cartoon-style scenes usually want tens of watts for a soft key
        rather than hundreds, which blow the colours out to white.

        *size* is the radius of an area light, or the cone angle for a spot.

        *location* is a 3-element list. *aim_at* is an optional 3-element target
        point; when given, the light is rotated to point at it, which is usually
        what you want instead of guessing Euler angles.

        *color* is an optional 3 or 4 element RGB(A) list in the 0-1 range.
        """
        p = Params(
            name=name,
            light_type=light_type,
            energy=energy,
            size=size,
            location=location,
            aim_at=aim_at,
            color=color,
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
