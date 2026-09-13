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
from blmcp.tools.export_scene_toolcode import Params
from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error,no-name-in-module
from mcp.types import ToolAnnotations  # pylint: disable=import-error,no-name-in-module

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="Export Scene",
            readOnlyHint=True,
        )
    )
    def export_scene(
        filename: str,
        export_format: str = "glb",
        selected_only: bool = False,
    ) -> dict[str, object]:
        """
        Export scene geometry to a file for use outside Blender.

        *export_format* is one of ``"glb"``, ``"gltf"``, ``"obj"``, ``"fbx"``,
        ``"stl"``. ``glb`` is the safest choice for handing a model to another
        tool, since it carries meshes and materials in a single file.

        *filename* is the name to write. As with the render tools it is resolved
        inside Blender's scratch directory, so the exported file has to be
        copied from there. Accepting an arbitrary path would make this an
        arbitrary-file-write primitive.

        *selected_only* exports just the selected objects rather than the whole
        scene. The response reports the resulting path and its size.

        Scene data is not modified; the tool only writes a file.
        """
        p = Params(
            filename=filename,
            export_format=export_format,
            selected_only=selected_only,
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
