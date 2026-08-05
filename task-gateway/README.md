# Task Gateway (Vikunja Integration)

Agent task coordination layer wrapping Vikunja. Provides auto-routing, lease management, and a companion database for agent state.

## Connection

```yaml
vikunja_url: "http://kanban:3456"
vikunja_token: "tk_d53aaef35826470ba696fd668c3c031c0c7f8cae"  # Store in ~/.hermes/.env
gateway_url: "http://127.0.0.1:8420"
```

## Quick Start

```bash
cd ~/Documents/Workspace/task-gateway
pip install -e .
python -m uvicorn task_gateway.server:app --port 8420
```

## Register an Agent

```bash
curl -X POST http://127.0.0.1:8420/agents/register \
  -H "Content-Type: application/json" \
  -d '{"name":"hermes-1","capabilities":[],"max_tasks":2}'
```

Or with Python SDK:

```python
from task_sdk import TaskClient
client = TaskClient("hermes-1")
await client.register(capabilities=[], max_tasks=2)
```

## Auto-Route a Task

All agents are equally skilled. Tasks are distributed to the least-loaded agent:

```bash
curl -X POST "http://127.0.0.1:8420/tasks/auto-route?task_id=42"
```

Response:
```json
{"lease_id": 1, "task_id": 42, "agent": "hermes-1", "expires_at": "..."}
```

## Complete a Task

```bash
curl -X POST http://127.0.0.1:8420/tasks/complete \
  -H "Content-Type: application/json" \
  -d '{"agent_name":"hermes-1","task_id":42,"comment":"Done"}'
```

## Heartbeat (Keep Lease Alive)

```bash
curl -X POST http://127.0.0.1:8420/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"agent_name":"hermes-1"}'
```

Default lease expiry: 180s. Heartbeat extends it.

## Check Agent Status

```bash
curl http://127.0.0.1:8420/agents
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agents/register` | POST | Register/update an agent |
| `/agents` | GET | List all agents with status |
| `/tasks/auto-route` | POST | Auto-assign to least-loaded agent |
| `/tasks/claim` | POST | Manual claim by specific agent |
| `/tasks/complete` | POST | Mark done, release lease |
| `/tasks/release` | POST | Release without completing |
| `/heartbeat` | POST | Extend lease expiry |
| `/tasks/available/{agent}` | GET | Get available tasks for agent |
| `/vikunja/projects` | GET | List all projects |
| `/vikunja/tasks/{project_id}` | GET | List tasks in project |
| `/vikunja/tasks` | POST | Create new task |
| `/` | GET | Dashboard |

## Projects in Vikunja

```
Development / Hermes
Development / AGDATA-HUB
Infrastructure / VPS
Research / Papers
GitHub: TopHermDev/quizforge
GitHub: TopHermDev/QuestFill
GitHub: TopHermDev/student-tracker
```

## Architecture

```
You (Vikunja UI)
     │
     ▼
Vikunja REST API (v2)  ←  http://kanban:3456
     ▲
     │
Task Gateway (FastAPI)  ←  http://127.0.0.1:8420
     │
     ├─→ Agent SDK (Python)
     ├─→ MCP Server (tools)
     └─→ Companion DB (SQLite)
```
