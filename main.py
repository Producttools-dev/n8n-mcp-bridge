"""
TenantVibe MCP Backend
Handles ALL request patterns GHL Voice AI might use to discover/call tools.
"""

import json
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Optional

from registry import TOOLS
from executor import execute_tool, ToolNotFoundError, ToolExecutionError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="TenantVibe MCP Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_tools_list() -> list:
    tools = []
    for name, meta in TOOLS.items():
        properties = {}
        for field, schema in meta.get("input_schema", {}).items():
            properties[field] = {
                "type": schema.get("type", "string"),
                "description": schema.get("description", ""),
            }
        tools.append({
            "name": name,
            "description": meta["description"],
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": meta.get("required", []),
            },
        })
    return tools


async def handle_jsonrpc(body: dict) -> dict:
    jsonrpc_id = body.get("id")
    method = body.get("method", "")
    params = body.get("params", {}) or {}
    logger.info(f"JSON-RPC method={method} id={jsonrpc_id}")

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": jsonrpc_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "TenantVibe MCP Backend", "version": "1.0.0"},
            },
        }

    if method == "ping":
        return {"jsonrpc": "2.0", "id": jsonrpc_id, "result": {}}

    if method.startswith("notifications/"):
        return {}

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": jsonrpc_id, "result": {"tools": build_tools_list()}}

    if method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {}) or {}
        try:
            result = await execute_tool(tool_name, tool_args)
            return {
                "jsonrpc": "2.0", "id": jsonrpc_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result)}], "isError": False},
            }
        except ToolNotFoundError as e:
            return {"jsonrpc": "2.0", "id": jsonrpc_id, "error": {"code": -32601, "message": str(e)}}
        except ToolExecutionError as e:
            return {"jsonrpc": "2.0", "id": jsonrpc_id, "result": {"content": [{"type": "text", "text": str(e)}], "isError": True}}

    return {"jsonrpc": "2.0", "id": jsonrpc_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}


async def handle_rest_tool_call(body: dict) -> dict:
    """Handle GHL-style REST tool call: {"tool": "...", "input": {...}}"""
    tool_name = body.get("tool") or body.get("name")
    tool_input = body.get("input") or body.get("arguments") or body.get("parameters") or {}
    try:
        result = await execute_tool(tool_name, tool_input)
        return {"tool": tool_name, "status": "success", "output": result}
    except ToolNotFoundError as e:
        return {"tool": tool_name, "status": "error", "error": str(e)}
    except ToolExecutionError as e:
        return {"tool": tool_name, "status": "error", "error": str(e)}


# ---------------------------------------------------------------------------
# Universal POST handler — works on ANY path GHL might call
# ---------------------------------------------------------------------------

async def smart_post(request: Request) -> JSONResponse:
    """
    Handles any POST request regardless of path.
    Auto-detects whether it's JSON-RPC or REST format.
    Logs the full request for debugging.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    path = request.url.path
    logger.info(f"POST {path} body={json.dumps(body)[:200]}")

    # JSON-RPC format detection
    if "method" in body and "jsonrpc" in body:
        method = body.get("method", "")
        if method.startswith("notifications/"):
            return JSONResponse(status_code=202, content={})
        result = await handle_jsonrpc(body)
        return JSONResponse(content=result)

    # REST format: {"tool": "...", "input": {...}}
    if "tool" in body or "name" in body:
        result = await handle_rest_tool_call(body)
        return JSONResponse(content=result)

    # Unknown — return error with what we received (helps debug)
    logger.warning(f"Unrecognised POST body: {body}")
    return JSONResponse(status_code=400, content={"error": "Unrecognised request format", "received": body})


# ---------------------------------------------------------------------------
# GET handler — works on ANY path
# ---------------------------------------------------------------------------

async def smart_get(request: Request) -> JSONResponse:
    """
    Handles any GET request.
    Always returns tools list so GHL can discover them regardless of path.
    """
    path = request.url.path
    logger.info(f"GET {path}")

    if path == "/":
        return JSONResponse(content={
            "status": "ok",
            "service": "TenantVibe MCP Backend",
            "version": "1.0.0",
            "tools_registered": len(TOOLS),
        })

    # /tools, /mcp, /sse, or anything else → return tools list
    return JSONResponse(content={"tools": build_tools_list()})


# ---------------------------------------------------------------------------
# Register routes — cover every path GHL might call
# ---------------------------------------------------------------------------

@app.get("/")
async def root_get(request: Request):
    return await smart_get(request)

@app.post("/")
async def root_post(request: Request):
    return await smart_post(request)

@app.get("/tools")
async def tools_get(request: Request):
    return await smart_get(request)

@app.post("/tools")
async def tools_post(request: Request):
    return await smart_post(request)

@app.get("/mcp")
async def mcp_get(request: Request):
    return await smart_get(request)

@app.post("/mcp")
async def mcp_post(request: Request):
    return await smart_post(request)

@app.get("/sse")
async def sse_get(request: Request):
    return await smart_get(request)

@app.post("/sse")
async def sse_post(request: Request):
    return await smart_post(request)

@app.get("/run")
async def run_get(request: Request):
    return await smart_get(request)

@app.post("/run")
async def run_post(request: Request):
    return await smart_post(request)


# ---------------------------------------------------------------------------
# Global error handler
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "error": str(exc)})
