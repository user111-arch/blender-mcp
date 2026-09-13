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
from blmcp.tools.create_material_toolcode import Params
from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error,no-name-in-module
from mcp.types import ToolAnnotations  # pylint: disable=import-error,no-name-in-module

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="Create Material",
            readOnlyHint=False,
        )
    )
    def create_material(
        name: str,
        base_color: list[float] | None = None,
        roughness: float | None = None,
        metallic: float | None = None,
        assign_to: list[str] | None = None,
    ) -> dict[str, object]:
        """
        Create a material, or update it when *name* already exists.

        *base_color* is a 3 or 4 element list of RGBA values in the 0-1 range.
        The Principled BSDF is configured directly. This is the supported way to
        set an object's colour, and it avoids two pitfalls that both leave a
        model rendering uniformly white: node names are localised in the UI (so
        the shader node must be located by type, not by name), and the Material
        Output's Surface socket is not always linked on a fresh material.

        *assign_to* optionally lists object names to assign the material to. It
        is appended to each object's material slots and made the active slot.

        The material's viewport ``diffuse_color`` is kept in sync with the
        shader, so solid shading and Workbench renders show the same colour.
        """
        p = Params(
            name=name,
            base_color=base_color,
            roughness=roughness,
            metallic=metallic,
            assign_to=assign_to,
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
