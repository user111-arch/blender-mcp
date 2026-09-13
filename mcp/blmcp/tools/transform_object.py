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
from blmcp.tools.transform_object_toolcode import Params
from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error,no-name-in-module
from mcp.types import ToolAnnotations  # pylint: disable=import-error,no-name-in-module

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="Transform Object",
            readOnlyHint=False,
        )
    )
    def transform_object(
        name: str,
        location: list[float] | None = None,
        rotation: list[float] | None = None,
        scale: list[float] | None = None,
        mode: str = "absolute",
    ) -> dict[str, object]:
        """
        Set or offset the transform of the object identified by *name*.

        *mode* is either ``"absolute"`` (assign the given values) or
        ``"relative"`` (location and rotation are added, scale is
        multiplied). At least one of location/rotation/scale is required.

        Vectors are 3-element lists. Rotation is in radians and is written to
        the XYZ Euler channels. If the object uses a different rotation mode
        it is switched to XYZ so the write actually takes effect - the
        existing orientation is preserved across the switch, and the response
        reports ``rotation_mode_before``/``rotation_mode_after`` so the change
        is never silent.

        Returns the resulting location, rotation, scale and dimensions.
        """
        p = Params(
            name=name,
            location=location,
            rotation=rotation,
            scale=scale,
            mode=mode,
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
