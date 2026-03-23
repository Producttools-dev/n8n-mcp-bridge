# TenantVibe MCP Backend

FastAPI backend exposing a central MCP-compatible tool registry for GHL Voice AI.

## Architecture

```
GHL Voice AI (MCP Client)
        ↓
GET /tools  →  Central Tool Registry (FastAPI)
POST /run   →  Tool Executor → Individual Tools → PMS / GHL APIs
```

## Endpoints

| Method | Path     | Description                          |
|--------|----------|--------------------------------------|
| GET    | `/`      | Health check                         |
| GET    | `/tools` | List all available tools + schemas   |
| POST   | `/run`   | Execute a tool by name               |

### POST /run — Request body

```json
{
  "tool": "create_booking",
  "input": {
    "customer_name": "John Doe",
    "check_in": "2026-04-01",
    "check_out": "2026-04-05",
    "guests": 2
  }
}
```

### POST /run — Response

```json
{
  "tool": "create_booking",
  "status": "success",
  "output": {
    "status": "success",
    "booking_id": "BKG-A1B2C3D4",
    "confirmation_number": "CNF-E5F6G7",
    ...
  }
}
```

## Available Tools

| Tool Name               | Category    | Description                            |
|-------------------------|-------------|----------------------------------------|
| `create_booking`        | booking     | Create a new property reservation      |
| `get_availability`      | booking     | Check property availability            |
| `cancel_booking`        | booking     | Cancel an existing booking             |
| `log_maintenance_request` | maintenance | Log a tenant maintenance request     |
| `create_lead`           | crm         | Create a GHL CRM contact/lead          |
| `update_lead`           | crm         | Update an existing CRM lead            |
| `get_tenant_info`       | crm         | Look up tenant details                 |
| `generate_invoice`      | billing     | Generate a billing invoice             |

## Local Development

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for the interactive Swagger UI.

## Deployment on Render

1. Push this folder to a GitHub repo
2. Create a new **Web Service** on [Render](https://render.com)
3. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port 10000`
4. Add environment variables in Render dashboard:
   - `PMS1_API_URL`, `PMS1_API_KEY`
   - `PMS2_API_URL`, `PMS2_API_KEY`
   - `GHL_API_KEY`, `GHL_LOCATION_ID`

## GHL Voice AI Configuration

After deploying, set the MCP Base URL in GHL to:
```
https://your-app.onrender.com
```

GHL will call:
- `GET /tools` to discover available actions
- `POST /run` to execute selected tools

## Connecting Real APIs

Each service file contains a `# --- DUMMY IMPLEMENTATION ---` block. Replace it with the commented-out `httpx` call above it and set the corresponding env vars.

Files to update:
- `services/pms1.py` — Primary PMS (bookings, availability, tenants)
- `services/pms2.py` — Secondary PMS (invoices, maintenance tickets)
- `services/ghl.py`  — GoHighLevel CRM (contacts/leads)
