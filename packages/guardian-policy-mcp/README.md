# guardian-policy-mcp

`guardian-policy-mcp` is the reusable open-source primitive inside Guardian AI.

It answers one question:

```text
An agent wants to take an action. Should it be allowed, require approval, or be blocked?
```

## Tool Concept

```text
guardian.request_action(action, reason, context)
```

Returns:

```json
{
  "decision": "BLOCK",
  "reason": "Automatic door access is disabled by household policy.",
  "action": "unlock_door"
}
```

## Why This Matters

Most agent demos connect an LLM directly to tools. That is unsafe for consequential actions.

This package puts a policy gate between agent intent and real-world capability:

```text
Agent intent -> Policy MCP -> ALLOW / ASK / BLOCK -> Tool execution
```

## Decisions

- `ALLOW`: informational or low-risk action can proceed.
- `ASK`: consequential action requires human approval.
- `BLOCK`: action violates explicit policy.

## Example Policies

```json
[
  {
    "source": "Never unlock the front door automatically.",
    "type": "deny_action",
    "condition": { "action": "unlock_door" },
    "effect": "block"
  },
  {
    "source": "If Mom does not respond after two attempts, notify John.",
    "type": "wellness_escalation",
    "condition": { "person": "mary", "missed_responses": 2 },
    "effect": "ask_to_contact_family"
  }
]
```

## Hackathon Scope

The current implementation lives in `guardian-ai/server/app.py`. The next extraction step is to move:

- `policy_blocks`
- `add_rule_from_text`
- `guardian.request_action`
- policy schemas

into this package as a standalone MCP server.
