"""
Tool: create_lead
Creates a new CRM lead/contact via GHL API.
Currently returns dummy data — replace with real GHL API call.
"""

from services import ghl


async def run(data: dict) -> dict:
    name = data.get("name")
    phone = data.get("phone")
    email = data.get("email", "")
    source = data.get("source", "voice_ai")
    notes = data.get("notes", "")

    result = await ghl.create_contact({
        "name": name,
        "phone": phone,
        "email": email,
        "source": source,
        "notes": notes,
    })

    return {
        "status": "success",
        "message": f"Lead created for {name}",
        "lead_id": result["lead_id"],
        "contact_id": result["contact_id"],
        "name": name,
        "phone": phone,
        "email": email,
        "source": source,
    }
