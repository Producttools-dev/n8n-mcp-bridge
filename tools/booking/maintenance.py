"""
Tool: log_maintenance_request
Logs a tenant maintenance/repair request.
Currently returns dummy data — replace with real PMS/ticketing API call.
"""

import uuid
from services import pms2


async def run(data: dict) -> dict:
    tenant_name = data.get("tenant_name")
    unit_number = data.get("unit_number")
    issue_type = data.get("issue_type")
    description = data.get("description")
    priority = data.get("priority", "medium")

    result = await pms2.log_maintenance({
        "tenant_name": tenant_name,
        "unit_number": unit_number,
        "issue_type": issue_type,
        "description": description,
        "priority": priority,
    })

    return {
        "status": "success",
        "message": f"Maintenance request logged for unit {unit_number}",
        "ticket_id": result["ticket_id"],
        "tenant_name": tenant_name,
        "unit_number": unit_number,
        "issue_type": issue_type,
        "priority": priority,
        "estimated_response": result["estimated_response"],
    }
