"""
Tool: get_availability
Checks property availability for a date range.
Currently returns dummy data — replace with real PMS API call.
"""

from services import pms1


async def run(data: dict) -> dict:
    property_id = data.get("property_id", "PROP-001")
    check_in = data.get("check_in")
    check_out = data.get("check_out")

    result = await pms1.check_availability({
        "property_id": property_id,
        "check_in": check_in,
        "check_out": check_out,
    })

    return {
        "status": "success",
        "property_id": property_id,
        "check_in": check_in,
        "check_out": check_out,
        "available": result["available"],
        "nightly_rate": result["nightly_rate"],
        "total_price": result["total_price"],
        "currency": "USD",
    }
