# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for duplicating an object.

Runs inside Blender. `main` must return a NamedTuple (or a callable for the
deferred protocol); the calling-convention footer converts it via `._asdict()`.

`Object.copy()` shares the data-block with the source, so an unlinked
duplicate needs `new_object.data = source.data.copy()` explicitly. The copy is
not part of any collection until it is linked into one, and an unlinked
object does not appear in the view layer.
"""

__all__ = (
    "Params",
    "Result",
    "main",
)

from typing import NamedTuple


class Params(NamedTuple):
    name: str
    count: int = 1
    offset: list[float] | None = None
    name_prefix: str | None = None
    linked: bool = False


class Result(NamedTuple):
    status: str
    source: str | None = None
    created: list[str] | None = None
    linked_data: bool | None = None
    message: str | None = None


def _vec3(value: list[float] | None, label: str) -> list[float] | None:
    if value is None:
        return None
    if len(value) != 3:
        raise ValueError("{:s} must have exactly 3 elements, got {:d}".format(label, len(value)))
    return [float(v) for v in value]


def main(params: Params) -> Result:
    import bpy  # pylint: disable=import-error,no-name-in-module

    try:
        count = int(params.count)
    except (TypeError, ValueError):
        return Result(status="error", message="count must be an integer, got {!r}".format(params.count))

    if count < 1:
        return Result(status="error", message="count must be at least 1, got {:d}".format(count))

    source = bpy.data.objects.get(params.name)
    if source is None:
        available = sorted(bpy.data.objects.keys())
        return Result(
            status="error",
            message="object {!r} not found. Available objects: {:s}".format(
                params.name, ", ".join(available) if available else "(none)",
            ),
        )

    try:
        offset = _vec3(params.offset, "offset") or [0.0, 0.0, 0.0]
    except ValueError as ex:
        return Result(status="error", message=str(ex))

    collections = list(source.users_collection)
    if not collections:
        return Result(
            status="error",
            message="object {!r} is not linked to any collection; a duplicate could not be placed".format(
                source.name,
            ),
        )

    base_location = [float(v) for v in source.location]
    prefix = str(params.name_prefix) if params.name_prefix else None

    created: list[str] = []
    for index in range(1, count + 1):
        new_object = source.copy()
        if not params.linked and source.data is not None:
            new_object.data = source.data.copy()

        for collection in collections:
            collection.objects.link(new_object)

        new_object.location = [base_location[i] + offset[i] * index for i in range(3)]

        if prefix is not None:
            new_object.name = "{:s}{:d}".format(prefix, index)

        created.append(new_object.name)

    view_layer = bpy.context.view_layer
    if view_layer is not None:
        view_layer.update()

    return Result(
        status="ok",
        source=source.name,
        created=created,
        linked_data=bool(params.linked),
    )
