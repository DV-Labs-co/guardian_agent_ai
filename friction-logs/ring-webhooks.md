# Friction Log: Ring Webhooks

## Task

Receive Ring front-door events through HTTPS webhooks.

## Expected

Webhook events arrive as signed HTTPS POST payloads and can be acknowledged quickly.

## Actual

Local prototype implements `/webhooks/ring`, HMAC-SHA256 verification when `RING_WEBHOOK_SECRET` is configured, event normalization, and idempotency.

## Severity

Medium until partner credentials are available.

## Workaround

Use simulated `PERSON_DETECTED` and `PACKAGE_DETECTED` webhook payloads for local judging.

## Suggestion

Provide sample event payloads for person, package, motion, and duplicate callback retries.

## Impact

Sample payloads would make it easier to build robust event validation and demo-ready tests.
