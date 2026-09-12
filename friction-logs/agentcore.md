# Friction Log: Bedrock AgentCore

## Task

Deploy Guardian as a Streamable HTTP MCP server on Amazon Bedrock AgentCore Runtime.

## Expected

Container listens on `0.0.0.0:8000` and exposes `/mcp`.

## Actual

Local Dockerfile is aligned to port `8000`. Real deployment is pending AWS account configuration, IAM, image publishing, and runtime creation.

## Severity

High for AWS Builder scoring.

## Workaround

Run locally on `127.0.0.1:8091` for development and test `/mcp` using JSON-RPC requests.

## Suggestion

Add a one-command deployment path for sample MCP servers, including IAM policy examples and MCP Inspector validation steps.

## Impact

Deployment clarity would help teams prove AWS usage earlier and spend more time on differentiated agent behavior.
