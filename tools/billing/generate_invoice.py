"""
Tool: generate_invoice
Generates a billing invoice for a completed booking.
Currently returns dummy data — replace with real billing API call.
"""

import uuid
from services import pms2


async def run(data: dict) -> dict:
    booking_id = data.get("booking_id")
    customer_name = data.get("customer_name")
    amount = data.get("amount", 0.0)
    due_date = data.get("due_date", "")
    line_items = data.get("line_items", [])

    result = await pms2.create_invoice({
        "booking_id": booking_id,
        "customer_name": customer_name,
        "amount": amount,
        "due_date": due_date,
        "line_items": line_items,
    })

    return {
        "status": "success",
        "message": f"Invoice generated for booking {booking_id}",
        "invoice_id": result["invoice_id"],
        "invoice_url": result["invoice_url"],
        "booking_id": booking_id,
        "customer_name": customer_name,
        "amount": amount,
        "due_date": due_date,
        "currency": "USD",
    }
