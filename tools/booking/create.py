"""
Tool: create_booking
Creates a new property booking/reservation.
Currently returns dummy data — replace with real PMS API call.
"""

import uuid
from services import pms1


async def run(data: dict) -> dict:
    customer_name = data.get("customer_name", "Unknown Guest")
    property_id = data.get("property_id", "PROP-001")
    check_in = data.get("check_in")
    check_out = data.get("check_out")
    guests = data.get("guests", 1)

    # --- Replace this block with real PMS API call ---
    result = await pms1.create_booking({
        "customer_name": customer_name,
        "property_id": property_id,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
    })
    # --------------------------------------------------

    return {
        "status": "success",
        "message": f"Booking created for {customer_name}",
        "booking_id": result["booking_id"],
        "confirmation_number": result["confirmation_number"],
        "property_id": property_id,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
    }
