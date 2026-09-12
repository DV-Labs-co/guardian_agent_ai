# Guardian AI Submission Packet

## Text Description

Guardian AI is an Alexa+ household safety agent that coordinates smart-home events, household context, user-defined policies, and safety decisions before taking action.

Most smart-home systems detect events and send alerts. Guardian goes further: it decides what should happen next. When Alexa+ activates Guardian, the agent monitors household context, receives Ring-style front-door events, checks expected visitors and family routines, evaluates risk, applies Guardian Rules, and updates a Fire TV-style household command center.

The core decision pipeline is:

```text
Event -> Context -> Policy -> Risk -> Action -> Explanation
```

The demo shows Guardian handling an expected delivery quietly, detecting an unexpected visitor, starting a wellness check for an elderly parent, asking before consequential actions, and refusing to unlock the door automatically because household policy blocks it.

Guardian is intentionally not presented as an emergency-response system. It helps households interpret events and coordinate appropriate responses.

## Tracks And Mini Challenges

- Primary track: Alexa+
- Secondary/mini challenges: AWS Builder, Open Source
- Supporting ecosystem demo: Ring simulator/webhook, Fire TV-style command center

## Required Technology Evidence

### Alexa+

Guardian includes a Streamable HTTP-style MCP server endpoint:

```text
POST /mcp
GET /mcp
```

The code implements JSON-RPC MCP methods:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `tools/call`

Implemented Guardian MCP tools:

- `guardian.get_home_status`
- `guardian.get_recent_events`
- `guardian.get_household_context`
- `guardian.evaluate_event`
- `guardian.start_wellness_check`
- `guardian.request_action`
- `guardian.create_rule`

Source file:

```text
server/app.py
```

### Ring

Guardian includes a Ring simulator and production-style webhook endpoint:

```text
POST /webhooks/ring
```

The webhook supports:

- signed payload verification with `RING_WEBHOOK_SECRET`
- HMAC-SHA256 `X-Signature`
- idempotency tracking
- event normalization
- fast `202 Accepted` response
- mapping Ring events into Guardian decisions

### Fire TV

The Fire TV command center is implemented as a local web dashboard in:

```text
web/
```

For final submission, the demo video should show this running on an actual Fire TV device or the Fire TV/Vega simulator if entering Fire TV officially.

### AWS Builder

The local prototype is deterministic for judging. The production architecture maps to AWS:

- Amazon Bedrock for event interpretation, policy extraction, and explanation generation.
- Amazon Bedrock AgentCore Runtime for hosting the MCP server.
- Amazon Bedrock AgentCore Gateway for tool discovery/invocation.
- AgentCore Observability for tracing tool calls and decisions.
- AWS Lambda for workflow/tool execution.
- Amazon DynamoDB for household profiles, rules, incidents, decisions, and webhook idempotency.
- Amazon EventBridge for Ring event routing and incident workflow triggers.
- Amazon CloudWatch for structured audit logs.

## Public GitHub Repository Requirements

Before submission:

1. Push the `guardian-ai` folder to a public GitHub repo.
2. Make sure `LICENSE` is at the top level of the repo.
3. In GitHub repo settings/About, select the MIT license if GitHub detects it.
4. Confirm the README includes local setup instructions.
5. Confirm the repo contains source code, dashboard assets, docs, tests, and friction logs.

## Demo Video Under 3 Minutes

Recommended structure:

```text
0:00-0:10 Problem
Your smart home can detect problems. But who decides what to do?

0:10-0:25 Alexa+ activation
Click "Alexa: I'm Leaving" and show Guardian active.

0:25-0:40 Expected delivery
Click "Ring: Expected Delivery" and show Guardian logging without unnecessary interruption.

0:40-1:05 Unknown visitor
Click "Ring: Unknown Visitor" and show context, risk, and blocked unsafe actions.

1:05-1:35 Wellness check
Click "Check On Mom" and "Mom Missed 2nd Check-In". Show Fire TV command center.

1:35-1:55 Responsible AI refusal
Click "Unsafe Unlock Request". Show Guardian returning BLOCK.

1:55-2:15 Resolution
Click "Mom Responds". Show all clear and audit timeline.

2:15-2:45 Technical proof
Show /mcp tools, MCP invocation log, Ring webhook, and AWS architecture diagram.
```

## Product Feedback

See:

```text
PRODUCT-FEEDBACK.md
```

## Open Source Mini Challenge

Guardian includes a reusable open-source safety primitive:

```text
packages/guardian-policy-mcp
```

Concept:

```text
Agent intent -> Policy MCP -> ALLOW / ASK / BLOCK -> Tool execution
```

This package can become a reusable MCP policy gate for any agent that needs to control consequential actions safely.

## If Project Existed Before Hackathon

Use this statement if needed:

Guardian AI was created during the hackathon submission window as a standalone project. The work included the Guardian decision engine, Streamable HTTP-style MCP endpoint, Ring webhook simulator, Fire TV-style dashboard, natural-language rules, safety refusal workflow, AWS architecture docs, open-source policy MCP package starter, smoke tests, and friction logs.

## Feature Requests

See:

```text
FEATURE-REQUESTS.md
```

## Friction Logs

Friction logs are included in:

```text
friction-logs/
```

Current entries:

- Alexa+ MCP onboarding
- Ring webhooks
- Bedrock AgentCore deployment
- Fire TV dashboard/simulator path
