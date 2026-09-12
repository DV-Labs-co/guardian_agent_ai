# Friction Log: Alexa+ MCP

## Task

Connect Alexa+ to Guardian through a Streamable HTTP MCP endpoint.

## Expected

Alexa+ can discover tools from `/mcp` and call Guardian tools through JSON-RPC.

## Actual

Pending real Alexa+ integration. Local prototype implements `initialize`, `tools/list`, and `tools/call` for validation with MCP Inspector.

## Severity

High for final submission.

## Workaround

Use local MCP endpoint and MCP Inspector until Alexa+ credentials/onboarding are available.

## Suggestion

Provide a minimal Alexa+ MCP starter template with Streamable HTTP, tool schemas, and required headers.

## Impact

Clearer onboarding would reduce time spent interpreting protocol details and let teams focus on product quality.
