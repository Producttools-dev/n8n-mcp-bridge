"""
Tool Executor
Dynamically imports and executes tool handlers from the registry.
"""

import importlib
import logging
from registry import TOOLS

logger = logging.getLogger(__name__)


class ToolNotFoundError(Exception):
    pass


class ToolExecutionError(Exception):
    pass


async def execute_tool(name: str, input_data: dict) -> dict:
    """
    Dynamically resolve and execute a tool by name.

    Args:
        name: Tool name (must exist in TOOLS registry)
        input_data: Dictionary of input parameters

    Returns:
        Tool execution result as a dict

    Raises:
        ToolNotFoundError: If tool name is not in registry
        ToolExecutionError: If tool execution fails
    """
    tool = TOOLS.get(name)

    if not tool:
        available = list(TOOLS.keys())
        raise ToolNotFoundError(
            f"Tool '{name}' not found. Available tools: {available}"
        )

    handler_path = tool["handler"]
    module_path, func_name = handler_path.rsplit(".", 1)

    try:
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to load handler '{handler_path}': {e}")
        raise ToolExecutionError(f"Could not load tool handler: {handler_path}")

    try:
        logger.info(f"Executing tool '{name}' with input: {input_data}")
        result = await func(input_data)
        logger.info(f"Tool '{name}' completed successfully")
        return result
    except Exception as e:
        logger.error(f"Tool '{name}' execution failed: {e}")
        raise ToolExecutionError(f"Tool execution failed: {str(e)}")
