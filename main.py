"""
TenantVibe MCP Backend
FastAPI application exposing MCP-compatible tools for GHL Voice AI.

GHL Voice AI calls:
  GET  /tools  → discover available tools (MCP format)
  POST /run    → execute a tool {"tool": "name", "input": {...}}

Endpoints:
  GET  /       → health check
  GET  /tools  → MCP-spec tool list (what GHL Voice AI reads)
  POST /run    → tool execution (what GHL Voice AI calls)
  POST /mcp    → JSON-RPC 2.0 (for other MCP clients)
"""

import json
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Optional

from registry import TOOLS
from executor import execute_tool, ToolNotFoundError, ToolExecutionError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TenantVibe MCP Backend",
    description="MCP tool registry and executor for GHL Voice AI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class RunToolRequest(BaseModel):
    tool: str
    input: Optional[dict[str, Any]] = {}


class RunToolResponse(BaseModel):
    tool: str
    output: Any
    status: str = "success"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_mcp_tools() -> list:
    """
    Build tools list in MCP spec format.
    GHL Voice AI reads this from GET /tools.
    Uses camelCase inputSchema as per MCP spec.
    """
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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def health_check():
    """Health check — Render and GHL use this to verify service is up."""
    return {
        "status": "ok",
        "service": "TenantVibe MCP Backend",
        "version": "1.0.0",
        "tools_registered": len(TOOLS),
    }


@app.get("/tools", tags=["MCP"])
def list_tools():
    """
    MCP-spec tool discovery endpoint.
    GHL Voice AI calls GET /tools to discover available actions.
    Returns tools with inputSchema in JSON Schema format.
    """
    return {"tools": build_mcp_tools()}


@app.post("/run", tags=["MCP"])
async def run_tool(payload: RunToolRequest):
    """
    Tool execution endpoint.
    GHL Voice AI calls POST /run after selecting a tool from /tools.

    Body: {"tool": "create_booking", "input": {"customer_name": "John", ...}}
    """
    if not payload.tool:
        raise HTTPException(status_code=400, detail="'tool' field is required")

    logger.info(f"Running tool: {payload.tool} with input: {payload.input}")

    try:
        result = await execute_tool(payload.tool, payload.input or {})
        return RunToolResponse(tool=payload.tool, output=result)
    except ToolNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ToolExecutionError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp", tags=["MCP JSON-RPC"])
async def mcp_jsonrpc(request: Request):
    """
    MCP JSON-RPC 2.0 endpoint for other MCP clients (not GHL Voice AI).
    Handles: initialize, tools/list, tools/call
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={
            "jsonrpc": "2.0",
            "error": {"code": -32700, "message": "Parse error"},
            "id": None,
        })

    jsonrpc_id = body.get("id")
    method = body.get("method", "")
    params = body.get("params", {}) or {}

    logger.info(f"MCP JSON-RPC: method={method} id={jsonrpc_id}")

    if method == "initialize":
        return JSONResponse(content={
            "jsonrpc": "2.0", "id": jsonrpc_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "TenantVibe MCP Backend", "version": "1.0.0"},
            },
        })

    if method == "ping":
        return JSONResponse(content={"jsonrpc": "2.0", "id": jsonrpc_id, "result": {}})

    if method.startswith("notifications/"):
        return JSONResponse(status_code=202, content={})

    if method == "tools/list":
        return JSONResponse(content={
            "jsonrpc": "2.0", "id": jsonrpc_id,
            "result": {"tools": build_mcp_tools()},
        })

    if method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {}) or {}
        try:
            result = await execute_tool(tool_name, tool_args)
            return JSONResponse(content={
                "jsonrpc": "2.0", "id": jsonrpc_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result)}],
                    "isError": False,
                },
            })
        except ToolNotFoundError as e:
            return JSONResponse(content={
                "jsonrpc": "2.0", "id": jsonrpc_id,
                "error": {"code": -32601, "message": str(e)},
            })
        except ToolExecutionError as e:
            return JSONResponse(content={
                "jsonrpc": "2.0", "id": jsonrpc_id,
                "result": {"content": [{"type": "text", "text": str(e)}], "isError": True},
            })

    return JSONResponse(content={
        "jsonrpc": "2.0", "id": jsonrpc_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    })


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
