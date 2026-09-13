# Blender MCP

[简体中文](readme.zh-CN.md)

A lightweight MCP (Model Context Protocol) server for Blender.
It offers a natural language interface with Blender's Python API,
improving access to documentation, and allowing users to explore
and understand complex setups.

This repository is a fork of the official
[Blender Lab MCP server](https://projects.blender.org/lab/blender_mcp),
extended with a set of modeling tools and access controls on top of the
upstream feature set. See [What this fork adds](#what-this-fork-adds).

Read the upstream documentation at [blender.org/lab/mcp-server](https://www.blender.org/lab/mcp-server/)

----

## Overview

The project is deliberately small, maintainable, and does no more than
necessary. It has two components that communicate over a TCP socket:

- A **Blender add-on** that runs inside Blender and executes requests.
- An **MCP server** that runs as a separate process, launched by the
  MCP client (e.g. [Llama.cpp](https://projects.blender.org/lab/blender_mcp/wiki/Llama.cpp)).

The data flow is:
```
MCP Client  ⇐ MCP/stdio ⇒  blender-mcp  ⇐ TCP socket ⇒  Blender Add-on
```

Any MCP-capable client can drive it: Claude Desktop, Cursor, Cline,
Continue, a local Llama.cpp web UI, or any other agent that speaks the
protocol. Each client launches its own `blender-mcp` process; the add-on
accepts several concurrent connections, so multiple clients can share one
Blender instance. Note that they then also share a single scene, so
simultaneous use is best avoided.


## What this fork adds

**Ten new tools** covering the parts of a modeling session that upstream
leaves to `execute_blender_code`:

| Tool | Purpose |
|---|---|
| `create_primitive` | Add cube / sphere / cylinder / plane / cone / torus |
| `transform_object` | Move / rotate / scale, absolute or relative |
| `duplicate_object` | Copy an object N times with a cumulative offset |
| `delete_objects` | Remove objects and optionally purge orphan data-blocks |
| `create_material` | Create or update a material and assign it to objects |
| `join_objects` | Merge meshes safely, with material slots preserved |
| `add_light` | Add or update a light, aimed at a target point |
| `setup_camera` | Position a camera and aim it at the subject |
| `render_to_image` | Render and return the image itself, not a file path |
| `export_scene` | Export the scene to glb / gltf / obj / fbx / stl |

Each of these replaces a block of hand-written `bpy` code that is easy to
get subtly wrong. Two examples of what they prevent: `join_objects` merges
through `bmesh` because `bpy.ops.object.join()` aborts Blender outright when
its operator context is incomplete, and `create_material` locates shader
nodes by type because their *names* are localized in the UI, so a
name-based lookup silently fails on non-English installs.

**Access controls**, both optional and off by default:

- Tool visibility lists (`BLENDER_MCP_ALLOW_TOOLS`, `BLENDER_MCP_DENY_TOOLS`,
  `BLENDER_MCP_READ_ONLY`) so a client can be given a restricted tool set.
- A shared-secret handshake on the bridge socket
  (`BLENDER_MCP_TOKEN` + the add-on's *Auth Token* preference) so other
  local processes cannot drive Blender through the port.

See [Security](#security).


## Requirements

- Blender 5.1 or newer (the add-on), running with a GUI for most tools.
- Python 3.10 or newer for the MCP server, with `uv` or `pip`.
- In Blender: `Preferences → System → Network → Allow Online Access` must be
  enabled, otherwise the add-on refuses to start its server.


## Installation

### 1. Blender add-on

From a checkout of this repository, zip the `addon/blender_mcp_addon/`
directory and install it in Blender:

```
Edit → Preferences → Get Extensions → (v dropdown) → Install from Disk…
```

Enable the *MCP* extension. Its preferences panel (found under
`Preferences → Add-ons → MCP`, not the 3D viewport sidebar) shows the host,
port, auto-start and logging settings, and reports whether the server is
running.

### 2. MCP server

From the `mcp/` directory of the checkout:

```
uv sync            # creates the venv and installs dependencies
```

or with plain pip:

```
pip install .
```

The entry point is `blender-mcp`; no separate step is needed because the
MCP client launches the process itself.


## Client configuration

For stdio-capable clients (Claude Desktop, Cursor, Cline, and most others),
point the server at the checkout:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uv",
      "args": ["--directory", "/path/to/blender-mcp/mcp", "run", "blender-mcp"]
    }
  }
}
```

On Windows, use a Windows-style path. Forward slashes work and are easier
to read in JSON:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uv",
      "args": ["--directory", "C:/path/to/blender-mcp/mcp", "run", "blender-mcp"]
    }
  }
}
```

For clients that prefer a URL (Continue, certain web UIs, or anything behind
a proxy), the server also speaks streamable HTTP. Start it once per session:

```
blender-mcp --transport http --host 127.0.0.1 --port 8000
```

The endpoint is `http://127.0.0.1:8000/`. Most URL-mode clients take a
similar JSON entry instead of a stdio command:

```json
{
  "mcpServers": {
    "blender": {
      "url": "http://127.0.0.1:8000/"
    }
  }
}
```

Bind HTTP to the loopback interface only. The server exposes arbitrary code
execution by design, and binding it elsewhere hands that to the whole
network.

**Start Blender before the client.** With auto-start enabled (the default),
the bridge socket is up about a second after Blender launches; if the client
attempts to connect first, that first call hits a cold-start window and
fails with a connection error. Retry once before troubleshooting.


## Security

### Tool visibility

Which tools are exposed to a client can be restricted through environment
variables. This is useful when handing the server to a client you do not fully
trust, since some tools are far more powerful than others.

``BLENDER_MCP_DENY_TOOLS``
   Comma separated tool names that are never exposed.
``BLENDER_MCP_ALLOW_TOOLS``
   When set, only tools matching an entry in this list are exposed.
``BLENDER_MCP_READ_ONLY``
   Set to ``1`` to expose only tools that declare ``readOnlyHint``.

Entries accept shell style wildcards, e.g. ``execute_blender_code*`` matches
both ``execute_blender_code`` and ``execute_blender_code_for_cli``.
``DENY`` is applied after ``ALLOW``, so a broad allow list can have specific
exceptions carved out of it. With none of these variables set, every tool is
exposed and behavior is unchanged.

For example, to give an agent read-only access::

   BLENDER_MCP_READ_ONLY=1 blender-mcp

Or to keep everything except the arbitrary code execution tools::

   BLENDER_MCP_DENY_TOOLS='execute_blender_code*' blender-mcp

The policy in effect is reported on stderr at startup, listing each withheld
tool with the reason, so a tool that is unexpectedly missing is easy to trace.

Two caveats worth knowing.

This controls tool *visibility*, it is not a sandbox. A tool that is exposed
runs with the full privileges of the Blender process - hiding
``execute_blender_code`` does not make the bridge itself safe, since anything
that can reach the add-on socket can still execute code.

``readOnlyHint`` says whether a tool modifies Blender data, not whether it has
side effects. ``render_viewport_to_path`` is read-only in that sense, yet it
still writes an image to disk.

### Authentication

By default the add-on accepts any client that can reach its socket. That socket
is bound to the loopback interface, so the network is not the threat here: any
*local* process, including a sandboxed application, can still connect and run
arbitrary Python inside Blender, because every request is ``exec()``'d with
Blender's own privileges.

To close that off, set a token in the add-on preferences and give the same value
to the MCP server through the ``BLENDER_MCP_TOKEN`` environment variable::

   Edit -> Preferences -> Add-ons -> MCP -> Auth Token: <your secret>

The MCP server is launched by the MCP client, so the variable belongs in the
client's server configuration, for example::

   "env": {"BLENDER_MCP_TOKEN": "<your secret>"}

Leaving the preference empty disables the check, which is the default, so
existing setups keep working unchanged. When a token is set, a request carrying
a missing or wrong token is rejected before any code is executed, and the
comparison is constant time so the response cannot be timed to recover it.

Note this protects the bridge socket only. It does not make
``execute_blender_code`` safe - see Tool Visibility above, and the add-on's
``weak_sandbox`` module for why filtering code content is not a viable defense.


## Tools

The server exposes 36 tools in total.

### Reference and inspection

The upstream tool set: scene and blend-file summaries, object details,
bundled API reference and manual search, screenshots, viewport navigation,
and code execution. See [readme_tools.rst](readme_tools.rst) for the
complete list with descriptions.

### Modeling and rendering

The ten extensions listed under [What this fork adds](#what-this-fork-adds).
Conventions worth knowing:

- Tools that write files (``render_to_image``, ``export_scene``) confine
  output to Blender's scratch directory, following the upstream render
  tools. That keeps them from becoming arbitrary-file-write primitives.
- Tools that create or reconfigure scene items use upsert semantics: calling
  ``create_material`` or ``add_light`` twice with the same name updates the
  existing item rather than stacking a duplicate.


## Development

### Adding a tool

A tool is a pair of modules in ``mcp/blmcp/tools/``:

- ``<name>.py`` - the MCP side. Calls ``toolcode_format_call`` and
  ``send_code``, and registers the tool with ``@mcp.tool()``.
- ``<name>_toolcode.py`` - the Blender side. Defines ``Params`` /
  ``Result`` NamedTuples and a ``main(params)`` entry point; ``bpy`` is
  imported inside ``main``, never at module level.

Tools are auto-discovered at startup; ``*_toolcode`` modules are skipped.
Shared logic belongs in ``tools_helpers/``, tools do not import each other.

After adding a tool, regenerate the listing snapshot and run the tests:

```
python tests/test_tool_listing.py --update
python tests/test_tool_listing.py
python tests/test_mcp_server.py
```

### Tests

``make test`` (or the two scripts above) runs the suite that needs no
Blender instance. Integration tests that drive a live Blender and an LLM
live under ``tests/integration/``; see ``make help`` for their environment
variables.

### Deploying add-on changes

Blender runs the copy under
``%APPDATA%\Blender Foundation\Blender\<version>\extensions\user_default\mcp\``,
not the checkout, so addon source changes must be reinstalled to take
effect. When patching an installed copy directly, normalize line endings
(the checkout is CRLF, the installed files are LF), keep backups, and
syntax-check each file before reloading. Reloading requires removing the
``bl_ext.user_default.mcp*`` entries from ``sys.modules`` between disable
and enable - a plain toggle reuses the cached submodules.


## License

GPL-3.0-or-later, as upstream. Each source file carries its SPDX header;
third-party contributions remain attributed in place.
