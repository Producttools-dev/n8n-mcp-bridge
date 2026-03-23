"""
PMS1 Service Layer
Abstracts all calls to your primary Property Management System (PMS).

HOW TO CONNECT:
  1. Set PMS1_API_URL and PMS1_API_KEY in your environment variables / Render settings
  2. Replace each dummy return block with a real httpx call to your PMS API
  3. Map the API response fields to match what callers expect
"""

import os
import uuid
import httpx

PMS1_API_URL = os.getenv("PMS1_API_URL", "https://dummy-pms1.example.com")
PMS1_API_KEY = os.getenv("PMS1_API_KEY", "dummy-key")

# Shared async HTTP client (reuse across requests for connection pooling)
_client = httpx.AsyncClient(
    base_url=PMS1_API_URL,
    headers={"Authorization": f"Bearer {PMS1_API_KEY}", "Content-Type": "application/json"},
    timeout=10.0,
)


async def create_booking(data: dict) -> dict:
    """
    Create a booking in PMS1.

    Real implementation (replace dummy block):
        response = await _client.post("/bookings", json=data)
        response.raise_for_status()
        return response.json()
    """
    # --- DUMMY IMPLEMENTATION ---
    return {
        "booking_id": f"BKG-{uuid.uuid4().hex[:8].upper()}",
        "confirmation_number": f"CNF-{uuid.uuid4().hex[:6].upper()}",
        "status": "confirmed",
    }


async def check_availability(data: dict) -> dict:
    """
    Check property availability for a date range.

    Real implementation:
        response = await _client.get("/availability", params=data)
        response.raise_for_status()
        return response.json()
    """
    # --- DUMMY IMPLEMENTATION ---
    return {
        "available": True,
        "nightly_rate": 150.00,
        "total_price": 600.00,
    }


async def cancel_booking(data: dict) -> dict:
    """
    Cancel an existing booking.

    Real implementation:
        response = await _client.delete(f"/bookings/{data['booking_id']}", json=data)
        response.raise_for_status()
        return response.json()
    """
    # --- DUMMY IMPLEMENTATION ---
    return {
        "cancellation_id": f"CXL-{uuid.uuid4().hex[:8].upper()}",
        "refund_eligible": True,
    }


async def get_tenant(data: dict) -> dict:
    """
    Retrieve tenant info by name or unit number.

    Real implementation:
        response = await _client.get("/tenants", params=data)
        response.raise_for_status()
        return response.json()
    """
    # --- DUMMY IMPLEMENTATION ---
    return {
        "tenant_id": f"TNT-{uuid.uuid4().hex[:6].upper()}",
        "name": data.get("name", "Jane Smith"),
        "unit_number": data.get("unit_number", "4B"),
        "email": "tenant@example.com",
        "phone": "+1-555-0100",
        "lease_start": "2025-01-01",
        "lease_end": "2026-01-01",
        "rent_status": "current",
    }
