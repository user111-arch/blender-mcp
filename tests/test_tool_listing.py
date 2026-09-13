# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Checks that the MCP server exposes the expected tool listing.
"""

__all__ = ()

import asyncio
import os
import sys
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Root of the repository.
_REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Complete expected tool listing.
# When a tool is added, changed, or removed this must be updated.
# Run with `--update` to regenerate from a live server query.

# BEGIN: EXPECTED_TOOLS
EXPECTED_TOOLS = [
    {
        "name": "add_light",
        "description": "\n"
        "        Add a light, or update the existing light with the same *name*.\n"
        "\n"
        "        *light_type* is one of ``\"AREA\"``, ``\"POINT\"``, ``\"SUN\"``, ``\"SPOT\"``.\n"
        "\n"
        "        *energy* is in watts for point/area/spot lights and irradiance for sun\n"
        "        lights. Cartoon-style scenes usually want tens of watts for a soft key\n"
        "        rather than hundreds, which blow the colours out to white.\n"
        "\n"
        "        *size* is the radius of an area light, or the cone angle for a spot.\n"
        "\n"
        "        *location* is a 3-element list. *aim_at* is an optional 3-element target\n"
        "        point; when given, the light is rotated to point at it, which is usually\n"
        "        what you want instead of guessing Euler angles.\n"
        "\n"
        "        *color* is an optional 3 or 4 element RGB(A) list in the 0-1 range.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "name": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Name"
                },
                "light_type": {
                    "default": "AREA",
                    "title": "Light Type",
                    "type": "string"
                },
                "energy": {
                    "default": 100.0,
                    "title": "Energy",
                    "type": "number"
                },
                "size": {
                    "default": 1.0,
                    "title": "Size",
                    "type": "number"
                },
                "location": {
                    "anyOf": [
                        {
                            "items": {
                                "type": "number"
                            },
                            "type": "array"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Location"
                },
                "aim_at": {
                    "anyOf": [
                        {
                            "items": {
                                "type": "number"
                            },
                            "type": "array"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Aim At"
                },
                "color": {
                    "anyOf": [
                        {
                            "items": {
                                "type": "number"
                            },
                            "type": "array"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Color"
                }
            },
            "title": "add_lightArguments",
            "type": "object"
        }
    },
    {
        "name": "create_material",
        "description": "\n"
        "        Create a material, or update it when *name* already exists.\n"
        "\n"
        "        *base_color* is a 3 or 4 element list of RGBA values in the 0-1 range.\n"
        "        The Principled BSDF is configured directly. This is the supported way to\n"
        "        set an object's colour, and it avoids two pitfalls that both leave a\n"
        "        model rendering uniformly white: node names are localised in the UI (so\n"
        "        the shader node must be located by type, not by name), and the Material\n"
        "        Output's Surface socket is not always linked on a fresh material.\n"
        "\n"
        "        *assign_to* optionally lists object names to assign the material to. It\n"
        "        is appended to each object's material slots and made the active slot.\n"
        "\n"
        "        The material's viewport ``diffuse_color`` is kept in sync with the\n"
        "        shader, so solid shading and Workbench renders show the same colour.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "name": {
                    "title": "Name",
                    "type": "string"
                },
                "base_color": {
                    "anyOf": [
                        {
                            "items": {
                                "type": "number"
                            },
                            "type": "array"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Base Color"
                },
                "roughness": {
                    "anyOf": [
                        {
                            "type": "number"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Roughness"
                },
                "metallic": {
                    "anyOf": [
                        {
                            "type": "number"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Metallic"
                },
                "assign_to": {
                    "anyOf": [
                        {
                            "items": {
                                "type": "string"
                            },
                            "type": "array"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Assign To"
                }
            },
            "required": [
                "name"
            ],
            "title": "create_materialArguments",
            "type": "object"
        }
    },
    {
        "name": "create_primitive",
        "description": "\n"
        "        Create a primitive mesh object in the connected Blender scene.\n"
        "\n"
        "        *primitive_type* is one of ``\"cube\"``, ``\"sphere\"``, ``\"cylinder\"``,\n"
        "        ``\"plane\"``, ``\"cone\"``, ``\"torus\"``.\n"
        "\n"
        "        *size* is the object's principal extent in meters, applied\n"
        "        consistently across types, so ``size=2.0`` yields a 2m cube, a\n"
        "        2m-diameter sphere, and so on. It must be greater than zero.\n"
        "\n"
        "        *location* and *rotation* are optional 3-element lists; rotation is\n"
        "        in radians and uses the XYZ Euler mode. *scale* is an optional\n"
        "        3-element list applied after creation.\n"
        "\n"
        "        *name* is a requested object name - Blender de-duplicates collisions\n"
        "        by appending ``.001``, so the response reports the name actually\n"
        "        assigned. The new object is linked to the active collection.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "primitive_type": {
                    "title": "Primitive Type",
                    "type": "string"
                },
                "name": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Name"
                },
                "size": {
                    "default": 2.0,
                    "title": "Size",
                    "type": "number"
                },
                "location": {
                    "anyOf": [
                        {
                            "items": {
                                "type": "number"
                            },
                            "type": "array"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Location"
                },
                "rotation": {
                    "anyOf": [
                        {
                            "items": {
                                "type": "number"
                            },
                            "type": "array"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Rotation"
                },
                "scale": {
                    "anyOf": [
                        {
                            "items": {
                                "type": "number"
                            },
                            "type": "array"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Scale"
                }
            },
            "required": [
                "primitive_type"
            ],
            "title": "create_primitiveArguments",
            "type": "object"
        }
    },
    {
        "name": "delete_objects",
        "description": "\n"
        "        Delete the objects named in *names*, unlinking them from every\n"
        "        collection they belong to.\n"
        "\n"
        "        Deleting objects leaves their data-blocks (meshes, materials, and so\n"
        "        on) behind until those lose all users. Set *purge_data* to additionally\n"
        "        remove the orphaned mesh / curve / material / camera / light / armature\n"
        "        data-blocks in the same call.\n"
        "\n"
        "        Returns the names that were deleted and the names that did not exist.\n"
        "        The deletion itself cannot be undone from this tool.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "names": {
                    "items": {
                        "type": "string"
                    },
                    "title": "Names",
                    "type": "array"
                },
                "purge_data": {
                    "default": False,
                    "title": "Purge Data",
                    "type": "boolean"
                }
            },
            "required": [
                "names"
            ],
            "title": "delete_objectsArguments",
            "type": "object"
        }
    },
    {
        "name": "duplicate_object",
        "description": "\n"
        "        Duplicate the object identified by *name*.\n"
        "\n"
        "        *count* copies are created and must be at least 1. *offset* is an\n"
        "        optional 3-element list: copy *i* (1-based) is placed at\n"
        "        ``source.location + offset * i``, so copies spread out in a row.\n"
        "\n"
        "        *linked* selects the duplication kind - ``False`` (default) gives each\n"
        "        copy its own data-block, ``True`` shares the source's data so editing\n"
        "        one geometry affects all of them.\n"
        "\n"
        "        *name_prefix* optionally renames the copies to ``<prefix>1``,\n"
        "        ``<prefix>2``, and so on. Copies are linked into every collection the\n"
        "        source belongs to. Returns the names actually assigned.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "name": {
                    "title": "Name",
                    "type": "string"
                },
                "count": {
                    "default": 1,
                    "title": "Count",
                    "type": "integer"
                },
                "offset": {
                    "anyOf": [
                        {
                            "items": {
                                "type": "number"
                            },
                            "type": "array"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Offset"
                },
                "name_prefix": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Name Prefix"
                },
                "linked": {
                    "default": False,
                    "title": "Linked",
                    "type": "boolean"
                }
            },
            "required": [
                "name"
            ],
            "title": "duplicate_objectArguments",
            "type": "object"
        }
    },
    {
        "name": "execute_blender_code",
        "description": "\n"
        "        Execute Python code in the connected Blender instance.\n"
        "\n"
        "        The code runs in Blender's Python environment with full access to ``bpy``.\n"
        "        To return data, assign a JSON-serialisable dict to a variable named ``result``.\n"
        "        Deferred completion via ``check_is_finished`` is only supported by the\n"
        "        interactive addon server, and is rejected in background mode.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "code": {
                    "title": "Code",
                    "type": "string"
                }
            },
            "required": [
                "code"
            ],
            "title": "execute_blender_codeArguments",
            "type": "object"
        }
    },
    {
        "name": "execute_blender_code_for_cli",
        "description": "\n"
        "        Execute Python code in a background Blender process.\n"
        "\n"
        "        Opens *blend_file* with ``blender --background`` and runs *code*.\n"
        "        Assign a dict to ``result`` to return data.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "blend_file": {
                    "title": "Blend File",
                    "type": "string"
                },
                "code": {
                    "title": "Code",
                    "type": "string"
                }
            },
            "required": [
                "blend_file",
                "code"
            ],
            "title": "execute_blender_code_for_cliArguments",
            "type": "object"
        }
    },
    {
        "name": "export_scene",
        "description": "\n"
        "        Export scene geometry to a file for use outside Blender.\n"
        "\n"
        "        *export_format* is one of ``\"glb\"``, ``\"gltf\"``, ``\"obj\"``, ``\"fbx\"``,\n"
        "        ``\"stl\"``. ``glb`` is the safest choice for handing a model to another\n"
        "        tool, since it carries meshes and materials in a single file.\n"
        "\n"
        "        *filename* is the name to write. As with the render tools it is resolved\n"
        "        inside Blender's scratch directory, so the exported file has to be\n"
        "        copied from there. Accepting an arbitrary path would make this an\n"
        "        arbitrary-file-write primitive.\n"
        "\n"
        "        *selected_only* exports just the selected objects rather than the whole\n"
        "        scene. The response reports the resulting path and its size.\n"
        "\n"
        "        Scene data is not modified; the tool only writes a file.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "filename": {
                    "title": "Filename",
                    "type": "string"
                },
                "export_format": {
                    "default": "glb",
                    "title": "Export Format",
                    "type": "string"
                },
                "selected_only": {
                    "default": False,
                    "title": "Selected Only",
                    "type": "boolean"
                }
            },
            "required": [
                "filename"
            ],
            "title": "export_sceneArguments",
            "type": "object"
        }
    },
    {
        "name": "get_blendfile_summary_datablocks",
        "description": "\n"
        "        Return a summary of the blend file: data-block counts, active workspace, and render engine.\n"
        "        ",
        "inputSchema": {
            "properties": {},
            "title": "get_blendfile_summary_datablocksArguments",
            "type": "object"
        }
    },
    {
        "name": "get_blendfile_summary_datablocks_for_cli",
        "description": "\n"
        "        Return a data-block summary by opening *blend_file* in background Blender.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "blend_file": {
                    "title": "Blend File",
                    "type": "string"
                }
            },
            "required": [
                "blend_file"
            ],
            "title": "get_blendfile_summary_datablocks_for_cliArguments",
            "type": "object"
        }
    },
    {
        "name": "get_blendfile_summary_missing_files",
        "description": "\n"
        "        Report external file references that are missing from disk\n"
        "        (images, libraries, fonts, sounds, movie clips, caches, sequences).\n"
        "        ",
        "inputSchema": {
            "properties": {},
            "title": "get_blendfile_summary_missing_filesArguments",
            "type": "object"
        }
    },
    {
        "name": "get_blendfile_summary_missing_files_for_cli",
        "description": "\n"
        "        Report missing file references by opening *blend_file* in background Blender.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "blend_file": {
                    "title": "Blend File",
                    "type": "string"
                }
            },
            "required": [
                "blend_file"
            ],
            "title": "get_blendfile_summary_missing_files_for_cliArguments",
            "type": "object"
        }
    },
    {
        "name": "get_blendfile_summary_of_linked_libraries",
        "description": "\n"
        "        Return a tree of directly and indirectly linked library files.\n"
        "        ",
        "inputSchema": {
            "properties": {},
            "title": "get_blendfile_summary_of_linked_librariesArguments",
            "type": "object"
        }
    },
    {
        "name": "get_blendfile_summary_of_linked_libraries_for_cli",
        "description": "\n"
        "        Return linked-library info by opening *blend_file* in background Blender.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "blend_file": {
                    "title": "Blend File",
                    "type": "string"
                }
            },
            "required": [
                "blend_file"
            ],
            "title": "get_blendfile_summary_of_linked_libraries_for_cliArguments",
            "type": "object"
        }
    },
    {
        "name": "get_blendfile_summary_path_info",
        "description": "\n"
        "        Simple/fast access to the blend file's path, save status, age, and backups.\n"
        "        ",
        "inputSchema": {
            "properties": {},
            "title": "get_blendfile_summary_path_infoArguments",
            "type": "object"
        }
    },
    {
        "name": "get_blendfile_summary_path_info_for_cli",
        "description": "\n"
        "        Return path info by opening *blend_file* in background Blender.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "blend_file": {
                    "title": "Blend File",
                    "type": "string"
                }
            },
            "required": [
                "blend_file"
            ],
            "title": "get_blendfile_summary_path_info_for_cliArguments",
            "type": "object"
        }
    },
    {
        "name": "get_blendfile_summary_usage_guess",
        "description": "\n"
        "        Guess the primary use-cases of the current blend file (scored 0-100 with certainty).\n"
        "        ",
        "inputSchema": {
            "properties": {},
            "title": "get_blendfile_summary_usage_guessArguments",
            "type": "object"
        }
    },
    {
        "name": "get_blendfile_summary_usage_guess_for_cli",
        "description": "\n"
        "        Guess use-cases by opening *blend_file* in background Blender.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "blend_file": {
                    "title": "Blend File",
                    "type": "string"
                }
            },
            "required": [
                "blend_file"
            ],
            "title": "get_blendfile_summary_usage_guess_for_cliArguments",
            "type": "object"
        }
    },
    {
        "name": "get_object_detail_summary",
        "description": "\n"
        "        Return a structured summary of the object identified by *name*.\n"
        "\n"
        "        Includes type, transforms, parent, children, modifiers, constraints,\n"
        "        materials, visibility, data-block name, and collections.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "name": {
                    "title": "Name",
                    "type": "string"
                }
            },
            "required": [
                "name"
            ],
            "title": "get_object_detail_summaryArguments",
            "type": "object"
        }
    },
    {
        "name": "get_objects_summary",
        "description": "\n"
        "        Return the scene's collection hierarchy and their objects.\n"
        "\n"
        "        Each collection lists its objects (name, type, parent, data name,\n"
        "        selection, visibility) and nested child collections.\n"
        "        ",
        "inputSchema": {
            "properties": {},
            "title": "get_objects_summaryArguments",
            "type": "object"
        }
    },
    {
        "name": "get_python_api_docs",
        "description": "\n"
        "        Return the Blender Python API docs for *identifier*, or list\n"
        "        modules matching a trailing-``*`` discovery pattern.\n"
        "\n"
        "        *identifier* should be a fully-qualified Python name (e.g.\n"
        "        ``bpy.app`` or ``bpy.types.Scene.frame_current``).\n"
        "        The trailing-``*`` forms are supported as discovery entry-points:\n"
        "\n"
        "        - ``*`` enumerates the top-level modules (``bpy``, ``bmesh``,\n"
        "          ``mathutils``, ``gpu``, ...).\n"
        "        - ``X.*`` enumerates the direct-child identifiers under the\n"
        "          *X* namespace (``bpy.*`` -> ``bpy.app``, ``bpy.context``, ...).\n"
        "\n"
        "        Both return a ``namespace`` response even when ``X.rst`` would\n"
        "        otherwise resolve to ``exact``; the ``.*`` form lets an agent\n"
        "        force the child listing.\n"
        "\n"
        "        The response always carries ``kind``, ``found``, and ``identifier``.\n"
        "        The remaining keys depend on ``kind``:\n"
        "\n"
        "        - ``\"exact\"`` (``found=True``): ``<identifier>.rst`` was read.\n"
        "          Extra keys: ``content`` (RST text), ``examples``. When the\n"
        "          file exceeds 32 KB, ``content`` is replaced with a dot-point\n"
        "          summary of the file's top-level definitions (prefixed by a\n"
        "          header noting the truncation) and ``examples`` is empty -\n"
        "          re-query individual members for their rendered blocks.\n"
        "        - ``\"namespace\"`` (``found=True``):\n"
        "          no ``<identifier>.rst`` but ``<identifier>.<child>.rst`` siblings exist.\n"
        "          Extra key: ``submodules`` (list of child identifiers).\n"
        "        - ``\"definition\"`` (``found=True``):\n"
        "          *identifier* is defined inside a parent RST\n"
        "          (e.g. ``bpy.props.IntProperty`` lives in ``bpy.props.rst``).\n"
        "          Extra keys: ``content`` (rendered block), ``examples``.\n"
        "        - ``\"partial\"`` (``found=False``):\n"
        "          the parent RST was located but the trailing component isn't defined in it.\n"
        "          Extra keys:\n"
        "          - ``parent`` the identifier whose RST was loaded.\n"
        "          - ``available`` top-level definitions in that RST.\n"
        "          - ``submodules`` sibling identifiers ``<parent>.<child>`` with their own RSTs,\n"
        "            filtered to those whose last component contains every character of the missing tail.\n"
        "\n"
        "          For a toctree landing page like ``bpy.types`` ``available`` is empty and ``submodules``\n"
        "          is the near-miss list; for a self-contained module like ``bpy.props`` it's the reverse.\n"
        "        - ``\"suggestions\"`` (``found=False``):\n"
        "          no direct match, but *identifier* appears as a component of other files.\n"
        "          Extra key: ``suggestions`` (list of full identifiers).\n"
        "        - ``\"missing\"`` (``found=False``): nothing matched.\n"
        "\n"
        "        ``examples`` (present on the ``exact`` and ``definition`` kinds)\n"
        "        is a list of ``{path, content}`` entries referenced from this documentation.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "identifier": {
                    "title": "Identifier",
                    "type": "string"
                }
            },
            "required": [
                "identifier"
            ],
            "title": "get_python_api_docsArguments",
            "type": "object"
        }
    },
    {
        "name": "get_screenshot_of_area_as_image",
        "description": "\n"
        "        Take a screenshot of a single Blender area and return it as a PNG image.\n"
        "\n"
        "        *area_ui_type* matches the area's ``ui_type``.\n"
        "\n"
        "        *size_limit_in_bytes* caps the image size in bytes.\n"
        "        Zero (the default) uses the MCP message size limit.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "area_ui_type": {
                    "enum": [
                        "VIEW_3D",
                        "IMAGE_EDITOR",
                        "UV",
                        "ShaderNodeTree",
                        "CompositorNodeTree",
                        "GeometryNodeTree",
                        "TextureNodeTree",
                        "SEQUENCE_EDITOR",
                        "CLIP_EDITOR",
                        "DOPESHEET_EDITOR",
                        "GRAPH_EDITOR",
                        "NLA_EDITOR",
                        "TEXT_EDITOR",
                        "CONSOLE",
                        "INFO",
                        "TOPBAR",
                        "STATUSBAR",
                        "OUTLINER",
                        "PROPERTIES",
                        "FILE_BROWSER",
                        "SPREADSHEET",
                        "PREFERENCES"
                    ],
                    "title": "Area Ui Type",
                    "type": "string"
                },
                "size_limit_in_bytes": {
                    "default": 0,
                    "title": "Size Limit In Bytes",
                    "type": "integer"
                }
            },
            "required": [
                "area_ui_type"
            ],
            "title": "get_screenshot_of_area_as_imageArguments",
            "type": "object"
        }
    },
    {
        "name": "get_screenshot_of_window_as_image",
        "description": "\n"
        "        Take a screenshot of the entire Blender window and return it as a PNG image.\n"
        "\n"
        "        *size_limit_in_bytes* caps the image size in bytes.\n"
        "        Zero (the default) uses the MCP message size limit.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "size_limit_in_bytes": {
                    "default": 0,
                    "title": "Size Limit In Bytes",
                    "type": "integer"
                }
            },
            "title": "get_screenshot_of_window_as_imageArguments",
            "type": "object"
        }
    },
    {
        "name": "get_screenshot_of_window_as_json",
        "description": "\n"
        "        Return a JSON description of the Blender window layout, areas, active object, and selection.\n"
        "        ",
        "inputSchema": {
            "properties": {},
            "title": "get_screenshot_of_window_as_jsonArguments",
            "type": "object"
        }
    },
    {
        "name": "join_objects",
        "description": "\n"
        "        Merge two or more mesh objects into a single object.\n"
        "\n"
        "        This is the safe alternative to Blender's Join operator. The merge runs\n"
        "        through ``bmesh`` at the data level, avoiding ``bpy.ops.object.join()``\n"
        "        which aborts Blender with an access violation when its operator context\n"
        "        is incomplete - a crash Python cannot catch.\n"
        "\n"
        "        *object_names* lists the objects to merge, at least two of them. Their\n"
        "        world transforms are baked into the geometry, and material slots from\n"
        "        every source are re-mapped into one shared list, so each part keeps its\n"
        "        own colour.\n"
        "\n"
        "        *name* is the requested name for the result. Blender de-duplicates\n"
        "        collisions with a ``.001`` suffix, so the response reports the name\n"
        "        actually assigned.\n"
        "\n"
        "        *keep_originals* leaves the source objects in the scene. By default they\n"
        "        are deleted, along with their mesh data when nothing else uses it.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "object_names": {
                    "items": {
                        "type": "string"
                    },
                    "title": "Object Names",
                    "type": "array"
                },
                "name": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Name"
                },
                "keep_originals": {
                    "default": False,
                    "title": "Keep Originals",
                    "type": "boolean"
                }
            },
            "required": [
                "object_names"
            ],
            "title": "join_objectsArguments",
            "type": "object"
        }
    },
    {
        "name": "jump_to_tab_by_name",
        "description": "\n"
        "        Switch the active workspace tab to *name*.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "name": {
                    "title": "Name",
                    "type": "string"
                }
            },
            "required": [
                "name"
            ],
            "title": "jump_to_tab_by_nameArguments",
            "type": "object"
        }
    },
    {
        "name": "jump_to_tab_by_space_type",
        "description": "\n"
        "        Switch to a workspace whose main area matches *space_type*.\n"
        "\n"
        "        If *allow_edits* is True and no matching workspace exists, a new one\n"
        "        is created by duplicating the current workspace.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "space_type": {
                    "title": "Space Type",
                    "type": "string"
                },
                "allow_edits": {
                    "default": False,
                    "title": "Allow Edits",
                    "type": "boolean"
                }
            },
            "required": [
                "space_type"
            ],
            "title": "jump_to_tab_by_space_typeArguments",
            "type": "object"
        }
    },
    {
        "name": "jump_to_view3d_object_by_name",
        "description": "\n"
        "        Move the 3D viewport to focus on an object by *name*.\n"
        "\n"
        "        If *allow_edits* is True the object may be un-hidden and its\n"
        "        collections enabled to make it visible.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "name": {
                    "title": "Name",
                    "type": "string"
                },
                "allow_edits": {
                    "default": False,
                    "title": "Allow Edits",
                    "type": "boolean"
                }
            },
            "required": [
                "name"
            ],
            "title": "jump_to_view3d_object_by_nameArguments",
            "type": "object"
        }
    },
    {
        "name": "jump_to_view3d_object_data_by_name",
        "description": "\n"
        "        Move the 3D viewport to the object whose data block matches *name*.\n"
        "\n"
        "        If *allow_edits* is True the object may be un-hidden and its\n"
        "        collections enabled to make it visible.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "name": {
                    "title": "Name",
                    "type": "string"
                },
                "allow_edits": {
                    "default": False,
                    "title": "Allow Edits",
                    "type": "boolean"
                }
            },
            "required": [
                "name"
            ],
            "title": "jump_to_view3d_object_data_by_nameArguments",
            "type": "object"
        }
    },
    {
        "name": "render_thumbnail_to_path",
        "description": "\n"
        "        Render a small, low-quality thumbnail to *output_path* (temporarily overrides settings).\n"
        "        ",
        "inputSchema": {
            "properties": {
                "output_path": {
                    "title": "Output Path",
                    "type": "string"
                }
            },
            "required": [
                "output_path"
            ],
            "title": "render_thumbnail_to_pathArguments",
            "type": "object"
        }
    },
    {
        "name": "render_to_image",
        "description": "\n"
        "        Render the current scene and return the result as a PNG image.\n"
        "\n"
        "        ``render_viewport_to_path`` only hands back a path inside Blender's\n"
        "        scratch directory, which is useless to a client that cannot read that\n"
        "        filesystem. This returns the image itself so the render can actually be\n"
        "        looked at.\n"
        "\n"
        "        *resolution_x* and *resolution_y* optionally override the scene\n"
        "        resolution for this render only, and are restored afterwards. Zero (the\n"
        "        default) keeps the current setting.\n"
        "\n"
        "        *size_limit_in_bytes* caps the returned image size; zero (the default)\n"
        "        uses the MCP message size limit and downscales the image if needed.\n"
        "\n"
        "        The render uses the scene's current engine, camera and settings. Scene\n"
        "        data is not modified, but a temporary PNG is written to Blender's\n"
        "        scratch directory.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "resolution_x": {
                    "default": 0,
                    "title": "Resolution X",
                    "type": "integer"
                },
                "resolution_y": {
                    "default": 0,
                    "title": "Resolution Y",
                    "type": "integer"
                },
                "size_limit_in_bytes": {
                    "default": 0,
                    "title": "Size Limit In Bytes",
                    "type": "integer"
                }
            },
            "title": "render_to_imageArguments",
            "type": "object"
        }
    },
    {
        "name": "render_viewport_to_path",
        "description": "\n"
        "        Render the current scene to *output_path* using current render settings.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "output_path": {
                    "title": "Output Path",
                    "type": "string"
                }
            },
            "required": [
                "output_path"
            ],
            "title": "render_viewport_to_pathArguments",
            "type": "object"
        }
    },
    {
        "name": "search_api_docs",
        "description": "\n"
        "Full-text search over the bundled Blender Python API reference.\n"
        "\n"
        "Returns a ranked list of hits. Each hit has:\n"
        "\n"
        "- ``path``: file path relative to the bundled docs.\n"
        "- ``text``: the matching paragraph plus ``context``\n"
        "  paragraphs on either side.\n"
        "- ``breadcrumb``: the section path containing the hit\n"
        "  (``Section > Sub-section > ...``).\n"
        "- ``index``: the hit's position in the result list.\n"
        "- ``score``: a relevance score; higher is better.\n"
        "\n"
        "The query is tokenised on whitespace and matched\n"
        "case-insensitively. Every token must appear somewhere in\n"
        "the paragraph body, the file path, or an enclosing section\n"
        "title - in any order. Common English stop-words (``the``,\n"
        "``a``, ``how``, ``to``, ...) are dropped, so natural\n"
        "phrasings like ``\"how to bake\"`` work as expected. Regular\n"
        "expressions are not supported.\n"
        "\n"
        "Use ``context`` to pull more surrounding paragraphs into\n"
        "each hit (symmetric, default 0). Use ``index`` with the\n"
        "position of a previous hit (same query) to get that hit\n"
        "alone with its text widened to its enclosing section.\n"
        "\n"
        "Read-only; consults bundled RST files only.\n",
        "inputSchema": {
            "properties": {
                "query": {
                    "title": "Query",
                    "type": "string"
                },
                "max_results": {
                    "default": 20,
                    "title": "Max Results",
                    "type": "integer"
                },
                "context": {
                    "default": 0,
                    "title": "Context",
                    "type": "integer"
                },
                "index": {
                    "anyOf": [
                        {
                            "type": "integer"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Index"
                }
            },
            "required": [
                "query"
            ],
            "title": "search_api_docsArguments",
            "type": "object"
        }
    },
    {
        "name": "search_manual_docs",
        "description": "\n"
        "Full-text search over the bundled Blender user manual.\n"
        "\n"
        "Returns a ranked list of hits. Each hit has:\n"
        "\n"
        "- ``path``: file path relative to the bundled docs.\n"
        "- ``text``: the matching paragraph plus ``context``\n"
        "  paragraphs on either side.\n"
        "- ``breadcrumb``: the section path containing the hit\n"
        "  (``Section > Sub-section > ...``).\n"
        "- ``index``: the hit's position in the result list.\n"
        "- ``score``: a relevance score; higher is better.\n"
        "\n"
        "The query is tokenised on whitespace and matched\n"
        "case-insensitively. Every token must appear somewhere in\n"
        "the paragraph body, the file path, or an enclosing section\n"
        "title - in any order. Common English stop-words (``the``,\n"
        "``a``, ``how``, ``to``, ...) are dropped, so natural\n"
        "phrasings like ``\"how to bake\"`` work as expected. Regular\n"
        "expressions are not supported.\n"
        "\n"
        "Use ``context`` to pull more surrounding paragraphs into\n"
        "each hit (symmetric, default 0). Use ``index`` with the\n"
        "position of a previous hit (same query) to get that hit\n"
        "alone with its text widened to its enclosing section.\n"
        "\n"
        "Read-only; consults bundled RST files only.\n",
        "inputSchema": {
            "properties": {
                "query": {
                    "title": "Query",
                    "type": "string"
                },
                "max_results": {
                    "default": 20,
                    "title": "Max Results",
                    "type": "integer"
                },
                "context": {
                    "default": 0,
                    "title": "Context",
                    "type": "integer"
                },
                "index": {
                    "anyOf": [
                        {
                            "type": "integer"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Index"
                }
            },
            "required": [
                "query"
            ],
            "title": "search_manual_docsArguments",
            "type": "object"
        }
    },
    {
        "name": "setup_camera",
        "description": "\n"
        "        Position a camera, creating it when it does not exist yet.\n"
        "\n"
        "        *location* is a 3-element list for the camera position and *aim_at* a\n"
        "        3-element target point. Aiming at a point is far more reliable than\n"
        "        supplying Euler angles by hand, and it is what makes a render frame the\n"
        "        subject rather than the empty space beside it.\n"
        "\n"
        "        *lens* is the focal length in millimetres; larger values are more\n"
        "        telephoto and flatten the perspective, which suits product-style shots\n"
        "        of a small model.\n"
        "\n"
        "        *camera_name* selects which camera object to configure, and\n"
        "        *make_active* also assigns it as the scene camera used for rendering.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "location": {
                    "anyOf": [
                        {
                            "items": {
                                "type": "number"
                            },
                            "type": "array"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Location"
                },
                "aim_at": {
                    "anyOf": [
                        {
                            "items": {
                                "type": "number"
                            },
                            "type": "array"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Aim At"
                },
                "lens": {
                    "default": 50.0,
                    "title": "Lens",
                    "type": "number"
                },
                "camera_name": {
                    "default": "Camera",
                    "title": "Camera Name",
                    "type": "string"
                },
                "make_active": {
                    "default": True,
                    "title": "Make Active",
                    "type": "boolean"
                }
            },
            "title": "setup_cameraArguments",
            "type": "object"
        }
    },
    {
        "name": "transform_object",
        "description": "\n"
        "        Set or offset the transform of the object identified by *name*.\n"
        "\n"
        "        *mode* is either ``\"absolute\"`` (assign the given values) or\n"
        "        ``\"relative\"`` (location and rotation are added, scale is\n"
        "        multiplied). At least one of location/rotation/scale is required.\n"
        "\n"
        "        Vectors are 3-element lists. Rotation is in radians and is written to\n"
        "        the XYZ Euler channels. If the object uses a different rotation mode\n"
        "        it is switched to XYZ so the write actually takes effect - the\n"
        "        existing orientation is preserved across the switch, and the response\n"
        "        reports ``rotation_mode_before``/``rotation_mode_after`` so the change\n"
        "        is never silent.\n"
        "\n"
        "        Returns the resulting location, rotation, scale and dimensions.\n"
        "        ",
        "inputSchema": {
            "properties": {
                "name": {
                    "title": "Name",
                    "type": "string"
                },
                "location": {
                    "anyOf": [
                        {
                            "items": {
                                "type": "number"
                            },
                            "type": "array"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Location"
                },
                "rotation": {
                    "anyOf": [
                        {
                            "items": {
                                "type": "number"
                            },
                            "type": "array"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Rotation"
                },
                "scale": {
                    "anyOf": [
                        {
                            "items": {
                                "type": "number"
                            },
                            "type": "array"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": None,
                    "title": "Scale"
                },
                "mode": {
                    "default": "absolute",
                    "title": "Mode",
                    "type": "string"
                }
            },
            "required": [
                "name"
            ],
            "title": "transform_objectArguments",
            "type": "object"
        }
    }
]
# END: EXPECTED_TOOLS


def _list_tools() -> list[dict[str, object]]:
    """
    Starts the MCP server and returns the full tool listing.
    """

    # Async is required because the MCP client SDK is async-only.
    async def _run() -> list[dict[str, object]]:
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.join(_REPO_DIR, "mcp")
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "blmcp"],
            env=env,
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return [
                    {
                        "name": t.name,
                        "description": t.description,
                        "inputSchema": t.inputSchema,
                    }
                    for t in result.tools
                ]

    return asyncio.run(_run())


class TestToolListing(unittest.TestCase):
    """
    Checks that the live tool listing matches the frozen snapshot.
    """

    _tools: list[dict[str, object]]

    @classmethod
    def setUpClass(cls) -> None:
        cls._tools = _list_tools()

    def test_tools_match_expected(self) -> None:
        """
        Checks that the live tool listing exactly matches ``EXPECTED_TOOLS``.
        """
        self.assertEqual(self._tools, EXPECTED_TOOLS)


def _update_expected_tools() -> None:
    """
    Re-generates the ``EXPECTED_TOOLS`` block from a live server query.
    """
    import json
    import subprocess

    filepath = os.path.abspath(__file__)
    with open(filepath, "r", encoding="utf-8") as fh:
        source = fh.read()
    begin = source.index("# BEGIN: EXPECTED_TOOLS\n") + len("# BEGIN: EXPECTED_TOOLS\n")
    end = source.index("# END: EXPECTED_TOOLS\n")
    formatted = json.dumps(_list_tools(), indent=4)
    formatted = (
        formatted.replace(": true", ": True")
        .replace(": false", ": False")
        .replace(": null", ": None")
    )
    formatted = formatted.replace("\\n", '\\n"\n"')
    # Also handles the `\n"` case (no trailing empty string).
    formatted = formatted.replace('\\n"\n""', '\\n"')
    formatted = "EXPECTED_TOOLS = " + formatted + "\n"
    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write(source[:begin] + formatted + source[end:])
    subprocess.check_call(["autopep8", "--in-place", filepath])


if __name__ == "__main__":
    if "--update" in sys.argv:
        sys.argv.remove("--update")
        _update_expected_tools()
    else:
        unittest.main()
