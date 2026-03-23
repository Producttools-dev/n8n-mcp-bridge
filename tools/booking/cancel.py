"""
Tool: cancel_booking
Cancels an existing booking by ID.
Currently returns dummy data — replace with real PMS API call.
"""

from services import pms1


async def run(data: dict) -> dict:
    booking_id = data.get("booking_id")
    reason = data.get("reason", "Customer requested cancellation")

    result = await pms1.cancel_booking({
        "booking_id": booking_id,
        "reason": reason,
    })

    return {
        "status": "success",
        "message": f"Booking {booking_id} has been cancelled",
        "booking_id": booking_id,
        "cancellation_id": result["cancellation_id"],
        "refund_eligible": result["refund_eligible"],
        "reason": reason,
    }
