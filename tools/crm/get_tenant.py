"""
Tool: get_tenant_info
Retrieves tenant/resident information from the PMS.
Currently returns dummy data — replace with real PMS API call.
"""

from services import pms1


async def run(data: dict) -> dict:
    name = data.get("name")
    unit_number = data.get("unit_number")
    property_id = data.get("property_id")

    result = await pms1.get_tenant({
        "name": name,
        "unit_number": unit_number,
        "property_id": property_id,
    })

    return {
        "status": "success",
        "tenant": result,
    }
