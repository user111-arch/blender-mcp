#####
Tools
#####

The tools exposed by the MCP server.

..
   Generated from the tool doc-strings by ``make readme_update``.
   Do not edit the listing between the sentinels below by hand.

.. BEGIN TOOL LISTING

``add_light``
   Add a light, or update the existing light with the same *name*.

``create_material``
   Create a material, or update it when *name* already exists.

``create_primitive``
   Create a primitive mesh object in the connected Blender scene.

``delete_objects``
   Delete the objects named in *names*, unlinking them from every
   collection they belong to.

``duplicate_object``
   Duplicate the object identified by *name*.

``execute_blender_code``
   Execute Python code in the connected Blender instance.

``execute_blender_code_for_cli``
   Execute Python code in a background Blender process.

``export_scene``
   Export scene geometry to a file for use outside Blender.

``get_blendfile_summary_datablocks``
   Return a summary of the blend file: data-block counts, active workspace,
   and render engine.

``get_blendfile_summary_datablocks_for_cli``
   Return a data-block summary by opening *blend_file* in background
   Blender.

``get_blendfile_summary_missing_files``
   Report external file references that are missing from disk (images,
   libraries, fonts, sounds, movie clips, caches, sequences).

``get_blendfile_summary_missing_files_for_cli``
   Report missing file references by opening *blend_file* in background
   Blender.

``get_blendfile_summary_of_linked_libraries``
   Return a tree of directly and indirectly linked library files.

``get_blendfile_summary_of_linked_libraries_for_cli``
   Return linked-library info by opening *blend_file* in background
   Blender.

``get_blendfile_summary_path_info``
   Simple/fast access to the blend file's path, save status, age, and
   backups.

``get_blendfile_summary_path_info_for_cli``
   Return path info by opening *blend_file* in background Blender.

``get_blendfile_summary_usage_guess``
   Guess the primary use-cases of the current blend file (scored 0-100 with
   certainty).

``get_blendfile_summary_usage_guess_for_cli``
   Guess use-cases by opening *blend_file* in background Blender.

``get_object_detail_summary``
   Return a structured summary of the object identified by *name*.

``get_objects_summary``
   Return the scene's collection hierarchy and their objects.

``get_python_api_docs``
   Return the Blender Python API docs for *identifier*, or list modules
   matching a trailing-``*`` discovery pattern.

``get_screenshot_of_area_as_image``
   Take a screenshot of a single Blender area and return it as a PNG image.

``get_screenshot_of_window_as_image``
   Take a screenshot of the entire Blender window and return it as a PNG
   image.

``get_screenshot_of_window_as_json``
   Return a JSON description of the Blender window layout, areas, active
   object, and selection.

``join_objects``
   Merge two or more mesh objects into a single object.

``jump_to_tab_by_name``
   Switch the active workspace tab to *name*.

``jump_to_tab_by_space_type``
   Switch to a workspace whose main area matches *space_type*.

``jump_to_view3d_object_by_name``
   Move the 3D viewport to focus on an object by *name*.

``jump_to_view3d_object_data_by_name``
   Move the 3D viewport to the object whose data block matches *name*.

``render_thumbnail_to_path``
   Render a small, low-quality thumbnail to *output_path* (temporarily
   overrides settings).

``render_to_image``
   Render the current scene and return the result as a PNG image.

``render_viewport_to_path``
   Render the current scene to *output_path* using current render settings.

``search_api_docs``
   Full-text search over the bundled Blender Python API reference.

``search_manual_docs``
   Full-text search over the bundled Blender user manual.

``setup_camera``
   Position a camera, creating it when it does not exist yet.

``transform_object``
   Set or offset the transform of the object identified by *name*.

.. END TOOL LISTING
