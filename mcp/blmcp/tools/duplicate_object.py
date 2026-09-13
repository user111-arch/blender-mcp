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
from blmcp.tools.duplicate_object_toolcode import Params
from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error,no-name-in-module
from mcp.types import ToolAnnotations  # pylint: disable=import-error,no-name-in-module

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="Duplicate Object",
            readOnlyHint=False,
        )
    )
    def duplicate_object(
        name: str,
        count: int = 1,
        offset: list[float] | None = None,
        name_prefix: str | None = None,
        linked: bool = False,
    ) -> dict[str, object]:
        """
        Duplicate the object identified by *name*.

        *count* copies are created and must be at least 1. *offset* is an
        optional 3-element list: copy *i* (1-based) is placed at
        ``source.location + offset * i``, so copies spread out in a row.

        *linked* selects the duplication kind - ``False`` (default) gives each
        copy its own data-block, ``True`` shares the source's data so editing
        one geometry affects all of them.

        *name_prefix* optionally renames the copies to ``<prefix>1``,
        ``<prefix>2``, and so on. Copies are linked into every collection the
        source belongs to. Returns the names actually assigned.
        """
        p = Params(
            name=name,
            count=count,
            offset=offset,
            name_prefix=name_prefix,
            linked=linked,
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
