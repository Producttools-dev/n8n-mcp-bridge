"""
Tool: update_lead
Updates an existing CRM lead/contact in GHL.
Currently returns dummy data — replace with real GHL API call.
"""

from services import ghl


async def run(data: dict) -> dict:
    lead_id = data.get("lead_id")
    updates = {k: v for k, v in data.items() if k != "lead_id" and v is not None}

    result = await ghl.update_contact(lead_id, updates)

    return {
        "status": "success",
        "message": f"Lead {lead_id} updated",
        "lead_id": lead_id,
        "updated_fields": list(updates.keys()),
    }
