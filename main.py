"""
TenantVibe MCP Backend
FastAPI application exposing a central MCP-compatible tool registry for GHL Voice AI.

Endpoints:
  GET  /         → health check
  GET  /tools    → list all registered tools
  POST /run      → execute a specific tool
"""

import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Optional

from registry import TOOLS
from executor import execute_tool, ToolNotFoundError, ToolExecutionError

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
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
# Request / Response models
# ---------------------------------------------------------------------------

class RunToolRequest(BaseModel):
    tool: str
    input: Optional[dict[str, Any]] = {}


class RunToolResponse(BaseModel):
    tool: str
    output: Any
    status: str = "success"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def health_check():
    """Simple health check — Render uses this to verify the service is up."""
    return {
        "status": "ok",
        "service": "TenantVibe MCP Backend",
        "version": "1.0.0",
        "tools_registered": len(TOOLS),
    }


@app.get("/tools", tags=["MCP"])
def list_tools():
    """
    Return all registered tools with their descriptions and input schemas.
    GHL Voice AI calls this to discover what actions are available.
    """
    tools_list = []
    for name, meta in TOOLS.items():
        tools_list.append({
            "name": name,
            "description": meta["description"],
            "category": meta.get("category", "general"),
            "input_schema": meta.get("input_schema", {}),
            "required": meta.get("required", []),
        })

    return {
        "tools": tools_list,
        "total": len(tools_list),
    }


@app.post("/run", tags=["MCP"], response_model=RunToolResponse)
async def run_tool(payload: RunToolRequest):
    """
    Execute a specific tool by name with the provided input.

    GHL calls this after selecting a tool from /tools.

    Body:
        {
            "tool": "create_booking",
            "input": {
                "customer_name": "John Doe",
                "check_in": "2026-04-01",
                "check_out": "2026-04-05"
            }
        }
    """
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
# Global error handler
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )
