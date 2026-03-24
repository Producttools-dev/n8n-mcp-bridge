"""
TenantVibe MCP Backend
FastAPI application exposing MCP-compatible tools for GHL Voice AI.

GHL Voice AI uses Streamable HTTP transport (MCP spec 2024-11-05):
  - POST /mcp with JSON-RPC body
  - If client sends Accept: text/event-stream → respond with SSE
  - If client sends Accept: application/json → respond with plain JSON
  - Both formats carry the same JSON-RPC 2.0 payload

Endpoints:
  GET  /       → health check
  GET  /tools  → legacy REST list (for testing)
  POST /run    → legacy REST execute (for testing / n8n)
  POST /mcp    → MCP Streamable HTTP (GHL Voice AI)
  GET  /mcp    → MCP SSE stream initializer (some clients use GET)
"""

import json
import logging
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Optional, AsyncIterator
from sse_starlette.sse import EventSourceResponse

from registry import TOOLS
from executor import execute_tool, ToolNotFoundError, ToolExecutionError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TenantVibe MCP Backend",
    description="MCP Streamable HTTP server for GHL Voice AI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Legacy REST models
# ---------------------------------------------------------------------------

class RunToolRequest(BaseModel):
    tool: str
    input: Optional[dict[str, Any]] = {}

class RunToolResponse(BaseModel):
    tool: str
    output: Any
    status: str = "success"


# ---------------------------------------------------------------------------
# MCP helpers
# ---------------------------------------------------------------------------

def build_tools_list() -> list:
    """Convert registry into MCP spec tools/list format."""
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
    """Core JSON-RPC dispatcher — returns a response dict."""
    jsonrpc_id = body.get("id")
    method = body.get("method", "")
    params = body.get("params", {}) or {}

    logger.info(f"MCP method={method} id={jsonrpc_id}")

    # ── initialize ────────────────────────────────────────────────────────
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": jsonrpc_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "TenantVibe MCP Backend", "version": "1.0.0"},
            },
        }

    # ── ping ──────────────────────────────────────────────────────────────
    if method == "ping":
        return {"jsonrpc": "2.0", "id": jsonrpc_id, "result": {}}

    # ── notifications (fire-and-forget, no id) ────────────────────────────
    if method.startswith("notifications/"):
        return {}   # empty — caller should not send this as a response

    # ── tools/list ────────────────────────────────────────────────────────
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": jsonrpc_id,
            "result": {"tools": build_tools_list()},
        }

    # ── tools/call ────────────────────────────────────────────────────────
    if method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {}) or {}

        if not tool_name:
            return {
                "jsonrpc": "2.0",
                "id": jsonrpc_id,
                "error": {"code": -32602, "message": "Missing tool name"},
            }

        try:
            result = await execute_tool(tool_name, tool_args)
            return {
                "jsonrpc": "2.0",
                "id": jsonrpc_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result)}],
                    "isError": False,
                },
            }
        except ToolNotFoundError as e:
            return {
                "jsonrpc": "2.0",
                "id": jsonrpc_id,
                "error": {"code": -32601, "message": str(e)},
            }
        except ToolExecutionError as e:
            return {
                "jsonrpc": "2.0",
                "id": jsonrpc_id,
                "result": {
                    "content": [{"type": "text", "text": str(e)}],
                    "isError": True,
                },
            }

    # ── unknown method ────────────────────────────────────────────────────
    return {
        "jsonrpc": "2.0",
        "id": jsonrpc_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "TenantVibe MCP Backend",
        "version": "1.0.0",
        "tools_registered": len(TOOLS),
        "transport": "MCP Streamable HTTP (2024-11-05)",
    }


@app.get("/tools", tags=["REST"])
def list_tools():
    tools_list = []
    for name, meta in TOOLS.items():
        tools_list.append({
            "name": name,
            "description": meta["description"],
            "category": meta.get("category", "general"),
            "input_schema": meta.get("input_schema", {}),
            "required": meta.get("required", []),
        })
    return {"tools": tools_list, "total": len(tools_list)}


@app.post("/run", tags=["REST"])
async def run_tool(payload: RunToolRequest):
    from fastapi import HTTPException
    if not payload.tool:
        raise HTTPException(status_code=400, detail="'tool' field is required")
    try:
        result = await execute_tool(payload.tool, payload.input or {})
        return RunToolResponse(tool=payload.tool, output=result)
    except ToolNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ToolExecutionError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp", tags=["MCP"])
async def mcp_post(request: Request):
    """
    MCP Streamable HTTP endpoint.
    GHL sends Accept: text/event-stream → we respond with SSE.
    Other clients may send Accept: application/json → plain JSON.
    """
    # Parse body
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None},
        )

    # Notifications don't need a response body
    method = body.get("method", "")
    if method.startswith("notifications/"):
        logger.info(f"Notification received: {method}")
        return JSONResponse(status_code=202, content={})

    response_data = await handle_jsonrpc(body)

    # Check if client wants SSE (GHL Voice AI does)
    accept = request.headers.get("accept", "")
    if "text/event-stream" in accept:
        async def event_generator() -> AsyncIterator[dict]:
            yield {
                "event": "message",
                "data": json.dumps(response_data),
            }

        return EventSourceResponse(event_generator())

    # Plain JSON fallback
    return JSONResponse(content=response_data)


@app.get("/mcp", tags=["MCP"])
async def mcp_get(request: Request):
    """
    Some MCP clients open a GET SSE stream first.
    We keep the connection alive and send a ready event.
    """
    async def ready_stream() -> AsyncIterator[dict]:
        yield {"event": "ready", "data": json.dumps({"status": "connected"})}
        # Keep alive
        while True:
            await asyncio.sleep(15)
            yield {"event": "ping", "data": "{}"}

    return EventSourceResponse(ready_stream())


# ---------------------------------------------------------------------------
# Global error handler
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )
