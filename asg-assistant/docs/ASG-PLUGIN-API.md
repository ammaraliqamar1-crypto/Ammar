# ASG Plugin API (contract between ASG server and ASG Assistant)

In ASG Assistant → Settings, set **ASG server URL** (e.g. `http://192.168.1.10:3000`) and an **access token**.
Leave the URL empty to use built-in demo data.

The ASG server must expose one discovery endpoint. The assistant sends `Authorization: Bearer <token>` on every call.

## `GET /assistant/manifest`
```json
{
  "name": "ASG",
  "tools": [
    {
      "name": "list_inquiries",
      "description": "List inquiries/RFQs, optionally filtered by status.",
      "parameters": { "type": "object", "properties": { "status": { "type": "string" } } },
      "risk": "read",
      "method": "GET",
      "path": "/api/inquiries"
    },
    {
      "name": "update_inquiry_status",
      "description": "Change the status of an inquiry.",
      "parameters": {
        "type": "object",
        "properties": { "id": { "type": "string" }, "status": { "type": "string" } },
        "required": ["id", "status"]
      },
      "risk": "write",
      "method": "POST",
      "path": "/api/inquiries/status"
    }
  ]
}
```

- `risk: "read"` runs immediately; `risk: "write"` always asks the user to approve first.
- GET/DELETE send arguments as query string; POST/PUT/PATCH send JSON body.
- Return JSON (or text). Use HTTP 4xx/5xx for errors; the assistant shows the message.
- Any new tool you add to the manifest becomes available to the AI automatically (LPO register, BOQ lookup, project status, etc.).

## Offline behaviour
- Server unreachable: read tools return the last cached result (flagged with its timestamp); write tools are queued and replayed automatically when the server is back.
- No internet: the assistant switches to the local Ollama model (`ollama pull llama3.1`). Use a tool-capable model.
