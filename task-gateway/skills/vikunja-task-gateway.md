---
name: vikunja-task-gateway
description: "Use when creating, claiming, or completing tasks via the Vikunja task gateway. Covers registration, auto-routing, heartbeats, and the agent SDK."
version: 1.0.0
author: Hermes Agent
tags: [vikunja, tasks, gateway, coordination, multi-agent]
---

# Vikunja Task Gateway

Use the task gateway to manage tasks across multiple agents. Vikunja is the human interface; the gateway handles agent coordination.

## Connection

- Vikunja: `http://kanban:3456` (Tailscale network)
- Gateway: `http://127.0.0.1:8420`
- Token: stored in `~/.hermes/.env` as `VIKUNJA_TOKEN`
- API version: Vikunja v2 (`/api/v2/`)

## Register as an Agent

```bash
curl -X POST http://127.0.0.1:8420/agents/register \
  -H "Content-Type: application/json" \
  -d '{"name":"hermes-<your-name>","capabilities":[],"max_tasks":2}'
```

All agents are equally skilled. Capabilities field is optional/empty.

## Get Work (Auto-Route)

Two ways tasks get auto-routed:

**Polling (automatic):** Gateway checks every 15s for unclaimed tasks and routes them to the least-loaded agent. No action needed.

**Manual:**
```bash
# Create a task
curl -X POST http://127.0.0.1:8420/vikunja/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Fix the thing","project_id":26}'

# Auto-route to least-loaded agent
curl -X POST "http://127.0.0.1:8420/tasks/auto-route?task_id=<id>"
```

## Heartbeat Loop

Run every 60s to keep your lease alive:

```bash
curl -X POST http://127.0.0.1:8420/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"agent_name":"hermes-<your-name>"}'
```

Lease expires after 180s without heartbeat. Expired tasks are auto-released.

## Complete a Task

```bash
curl -X POST http://127.0.0.1:8420/tasks/complete \
  -H "Content-Type: application/json" \
  -d '{"agent_name":"hermes-<your-name>","task_id":<id>,"comment":"Done"}'
```

## Python SDK

```python
from task_sdk import TaskClient

client = TaskClient("hermes-<your-name>")
await client.register(capabilities=[], max_tasks=2)
await client.start_heartbeat(interval=60)

task = await client.claim(task_id)
await client.complete(task_id, comment="Done")
```

## Check Status

```bash
curl http://127.0.0.1:8420/agents
```

## Vikunja Projects

Use these project IDs when creating tasks:
- `8` — Development / Hermes
- `9` — Development / AGDATA-HUB
- `11` — Infrastructure / VPS
- `15` — Research / Papers
- `39` — GitHub: TopHermDev/quizforge
- `40` — GitHub: TopHermDev/QuestFill
- `41` — GitHub: TopHermDev/student-tracker

## Pitfalls

- Gateway must be running on port 8420 for all agent operations
- Heartbeat loop must run continuously or lease expires in 180s
- Agent names must be unique across all registered agents
- If all agents are at capacity, auto-route returns `{"error": "All agents at capacity"}`
