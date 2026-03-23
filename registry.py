"""
Central Tool Registry
All available tools are defined here. GHL fetches this list via GET /tools
and selects the appropriate tool based on user intent.
"""

TOOLS = {
    "create_booking": {
        "description": "Create a new property booking/reservation in the PMS",
        "input_schema": {
            "customer_name": {"type": "string", "description": "Full name of the customer"},
            "property_id": {"type": "string", "description": "ID of the property to book"},
            "check_in": {"type": "string", "description": "Check-in date (YYYY-MM-DD)"},
            "check_out": {"type": "string", "description": "Check-out date (YYYY-MM-DD)"},
            "guests": {"type": "integer", "description": "Number of guests"},
        },
        "required": ["customer_name", "check_in", "check_out"],
        "handler": "tools.booking.create.run",
        "category": "booking",
    },
    "get_availability": {
        "description": "Check property availability for a given date range",
        "input_schema": {
            "property_id": {"type": "string", "description": "ID of the property"},
            "check_in": {"type": "string", "description": "Check-in date (YYYY-MM-DD)"},
            "check_out": {"type": "string", "description": "Check-out date (YYYY-MM-DD)"},
        },
        "required": ["check_in", "check_out"],
        "handler": "tools.booking.availability.run",
        "category": "booking",
    },
    "cancel_booking": {
        "description": "Cancel an existing booking by booking ID",
        "input_schema": {
            "booking_id": {"type": "string", "description": "Unique booking identifier"},
            "reason": {"type": "string", "description": "Reason for cancellation"},
        },
        "required": ["booking_id"],
        "handler": "tools.booking.cancel.run",
        "category": "booking",
    },
    "create_lead": {
        "description": "Create a new CRM lead/contact in GHL",
        "input_schema": {
            "name": {"type": "string", "description": "Full name of the lead"},
            "phone": {"type": "string", "description": "Phone number"},
            "email": {"type": "string", "description": "Email address"},
            "source": {"type": "string", "description": "Lead source (e.g. voice_ai, web, referral)"},
            "notes": {"type": "string", "description": "Additional notes about the lead"},
        },
        "required": ["name", "phone"],
        "handler": "tools.crm.create_lead.run",
        "category": "crm",
    },
    "update_lead": {
        "description": "Update an existing CRM lead's information",
        "input_schema": {
            "lead_id": {"type": "string", "description": "Unique lead identifier"},
            "phone": {"type": "string", "description": "Updated phone number"},
            "email": {"type": "string", "description": "Updated email address"},
            "status": {"type": "string", "description": "Lead status (new, contacted, qualified, closed)"},
            "notes": {"type": "string", "description": "Updated notes"},
        },
        "required": ["lead_id"],
        "handler": "tools.crm.update_lead.run",
        "category": "crm",
    },
    "generate_invoice": {
        "description": "Generate a billing invoice for a completed booking",
        "input_schema": {
            "booking_id": {"type": "string", "description": "Booking ID to invoice"},
            "customer_name": {"type": "string", "description": "Customer full name"},
            "amount": {"type": "number", "description": "Invoice amount in USD"},
            "due_date": {"type": "string", "description": "Payment due date (YYYY-MM-DD)"},
            "line_items": {"type": "array", "description": "List of itemized charges"},
        },
        "required": ["booking_id", "customer_name", "amount"],
        "handler": "tools.billing.generate_invoice.run",
        "category": "billing",
    },
    "get_tenant_info": {
        "description": "Retrieve tenant/resident details by name or unit number",
        "input_schema": {
            "name": {"type": "string", "description": "Tenant full name"},
            "unit_number": {"type": "string", "description": "Unit or apartment number"},
            "property_id": {"type": "string", "description": "Property ID"},
        },
        "required": [],
        "handler": "tools.crm.get_tenant.run",
        "category": "crm",
    },
    "log_maintenance_request": {
        "description": "Log a maintenance or repair request from a tenant",
        "input_schema": {
            "tenant_name": {"type": "string", "description": "Tenant's full name"},
            "unit_number": {"type": "string", "description": "Unit number"},
            "issue_type": {"type": "string", "description": "Type of issue (plumbing, electrical, HVAC, etc.)"},
            "description": {"type": "string", "description": "Detailed description of the issue"},
            "priority": {"type": "string", "description": "Priority level: low, medium, high, emergency"},
        },
        "required": ["tenant_name", "unit_number", "issue_type", "description"],
        "handler": "tools.booking.maintenance.run",
        "category": "maintenance",
    },
}
