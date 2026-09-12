# Product Feedback

## Alexa+ / MCP

### Used For

Guardian exposes household safety capabilities as MCP tools so Alexa+ can activate monitoring, inspect household context, evaluate events, start wellness checks, and request policy approval for consequential actions.

### What Worked Well

MCP is a strong fit because the project is not a chatbot. Guardian needs explicit tools, structured results, and auditable action boundaries.

### What Needs Work

The most important onboarding need is a complete Alexa+ MCP starter project using the required Streamable HTTP transport, including headers, session behavior, deployment path, and tool schema examples.

### Would We Build With It Again?

Yes. MCP is the right abstraction for safe smart-home orchestration because it makes tools visible and testable.

## Ring

### Used For

Guardian receives front-door events through a simulator and production-style webhook endpoint. The webhook maps person/package events into Guardian's decision engine.

### What Worked Well

Ring events create a strong real-world trigger for the agent. The household context layer makes those events more meaningful than simple alerts.

### What Needs Work

Hackathon teams would benefit from official sample webhook payloads, duplicate retry examples, signature examples, and local testing utilities.

### Would We Build With It Again?

Yes. Ring is a natural input source for household safety agents.

## Fire TV

### Used For

Guardian uses a Fire TV-style command center to show household status, active incidents, recommended actions, and all-clear resolution.

### What Worked Well

The living-room display turns the agent's internal state into something judges can see immediately.

### What Needs Work

A quickstart for showing a local web dashboard on Fire TV or Vega simulator would help teams move faster.

### Would We Build With It Again?

Yes, especially as a secondary interface for high-context household workflows.

## Amazon Bedrock

### Used For

Production Guardian would use Bedrock for event interpretation, policy extraction from natural language, and natural-language explanations of structured decisions.

### What Worked Well

Bedrock fits the reasoning and explanation layer while the policy engine keeps consequential action control deterministic.

### What Needs Work

More reference examples showing Bedrock working with MCP tools and explicit policy gates would help.

### Would We Build With It Again?

Yes. Bedrock is appropriate for the AI reasoning layer.

## Amazon Bedrock AgentCore

### Used For

Production Guardian would use AgentCore Runtime to host the MCP server, AgentCore Gateway for tool connectivity, and AgentCore Observability for traces.

### What Worked Well

AgentCore makes AWS central to the agent infrastructure rather than merely a hosting provider.

### What Needs Work

The deployment path should be as close to one-command as possible for sample MCP servers.

### Would We Build With It Again?

Yes, because the project needs runtime, gateway, and observability around agent tools.

## DynamoDB

### Used For

Production Guardian would store household profiles, routines, policies, incidents, decisions, and webhook idempotency records.

### What Worked Well

The data model is simple, event-driven, and well suited to DynamoDB access patterns.

### What Needs Work

A reference schema for event-driven agent memory would be useful.

### Would We Build With It Again?

Yes.

## EventBridge

### Used For

Production Guardian would route normalized Ring events into Guardian workflows.

### What Worked Well

EventBridge fits the event-driven nature of household safety workflows.

### What Needs Work

More examples of third-party webhook normalization into EventBridge for agent workflows would help.

### Would We Build With It Again?

Yes.

## Lambda

### Used For

Production Guardian would use Lambda for tool execution, notification adapters, and workflow steps.

### What Worked Well

Lambda is a natural fit for short-lived event handling and adapter code.

### What Needs Work

Examples connecting Lambda tools to AgentCore Gateway would help.

### Would We Build With It Again?

Yes.

## CloudWatch / AgentCore Observability

### Used For

Guardian uses local audit logs now. In production, CloudWatch and AgentCore Observability would trace decisions, tool calls, webhook handling, and safety refusals.

### What Worked Well

Observability is especially important because Guardian needs to explain why it acted or refused.

### What Needs Work

Agent-specific trace templates for decision pipelines would be useful.

### Would We Build With It Again?

Yes.
