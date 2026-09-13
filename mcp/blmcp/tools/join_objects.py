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
from blmcp.tools.join_objects_toolcode import Params
from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error,no-name-in-module
from mcp.types import ToolAnnotations  # pylint: disable=import-error,no-name-in-module

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="Join Objects",
            readOnlyHint=False,
            destructiveHint=True,
        )
    )
    def join_objects(
        object_names: list[str],
        name: str | None = None,
        keep_originals: bool = False,
    ) -> dict[str, object]:
        """
        Merge two or more mesh objects into a single object.

        This is the safe alternative to Blender's Join operator. The merge runs
        through ``bmesh`` at the data level, avoiding ``bpy.ops.object.join()``
        which aborts Blender with an access violation when its operator context
        is incomplete - a crash Python cannot catch.

        *object_names* lists the objects to merge, at least two of them. Their
        world transforms are baked into the geometry, and material slots from
        every source are re-mapped into one shared list, so each part keeps its
        own colour.

        *name* is the requested name for the result. Blender de-duplicates
        collisions with a ``.001`` suffix, so the response reports the name
        actually assigned.

        *keep_originals* leaves the source objects in the scene. By default they
        are deleted, along with their mesh data when nothing else uses it.
        """
        p = Params(
            object_names=object_names,
            name=name,
            keep_originals=keep_originals,
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
