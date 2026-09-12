# AgentCore Deployment Checklist

## Container

- Build ARM64 image.
- Expose host `0.0.0.0`.
- Use port `8000`.
- Serve MCP at `/mcp`.
- Keep state in DynamoDB or another backing store for stateless operation.

## MCP Protocol

- Support `POST /mcp`.
- Support `GET /mcp` if using 2025-11-25 Streamable HTTP behavior.
- Accept JSON-RPC messages.
- Implement `initialize`.
- Implement `tools/list`.
- Implement `tools/call`.
- Return JSON-RPC errors for unsupported methods.
- Preserve and return `Mcp-Session-Id`.
- Require `Accept: application/json, text/event-stream`.

## AWS Services

- AgentCore Runtime hosts the MCP server.
- AgentCore Gateway manages tool discovery/invocation.
- AgentCore Observability traces decisions and tool calls.
- DynamoDB stores household context, policies, incidents, decisions, and idempotency records.
- EventBridge receives normalized Ring events.
- Lambda runs workflow actions and notification adapters.
- Bedrock assists event interpretation and natural-language policy extraction.
- CloudWatch receives structured audit logs.

## Demo Readiness

- Verify MCP with MCP Inspector.
- Show `guardian.request_action` returning `BLOCK` for `unlock_door`.
- Show Ring webhook creating an incident.
- Show expected delivery producing no unnecessary alert.
- Show wellness workflow requiring approval before escalation.
