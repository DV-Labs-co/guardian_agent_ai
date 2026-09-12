# Guardian AI

Guardian AI is an Alexa+ household safety agent prototype. It coordinates smart-home events, household context, natural-language rules, and safety policy before deciding what action to take.

The central idea:

```text
Smart homes detect events. Guardian decides what should happen next.
```

## Why It Can Win

Guardian is not a generic chatbot and it is not a simple Ring alert. It demonstrates an agentic safety workflow:

```text
Event -> Context -> Policy -> Risk -> Action -> Explanation
```

The demo shows:

- Alexa+ activating Guardian when the owner leaves.
- Ring-style front-door events entering the agent workflow.
- Household memory for family members, routines, and expected visitors.
- Guardian Rules that convert natural-language policies into structured rules.
- A visible safety refusal when the user asks for an unsafe door unlock.
- A wellness workflow for an elderly parent.
- A Fire TV-style command center for household status and incident actions.
- An MCP-style tool catalog for Alexa+ agent orchestration.

## Local Setup

Requires Python 3.11+.

```powershell
cd guardian-ai
python server/app.py
```

Open:

```text
http://127.0.0.1:8080
```

Run the CLI demo:

```powershell
python server/app.py guardian:demo
```

## Winning Demo Flow

1. Click **Alexa: I'm Leaving**.
2. Click **Ring: Expected Delivery** to show Guardian avoiding unnecessary interruption.
3. Click **Ring: Unknown Visitor**.
4. Show the Decision Engine output and blocked actions.
5. Click **Check On Mom**.
6. Click **Mom Missed 2nd Check-In**.
7. Show the Fire TV command center recommending family contact.
8. Click **Unsafe Unlock Request**.
9. Show Guardian refusing the unlock because of household policy.
10. Click **Mom Responds**.
11. Show the all-clear state, audit timeline, and MCP invocation log.

## MCP Tool Surface

The prototype exposes a Streamable HTTP-style MCP endpoint at:

```text
POST /mcp
GET /mcp
```

The endpoint accepts JSON-RPC MCP messages for `initialize`, `tools/list`, and `tools/call`. The local dashboard also exposes the readable catalog at:

```text
GET /api/mcp/tools
```

Implemented tools:

- `guardian.get_home_status`
- `guardian.get_recent_events`
- `guardian.get_household_context`
- `guardian.evaluate_event`
- `guardian.start_wellness_check`
- `guardian.request_action`
- `guardian.create_rule`

Example MCP tool call:

Initialize the MCP session first:

```powershell
$init = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"guardian-demo","version":"1.0.0"}}}'

Invoke-WebRequest http://127.0.0.1:8080/mcp `
  -Method POST `
  -ContentType 'application/json' `
  -Headers @{ Accept = 'application/json, text/event-stream' } `
  -Body $init

$initialized = '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}'

Invoke-WebRequest http://127.0.0.1:8080/mcp `
  -Method POST `
  -ContentType 'application/json' `
  -Headers @{ Accept = 'application/json, text/event-stream' } `
  -Body $initialized

Invoke-WebRequest http://127.0.0.1:8080/mcp `
  -Method POST `
  -ContentType 'application/json' `
  -Headers @{ Accept = 'application/json, text/event-stream' } `
  -Body '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"guardian.request_action","arguments":{"action":"unlock_door"}}}'
```

## API

Get Guardian state:

```text
GET /api/guardian
```

Simulate a smart-home event:

```text
POST /api/simulate
```

Example body:

```json
{
  "action": "unknown_visitor"
}
```

Supported actions:

- `reset`
- `activate_guardian`
- `expected_delivery`
- `unknown_visitor`
- `start_wellness_check`
- `mom_second_miss`
- `unsafe_unlock_request`
- `mom_responds`
- `package_delivery`

Add a natural-language Guardian Rule:

```text
POST /api/rules
```

Example body:

```json
{
  "rule": "Never unlock the front door automatically."
}
```

Receive a production-style Ring webhook:

```text
POST /webhooks/ring
```

Example body:

```json
{
  "event_type": "PERSON_DETECTED",
  "location": "front_door"
}
```

If `RING_WEBHOOK_SECRET` is set, the endpoint verifies `X-Signature` using HMAC-SHA256 before accepting the event.

## AWS Builder Architecture

The local app is deterministic so judging is reliable without credentials. The production version maps cleanly to AWS:

- Amazon Bedrock: event interpretation, policy extraction, explanation generation.
- AWS Lambda: MCP tool execution and workflow steps.
- Amazon DynamoDB: household profiles, routines, rules, incidents, decisions, and events.
- Amazon EventBridge: Ring event routing and incident workflow triggers.
- Amazon CloudWatch: decision audit logs and operational traces.
- Amazon Bedrock AgentCore Runtime: hosts the Streamable HTTP MCP server at `/mcp`.
- Amazon Bedrock AgentCore Gateway: tool discovery and invocation across Guardian and Amazon capability adapters.
- AgentCore Observability: traces tool calls, decisions, refusals, and workflow steps.
- Fire TV app/web view: household command center.
- Alexa+ Agent Skill/MCP server: voice and agent orchestration layer.

## Safety Model

Guardian uses three safety levels:

- Green: inform automatically.
- Yellow: ask for human approval.
- Red: block or escalate only under explicit policy.

The prototype intentionally demonstrates refusal:

```text
Guardian cannot unlock the door because the visitor is unidentified and policy forbids automatic unlocks.
```

That refusal is a feature. It shows responsible agentic behavior.

## Open Source Angle

For the open-source mini challenge, extract the reusable layer as `guardian-mcp`:

```text
guardian-mcp/
  server/
  tools/
  policies/
  context/
  workflows/
  examples/
```

The pitch:

```text
An open-source MCP framework for building context-aware household safety agents.
```

The reusable package starter lives at:

```text
packages/guardian-policy-mcp
```

## Submission Artifacts

- `docs/architecture.md`: technical architecture and production mapping.
- `deployment/agentcore-checklist.md`: AgentCore deployment checklist.
- `friction-logs/`: bonus-ready friction log drafts.
- `sample-data/demo-script.md`: 2-minute demo script.
