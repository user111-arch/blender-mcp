# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for creating or updating a material.

Runs inside Blender. `main` must return a NamedTuple (or a callable for the
deferred protocol); the calling-convention footer converts it via `._asdict()`.

Two traps are handled here deliberately. Both of them leave a model rendering
uniformly white when missed, and neither raises an error:

- Shader nodes are located by `bl_idname`, never by name. Blender localises a
  node's default name to the UI language, so on a non-English install the
  Principled node is not called "Principled BSDF" and a name lookup quietly
  returns None, leaving Base Color unwritten.
- The Material Output `Surface` socket is wired up explicitly. A freshly created
  material was observed with it unlinked, which is an empty shader: it renders
  white regardless of the colour that was set.
"""

__all__ = (
    "Params",
    "Result",
    "main",
)

from typing import NamedTuple


class Params(NamedTuple):
    name: str
    base_color: list[float] | None = None
    roughness: float | None = None
    metallic: float | None = None
    assign_to: list[str] | None = None


class Result(NamedTuple):
    status: str
    material: str | None = None
    created: bool | None = None
    base_color: list[float] | None = None
    roughness: float | None = None
    metallic: float | None = None
    assigned_to: list[str] | None = None
    missing_objects: list[str] | None = None
    message: str | None = None


def _color4(value: list[float] | None) -> list[float] | None:
    if value is None:
        return None
    if len(value) not in (3, 4):
        raise ValueError("base_color must have 3 or 4 elements, got {:d}".format(len(value)))
    out = [float(v) for v in value]
    if len(out) == 3:
        # Blender colours are RGBA; assume opaque when alpha is omitted.
        out.append(1.0)
    for channel in out:
        if not 0.0 <= channel <= 1.0:
            raise ValueError("base_color components must be within 0-1, got {:g}".format(channel))
    return out


def _shader_nodes(tree: object) -> tuple[object, object]:
    """
    Return the tree's Principled BSDF and Material Output nodes.

    Missing nodes are created, so a partial or empty node tree is repaired
    rather than silently producing a material with no surface shader.
    """
    bsdf = next((n for n in tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    output = next((n for n in tree.nodes if n.bl_idname == "ShaderNodeOutputMaterial"), None)
    if bsdf is None:
        bsdf = tree.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (0.0, 0.0)
    if output is None:
        output = tree.nodes.new("ShaderNodeOutputMaterial")
        output.location = (300.0, 0.0)
    return bsdf, output


def _assign(objects: list[str], material: object) -> tuple[list[str], list[str]]:
    import bpy  # pylint: disable=import-error,no-name-in-module

    assigned: list[str] = []
    missing: list[str] = []
    for object_name in objects:
        obj = bpy.data.objects.get(object_name)
        if obj is None or obj.type != 'MESH':
            missing.append(object_name)
            continue
        # Reuse a slot already holding this material, otherwise append a new one.
        slot_index = next(
            (i for i, slot in enumerate(obj.material_slots) if slot.material == material),
            None,
        )
        if slot_index is None:
            obj.data.materials.append(material)
            slot_index = len(obj.data.materials) - 1
        obj.active_material_index = slot_index
        assigned.append(obj.name)
    return assigned, missing


def main(params: Params) -> Result:
    import bpy  # pylint: disable=import-error,no-name-in-module

    name = params.name.strip()
    if not name:
        return Result(status="error", message="Material name must not be empty")

    try:
        color = _color4(params.base_color)
    except ValueError as ex:
        return Result(status="error", message=str(ex))

    for label, value in (("roughness", params.roughness), ("metallic", params.metallic)):
        if value is not None and not 0.0 <= float(value) <= 1.0:
            return Result(status="error", message="{:s} must be within 0-1".format(label))

    material = bpy.data.materials.get(name)
    created = material is None
    if material is None:
        material = bpy.data.materials.new(name)

    material.use_nodes = True
    bsdf, output = _shader_nodes(material.node_tree)

    if color is not None:
        bsdf.inputs["Base Color"].default_value = color
        # The solid/viewport shading path reads `diffuse_color`, so keep it in
        # sync or a Workbench render shows a different colour.
        material.diffuse_color = color
    if params.roughness is not None:
        bsdf.inputs["Roughness"].default_value = float(params.roughness)
    if params.metallic is not None:
        bsdf.inputs["Metallic"].default_value = float(params.metallic)

    if not output.inputs["Surface"].is_linked:
        material.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    assigned, missing = _assign(list(params.assign_to or []), material)

    return Result(
        status="ok",
        material=material.name,
        created=created,
        base_color=[round(float(v), 4) for v in bsdf.inputs["Base Color"].default_value],
        roughness=round(float(bsdf.inputs["Roughness"].default_value), 4),
        metallic=round(float(bsdf.inputs["Metallic"].default_value), 4),
        assigned_to=assigned,
        missing_objects=missing,
        message=("Material created" if created else "Material updated"),
    )
