"""
TenantVibe MCP Backend
FastAPI application exposing a central MCP-compatible tool registry for GHL Voice AI.

Endpoints:
  GET  /         → health check
  GET  /tools    → list all registered tools (legacy REST)
  POST /run      → execute a specific tool (legacy REST)
  POST /mcp      → MCP JSON-RPC 2.0 endpoint (GHL Voice AI compatible)
"""

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
    description="Central MCP tool registry and executor for GHL Voice AI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / Response models (legacy REST)
# ---------------------------------------------------------------------------

class RunToolRequest(BaseModel):
    tool: str
    input: Optional[dict[str, Any]] = {}


class RunToolResponse(BaseModel):
    tool: str
    output: Any
    status: str = "success"


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "TenantVibe MCP Backend",
        "version": "1.0.0",
        "tools_registered": len(TOOLS),
    }


# ---------------------------------------------------------------------------
# Legacy REST endpoints (keep for testing / n8n)
# ---------------------------------------------------------------------------

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


@app.post("/run", tags=["REST"], response_model=RunToolResponse)
async def run_tool(payload: RunToolRequest):
    if not payload.tool:
        raise HTTPException(status_code=400, detail="'tool' field is required")
    try:
        result = await execute_tool(payload.tool, payload.input or {})
        return RunToolResponse(tool=payload.tool, output=result)
    except ToolNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ToolExecutionError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# MCP JSON-RPC 2.0 endpoint — GHL Voice AI compatible
# ---------------------------------------------------------------------------

def build_tools_list() -> list:
    """Convert registry into MCP-spec tools/list format."""
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


@app.post("/mcp", tags=["MCP"])
async def mcp_endpoint(request: Request):
    """
    MCP JSON-RPC 2.0 endpoint.
    GHL Voice AI sends requests here to:
      - initialize  : handshake
      - tools/list  : discover available tools
      - tools/call  : execute a tool
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None},
        )

    jsonrpc_id = body.get("id")
    method = body.get("method", "")
    params = body.get("params", {})

    logger.info(f"MCP request: method={method} id={jsonrpc_id}")

    # ── initialize ─────────────────────────────────────────────────────────
    if method == "initialize":
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "id": jsonrpc_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "TenantVibe MCP Backend",
                    "version": "1.0.0",
                },
            },
        })

    # ── notifications/initialized (no response needed) ─────────────────────
    if method == "notifications/initialized":
        return JSONResponse(content={})

    # ── tools/list ─────────────────────────────────────────────────────────
    if method == "tools/list":
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "id": jsonrpc_id,
            "result": {
                "tools": build_tools_list(),
            },
        })

    # ── tools/call ─────────────────────────────────────────────────────────
    if method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        if not tool_name:
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": jsonrpc_id,
                "error": {"code": -32602, "message": "Missing tool name"},
            })

        try:
            result = await execute_tool(tool_name, tool_args)
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": jsonrpc_id,
                "result": {
                    "content": [{"type": "text", "text": str(result)}],
                    "isError": False,
                },
            })
        except ToolNotFoundError as e:
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": jsonrpc_id,
                "error": {"code": -32601, "message": str(e)},
            })
        except ToolExecutionError as e:
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": jsonrpc_id,
                "result": {
                    "content": [{"type": "text", "text": str(e)}],
                    "isError": True,
                },
            })

    # ── unknown method ──────────────────────────────────────────────────────
    return JSONResponse(content={
        "jsonrpc": "2.0",
        "id": jsonrpc_id,
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
