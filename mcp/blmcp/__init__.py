# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
MCP server for Blender.

Provides tools for LLM's, connecting to Blender via a bridge-server.
All tools send code to the add-on to run.
"""

__all__ = (
    "main",
)

import argparse
import fnmatch
import importlib
import os
import pkgutil
import sys
from typing import Any

import yaml
from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error,no-name-in-module

# NOTE(@ideasman42): this was written to support LLAMA-C++'s Web UI,
# which is one of the nicer ways to run this locally.
# It is not full HTTP support because there looks to be many options for this protocol.
# This could be disabled if it no longer serves its purpose - as most agents wont use STDIO.
_USE_HTTP_SUPPORT = True

_TRANSPORTS = ("stdio", *(("http",) if _USE_HTTP_SUPPORT else ()))

# Environment variables limiting which tools are exposed to the client.
#
# ALLOW and DENY each take a comma separated list of tool names, where every
# entry may use shell style wildcards, e.g. "execute_blender_code*".
# DENY is applied after ALLOW so a broad allow list can have exceptions carved
# out of it. Leaving both unset means no restriction at all.
#
# READ_ONLY exposes only tools declaring ``readOnlyHint=True``. It fails closed:
# a tool that does not explicitly declare itself read-only is withheld. That is
# the behavior you want when handing the server to a client you do not fully
# trust, since the add-on executes whatever it is sent.
#
# These knobs only affect tool *visibility*, they are not a sandbox. See the
# add-on's `weak_sandbox` module for why filtering code content is not viable.
_ENV_ALLOW_TOOLS = "BLENDER_MCP_ALLOW_TOOLS"
_ENV_DENY_TOOLS = "BLENDER_MCP_DENY_TOOLS"
_ENV_READ_ONLY = "BLENDER_MCP_READ_ONLY"
_TRUTHY = ("1", "true", "yes", "on")


def _parse_env_patterns(name: str) -> list[str]:
    """
    Read a comma separated wildcard list from the *name* environment variable.
    """
    return [part.strip() for part in os.environ.get(name, "").split(",") if part.strip()]


class _ToolRegistryFilter:
    """
    Proxy around ``FastMCP`` that withholds selected ``@mcp.tool()`` registrations.

    This holds policy only and knows nothing about individual tools, so adding a
    tool never requires editing this file.

    Filtering is per TOOL NAME rather than per module because a single module may
    register several tools (``execute_blender_code`` registers two). Skipping
    whole modules would drag unrelated tools down with the blocked one.

    Tool modules only ever call ``mcp.tool(...)``, so every other attribute is
    forwarded to the real server and nothing else about startup changes.
    """

    __slots__ = ("_mcp", "_read_only", "_allow", "_deny", "blocked")

    def __init__(
            self,
            mcp: FastMCP,
            read_only: bool,
            allow: list[str],
            deny: list[str],
    ) -> None:
        self._mcp = mcp
        self._read_only = read_only
        self._allow = allow
        self._deny = deny
        # ``(tool_name, reason)`` for each withheld tool, so startup can report it.
        self.blocked: list[tuple[str, str]] = []

    def _reject_reason(self, name: str, annotations: Any) -> str | None:
        """
        Return why *name* must not be registered, or ``None`` when it is allowed.
        """
        if self._read_only and getattr(annotations, "readOnlyHint", None) is not True:
            return "does not declare readOnlyHint"
        if self._allow and not any(fnmatch.fnmatchcase(name, pat) for pat in self._allow):
            return "not matched by " + _ENV_ALLOW_TOOLS
        if any(fnmatch.fnmatchcase(name, pat) for pat in self._deny):
            return "matched by " + _ENV_DENY_TOOLS
        return None

    def tool(self, *args: Any, **kwargs: Any) -> Any:
        annotations = kwargs.get("annotations")
        register_tool = self._mcp.tool(*args, **kwargs)

        def decorator(fn: Any) -> Any:
            name = str(getattr(fn, "__name__", repr(fn)))
            reason = self._reject_reason(name, annotations)
            if reason is not None:
                self.blocked.append((name, reason))
                # The function stays intact, it is simply never registered.
                return fn
            return register_tool(fn)

        return decorator

    def __getattr__(self, name: str) -> Any:
        # Everything except ``tool`` behaves exactly like the real server.
        return getattr(self._mcp, name)


def main() -> int:
    parser = argparse.ArgumentParser(description="MCP server for Blender.")
    parser.add_argument(
        "--transport", "-t",
        choices=_TRANSPORTS,
        default="stdio",
        help="Transport protocol (default: stdio).",
    )
    if _USE_HTTP_SUPPORT:
        parser.add_argument(
            "--host",
            default="127.0.0.1",
            help="Host to bind to for HTTP transports (default: 127.0.0.1).",
        )
        parser.add_argument(
            "--port", "-p",
            type=int,
            default=8000,
            help="Port to bind to for HTTP transports (default: 8000).",
        )
    args = parser.parse_args()

    # Load prompts.
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    with open(os.path.join(data_dir, "prompts.yml"), encoding="utf-8") as fh:
        prompts = yaml.safe_load(fh)

    mcp = FastMCP("blender-mcp", instructions=str(prompts["initial_instructions"]))

    # Tool visibility policy, see the environment variable notes above.
    allow_patterns = _parse_env_patterns(_ENV_ALLOW_TOOLS)
    deny_patterns = _parse_env_patterns(_ENV_DENY_TOOLS)
    read_only = os.environ.get(_ENV_READ_ONLY, "").strip().lower() in _TRUTHY
    restricted = bool(allow_patterns or deny_patterns or read_only)

    # Auto-discover and register all tools (they are never un-registered).
    import blmcp.tools as tools_pkg

    registry: Any = (
        _ToolRegistryFilter(mcp, read_only, allow_patterns, deny_patterns)
        if restricted else mcp
    )

    for _importer, modname, _ispkg in pkgutil.iter_modules(tools_pkg.__path__):
        if modname.endswith("_toolcode") or modname.startswith("_template_"):
            continue
        mod = importlib.import_module("blmcp.tools.{:s}".format(modname))
        if hasattr(mod, "register"):
            mod.register(registry)

    if restricted:
        # Report the policy on stderr. A silently missing tool is painful to
        # debug from the client side, which only sees a shorter tool list.
        print(
            "blender-mcp: tool policy active (read_only={:s}, allow={:s}, deny={:s})".format(
                str(read_only), repr(allow_patterns), repr(deny_patterns),
            ),
            file=sys.stderr,
        )
        for _name, _reason in sorted(registry.blocked):
            print("blender-mcp: withheld {:s} - {:s}".format(_name, _reason), file=sys.stderr)

    transport = args.transport
    if _USE_HTTP_SUPPORT and transport == "http":
        # pylint: disable-next=import-error,no-name-in-module
        from mcp.server.fastmcp.server import TransportSecuritySettings  # type: ignore[attr-defined]
        from starlette.applications import Starlette
        from starlette.middleware.cors import CORSMiddleware

        transport = "streamable-http"

        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.settings.streamable_http_path = "/"
        mcp.settings.stateless_http = True
        mcp.settings.transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=False,
        )

        # Add CORS middleware so browser-based clients
        # (e.g. llama.cpp web UI) can connect without preflight failures.
        _orig = mcp.streamable_http_app

        def _app_with_cors() -> Starlette:
            app = _orig()
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
            )
            return app

        mcp.streamable_http_app = _app_with_cors  # type: ignore[method-assign]

    mcp.run(transport=transport)
    return 0
