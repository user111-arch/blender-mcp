# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for merging mesh objects into one.

Runs inside Blender. `main` must return a NamedTuple (or a callable for the
deferred protocol); the calling-convention footer converts it via `._asdict()`.

The merge is done with `bmesh` on mesh data, NOT with `bpy.ops.object.join()`.
That operator dereferences operator-context fields without a null check and
therefore aborts Blender with EXCEPTION_ACCESS_VIOLATION when invoked under a
partial `temp_override`. Nothing in Python can catch that, so the data-level
path is used instead of trying to build an operator context.

Source objects are only deleted once the merged mesh has been built, so a
failure part-way through leaves the scene untouched.
"""

__all__ = (
    "Params",
    "Result",
    "main",
)

from typing import NamedTuple


class Params(NamedTuple):
    object_names: list[str]
    name: str | None = None
    keep_originals: bool = False


class Result(NamedTuple):
    status: str
    name: str | None = None
    source_objects: list[str] | None = None
    vertex_count: int | None = None
    polygon_count: int | None = None
    materials: list[str] | None = None
    message: str | None = None


def _collect(object_names: list[str]) -> tuple[list[object], str | None]:
    """
    Resolve names to mesh objects, returning an error message on failure.
    """
    import bpy  # pylint: disable=import-error,no-name-in-module

    objects: list[object] = []
    missing: list[str] = []
    for object_name in object_names:
        obj = bpy.data.objects.get(object_name)
        if obj is None:
            missing.append(object_name)
        elif obj.type != 'MESH':
            return [], "Object {!r} is a {:s}, only meshes can be merged".format(object_name, obj.type)
        else:
            objects.append(obj)
    if missing:
        return [], "Objects not found: " + ", ".join(missing)
    return objects, None


def _merge(objects: list[object]) -> tuple[object, list[object], list[str]]:
    """
    Build one mesh from *objects*.

    Returns ``(merged_mesh, shared_materials, name_order)``. Each source mesh is
    copied before its transform is baked in, so the originals stay untouched
    until the caller has a valid result.
    """
    import bmesh  # pylint: disable=import-error,no-name-in-module
    import bpy  # pylint: disable=import-error,no-name-in-module

    shared_materials: list[object] = []
    material_index: dict[str, int] = {}
    name_order: list[str] = []
    bm = bmesh.new()

    for obj in objects:
        mesh = obj.data
        name_order.append(obj.name)

        # Map this object's slots into the shared list.
        local_map: list[int] = []
        for material in mesh.materials:
            if material is None:
                continue
            if material.name not in material_index:
                material_index[material.name] = len(shared_materials)
                shared_materials.append(material)
            local_map.append(material_index[material.name])

        tmp = mesh.copy()
        # Bake the object's world transform into the geometry, otherwise the
        # parts collapse onto each other's origins.
        tmp.transform(obj.matrix_world)
        for poly in tmp.polygons:
            if local_map:
                index = poly.material_index
                poly.material_index = local_map[index] if index < len(local_map) else local_map[0]
            else:
                poly.material_index = 0
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)

    merged_mesh = bpy.data.meshes.new("_blmcp_join_tmp")
    bm.to_mesh(merged_mesh)
    bm.free()
    for material in shared_materials:
        merged_mesh.materials.append(material)

    return merged_mesh, shared_materials, name_order


def main(params: Params) -> Result:
    import bpy  # pylint: disable=import-error,no-name-in-module

    names = [n for n in list(params.object_names or []) if n]
    if len(names) < 2:
        return Result(status="error", message="At least two object names are required")
    if len(set(names)) != len(names):
        return Result(status="error", message="object_names contains duplicates")

    objects, error = _collect(names)
    if error is not None:
        return Result(status="error", message=error)

    merged_mesh, shared_materials, name_order = _merge(objects)

    requested = (params.name or "").strip() or (name_order[0] + "_joined")
    merged = bpy.data.objects.new(requested, merged_mesh)
    bpy.context.collection.objects.link(merged)
    # Rename the mesh only after the object exists, so the name is final.
    merged_mesh.name = merged.name

    if not params.keep_originals:
        for obj in objects:
            old_mesh = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if old_mesh.users == 0:
                bpy.data.meshes.remove(old_mesh)

    return Result(
        status="ok",
        name=merged.name,
        source_objects=name_order,
        vertex_count=len(merged_mesh.vertices),
        polygon_count=len(merged_mesh.polygons),
        materials=[m.name for m in shared_materials],
        message="Merged {:d} objects".format(len(objects)),
    )
