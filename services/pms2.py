"""
PMS2 Service Layer
Abstracts all calls to your secondary PMS / billing / ticketing system.

HOW TO CONNECT:
  1. Set PMS2_API_URL and PMS2_API_KEY in environment variables / Render settings
  2. Replace each dummy return block with a real httpx call
"""

import os
import uuid
import httpx

PMS2_API_URL = os.getenv("PMS2_API_URL", "https://dummy-pms2.example.com")
PMS2_API_KEY = os.getenv("PMS2_API_KEY", "dummy-key")

_client = httpx.AsyncClient(
    base_url=PMS2_API_URL,
    headers={"Authorization": f"Bearer {PMS2_API_KEY}", "Content-Type": "application/json"},
    timeout=10.0,
)


async def create_invoice(data: dict) -> dict:
    """
    Generate a billing invoice.

    Real implementation:
        response = await _client.post("/invoices", json=data)
        response.raise_for_status()
        return response.json()
    """
    # --- DUMMY IMPLEMENTATION ---
    invoice_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
    return {
        "invoice_id": invoice_id,
        "invoice_url": f"https://billing.example.com/invoices/{invoice_id}",
        "status": "pending",
    }


async def log_maintenance(data: dict) -> dict:
    """
    Log a maintenance/repair request.

    Real implementation:
        response = await _client.post("/maintenance", json=data)
        response.raise_for_status()
        return response.json()
    """
    # --- DUMMY IMPLEMENTATION ---
    priority_eta = {
        "emergency": "2 hours",
        "high": "24 hours",
        "medium": "3 business days",
        "low": "7 business days",
    }
    priority = data.get("priority", "medium")
    return {
        "ticket_id": f"MNT-{uuid.uuid4().hex[:8].upper()}",
        "status": "open",
        "estimated_response": priority_eta.get(priority, "3 business days"),
    }
