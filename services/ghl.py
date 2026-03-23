"""
GoHighLevel (GHL) Service Layer
Abstracts all calls to the GHL CRM API.

HOW TO CONNECT:
  1. Set GHL_API_KEY and GHL_LOCATION_ID in environment variables / Render settings
  2. Replace each dummy return block with a real httpx call to the GHL API
  Docs: https://highlevel.stoplight.io/docs/integrations
"""

import os
import uuid
import httpx

GHL_API_URL = os.getenv("GHL_API_URL", "https://services.leadconnectorhq.com")
GHL_API_KEY = os.getenv("GHL_API_KEY", "dummy-ghl-key")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID", "dummy-location-id")

_client = httpx.AsyncClient(
    base_url=GHL_API_URL,
    headers={
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
        "Version": "2021-07-28",
    },
    timeout=10.0,
)


async def create_contact(data: dict) -> dict:
    """
    Create a contact/lead in GHL CRM.

    Real implementation:
        payload = {
            "locationId": GHL_LOCATION_ID,
            "firstName": data["name"].split()[0],
            "lastName": " ".join(data["name"].split()[1:]),
            "phone": data["phone"],
            "email": data.get("email"),
            "source": data.get("source"),
            "customFields": [{"key": "notes", "value": data.get("notes")}],
        }
        response = await _client.post("/contacts/", json=payload)
        response.raise_for_status()
        body = response.json()
        return {"lead_id": body["contact"]["id"], "contact_id": body["contact"]["id"]}
    """
    # --- DUMMY IMPLEMENTATION ---
    contact_id = f"GHL-{uuid.uuid4().hex[:10].upper()}"
    return {
        "lead_id": contact_id,
        "contact_id": contact_id,
    }


async def update_contact(lead_id: str, updates: dict) -> dict:
    """
    Update an existing GHL contact.

    Real implementation:
        response = await _client.put(f"/contacts/{lead_id}", json=updates)
        response.raise_for_status()
        return response.json()
    """
    # --- DUMMY IMPLEMENTATION ---
    return {
        "contact_id": lead_id,
        "updated": True,
    }
