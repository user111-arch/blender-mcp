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
from blmcp.tools.delete_objects_toolcode import Params
from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error,no-name-in-module
from mcp.types import ToolAnnotations  # pylint: disable=import-error,no-name-in-module

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="Delete Objects",
            readOnlyHint=False,
            destructiveHint=True,
        )
    )
    def delete_objects(
        names: list[str],
        purge_data: bool = False,
    ) -> dict[str, object]:
        """
        Delete the objects named in *names*, unlinking them from every
        collection they belong to.

        Deleting objects leaves their data-blocks (meshes, materials, and so
        on) behind until those lose all users. Set *purge_data* to additionally
        remove the orphaned mesh / curve / material / camera / light / armature
        data-blocks in the same call.

        Returns the names that were deleted and the names that did not exist.
        The deletion itself cannot be undone from this tool.
        """
        p = Params(
            names=names,
            purge_data=purge_data,
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
