# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for deleting objects by name.

Runs inside Blender. `main` must return a NamedTuple (or a callable for the
deferred protocol); the calling-convention footer converts it via `._asdict()`.

Objects and their data are separate datablocks: removing an object does not
free its mesh/material, which becomes orphaned until its user count drops to
zero. `purge_data` performs that cleanup explicitly.
"""

__all__ = (
    "Params",
    "Result",
    "main",
)

from typing import NamedTuple

# Data-block collections scanned by `purge_data`. `collections` is deliberately
# excluded: an empty collection is a legitimate organisational container.
_PURGE_COLLECTIONS = ("meshes", "curves", "materials", "cameras", "lights", "armatures")


class Params(NamedTuple):
    names: list[str]
    purge_data: bool = False


class Result(NamedTuple):
    status: str
    deleted: list[str] | None = None
    not_found: list[str] | None = None
    purged_datablocks: int | None = None
    message: str | None = None


def main(params: Params) -> Result:
    import bpy  # pylint: disable=import-error,no-name-in-module

    names = [str(name) for name in (params.names or [])]
    if not names:
        return Result(status="error", message="names must contain at least one object name")

    deleted: list[str] = []
    not_found: list[str] = []

    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is None:
            not_found.append(name)
            continue
        actual_name = obj.name
        bpy.data.objects.remove(obj, do_unlink=True)
        deleted.append(actual_name)

    purged: int | None = None
    if params.purge_data:
        purged = 0
        for attr in _PURGE_COLLECTIONS:
            datablocks = getattr(bpy.data, attr, None)
            if datablocks is None:
                continue
            for datablock in list(datablocks):
                if datablock.users == 0:
                    datablocks.remove(datablock)
                    purged += 1

    view_layer = bpy.context.view_layer
    if view_layer is not None:
        view_layer.update()

    if not deleted:
        return Result(
            status="error",
            deleted=deleted,
            not_found=not_found,
            purged_datablocks=purged,
            message="none of the requested objects exist",
        )

    return Result(
        status="ok",
        deleted=deleted,
        not_found=not_found,
        purged_datablocks=purged,
    )
