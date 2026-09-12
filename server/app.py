from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"
STATE_LOCK = threading.RLock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def initial_state() -> dict[str, Any]:
    return {
        "mode": "idle",
        "risk": "low",
        "progress": 0,
        "household": {
            "members": [
                {
                    "id": "john",
                    "name": "John",
                    "role": "owner",
                    "status": "away",
                    "routine": "Away weekdays 8AM-6PM",
                },
                {
                    "id": "mary",
                    "name": "Mary",
                    "role": "elderly parent",
                    "status": "home",
                    "routine": "Usually active by 9AM and answers Alexa check-ins",
                },
            ],
            "expected_visitors": [
                {"name": "Caregiver", "window": "Wednesday 2PM"},
                {"name": "Cleaner", "window": "Monday 10AM"},
            ],
            "areas": [
                {"name": "Front Door", "status": "secure"},
                {"name": "Living Room", "status": "normal"},
                {"name": "Kitchen", "status": "normal"},
            ],
        },
        "rules": [
            {
                "id": new_id("rule"),
                "source": "Never unlock the front door automatically.",
                "type": "deny_action",
                "condition": {"action": "unlock_door"},
                "effect": "block",
                "severity": "critical",
            },
            {
                "id": new_id("rule"),
                "source": "If Mom does not respond after two attempts, notify John.",
                "type": "wellness_escalation",
                "condition": {"person": "mary", "missed_responses": 2},
                "effect": "ask_to_contact_family",
                "severity": "high",
            },
            {
                "id": new_id("rule"),
                "source": "Do not wake me unless something is urgent.",
                "type": "notification_filter",
                "condition": {"quiet_hours": True, "minimum_risk": "high"},
                "effect": "suppress_low_risk_alerts",
                "severity": "medium",
            },
        ],
        "incidents": [],
        "decisions": [],
        "events": [],
        "mcp_calls": [],
        "processed_webhook_ids": [],
        "wellness": {
            "active": False,
            "person": "Mary",
            "attempts": 0,
            "status": "not started",
        },
        "fire_tv": {
            "visible": False,
            "headline": "Guardian idle",
            "message": "No active incident.",
            "actions": [],
        },
    }


GUARDIAN: dict[str, Any] = initial_state()


RISK_SCORE = {"low": 1, "moderate": 2, "high": 3, "critical": 4}


def log_event(state: dict[str, Any], event: str, detail: str, source: str = "Guardian") -> dict[str, Any]:
    row = {
        "id": new_id("evt"),
        "at": utc_now(),
        "event": event,
        "source": source,
        "detail": detail,
    }
    state["events"].append(row)
    print(json.dumps(row), file=sys.stderr, flush=True)
    return row


def mcp_call(state: dict[str, Any], tool: str, args: dict[str, Any], result: dict[str, Any]) -> None:
    state["mcp_calls"].append(
        {
            "id": new_id("mcp"),
            "at": utc_now(),
            "tool": tool,
            "args": args,
            "result": result,
        }
    )


def create_incident(state: dict[str, Any], kind: str, title: str, risk: str) -> dict[str, Any]:
    incident = {
        "id": new_id("inc"),
        "kind": kind,
        "title": title,
        "risk": risk,
        "status": "active",
        "created_at": utc_now(),
    }
    state["incidents"].append(incident)
    state["risk"] = max_risk(state["risk"], risk)
    mcp_call(state, "create_incident", {"kind": kind, "risk": risk}, incident)
    return incident


def max_risk(current: str, incoming: str) -> str:
    return incoming if RISK_SCORE[incoming] > RISK_SCORE[current] else current


def active_incidents(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [incident for incident in state["incidents"] if incident["status"] == "active"]


def resolve_incidents(state: dict[str, Any], kind: str | None = None) -> None:
    for incident in state["incidents"]:
        if kind is None or incident["kind"] == kind:
            incident["status"] = "resolved"
            incident["resolved_at"] = utc_now()
    unresolved = active_incidents(state)
    state["risk"] = max([item["risk"] for item in unresolved], key=lambda value: RISK_SCORE[value]) if unresolved else "low"


def context_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    owner = next(member for member in state["household"]["members"] if member["role"] == "owner")
    mom = next(member for member in state["household"]["members"] if member["id"] == "mary")
    return {
        "ownerAway": owner["status"] == "away",
        "elderlyParentHome": mom["status"] == "home",
        "expectedVisitor": bool(state.get("current_expected_visitor")),
        "expectedVisitorName": state.get("current_expected_visitor"),
        "activeIncidentCount": len(active_incidents(state)),
        "wellnessActive": state["wellness"]["active"],
    }


def policy_blocks(state: dict[str, Any], requested_actions: list[str]) -> list[dict[str, str]]:
    blocked: list[dict[str, str]] = []
    for action in requested_actions:
        for rule in state["rules"]:
            if rule["type"] == "deny_action" and rule["condition"].get("action") == action:
                blocked.append({"action": action, "policy": rule["source"], "severity": rule["severity"]})
    return blocked


def record_decision(
    state: dict[str, Any],
    event: str,
    risk: str,
    recommended_action: str,
    reason: str,
    context: dict[str, Any],
    requested_actions: list[str] | None = None,
    requires_approval: bool = False,
) -> dict[str, Any]:
    blocked = policy_blocks(state, requested_actions or [])
    decision = {
        "id": new_id("dec"),
        "at": utc_now(),
        "event": event,
        "context": context,
        "risk": risk,
        "recommendedAction": recommended_action,
        "requiresApproval": requires_approval,
        "blockedActions": blocked,
        "reason": reason,
        "pipeline": ["event", "context", "policy", "risk", "action", "explanation"],
    }
    state["decisions"].append(decision)
    state["risk"] = max_risk(state["risk"], risk)
    mcp_call(state, "evaluate_event_risk", {"event": event, "context": context}, decision)
    return decision


def show_fire_tv_alert(state: dict[str, Any], headline: str, message: str, actions: list[str]) -> None:
    state["fire_tv"] = {"visible": True, "headline": headline, "message": message, "actions": actions}
    mcp_call(state, "show_fire_tv_alert", {"headline": headline, "actions": actions}, state["fire_tv"])


def add_rule_from_text(state: dict[str, Any], text: str) -> dict[str, Any]:
    lowered = text.lower()
    if "never" in lowered and "unlock" in lowered:
        rule = {
            "id": new_id("rule"),
            "source": text,
            "type": "deny_action",
            "condition": {"action": "unlock_door"},
            "effect": "block",
            "severity": "critical",
        }
    elif "mom" in lowered and ("respond" in lowered or "answer" in lowered):
        rule = {
            "id": new_id("rule"),
            "source": text,
            "type": "wellness_escalation",
            "condition": {"person": "mary", "missed_responses": 2},
            "effect": "ask_to_contact_family",
            "severity": "high",
        }
    elif "wake" in lowered or "urgent" in lowered:
        rule = {
            "id": new_id("rule"),
            "source": text,
            "type": "notification_filter",
            "condition": {"quiet_hours": True, "minimum_risk": "high"},
            "effect": "suppress_low_risk_alerts",
            "severity": "medium",
        }
    else:
        rule = {
            "id": new_id("rule"),
            "source": text,
            "type": "human_review",
            "condition": {"natural_language": text},
            "effect": "ask_before_acting",
            "severity": "medium",
        }
    state["rules"].append(rule)
    mcp_call(state, "create_guardian_rule", {"source": text}, rule)
    log_event(state, "RULE_CREATED", f"Guardian converted policy text into {rule['type']}.", "Policy Engine")
    return rule


def simulate_action(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    with STATE_LOCK:
        state = GUARDIAN
        if action == "reset":
            state.clear()
            state.update(initial_state())
            log_event(state, "SYSTEM_RESET", "Guardian state reset for a clean demo.", "Demo")
            return state

        if action == "activate_guardian":
            state["mode"] = "monitoring"
            state["progress"] = 20
            log_event(state, "GUARDIAN_ACTIVATED", "Alexa+ activated Guardian monitoring mode.", "Alexa+")
            show_fire_tv_alert(state, "Guardian active", "Monitoring front door, household routines, and wellness context.", ["VIEW STATUS"])
            return state

        if action == "unknown_visitor":
            state["current_expected_visitor"] = None
            context = context_snapshot(state)
            create_incident(state, "front_door", "Unknown visitor at front door", "moderate")
            decision = record_decision(
                state,
                "unknown_person_at_front_door",
                "moderate",
                "notify_owner_and_continue_monitoring",
                "Owner is away, the visitor is not expected, and the elderly parent is home.",
                context,
                requested_actions=["unlock_door", "call_emergency_services"],
            )
            show_fire_tv_alert(
                state,
                "Unknown visitor detected",
                "Guardian notified John and blocked unsafe automatic door unlock.",
                ["CONTACT JOHN", "SHOW FRONT DOOR", "DISMISS"],
            )
            state["progress"] = max(state["progress"], 42)
            log_event(state, "RING_EVENT", "Ring simulator reported an unknown person at the front door.", "Ring")
            log_event(state, "DECISION_RECORDED", decision["reason"], "Decision Engine")
            return state

        if action == "expected_delivery":
            state["current_expected_visitor"] = "Amazon delivery"
            context = context_snapshot(state)
            decision = record_decision(
                state,
                "expected_delivery_detected",
                "low",
                "log_event_without_interrupting_owner",
                "The front-door visitor matches expected delivery context, so Guardian logs it without creating an unnecessary alert.",
                context,
            )
            show_fire_tv_alert(
                state,
                "Expected delivery",
                "Guardian logged the delivery and kept household monitoring quiet.",
                ["VIEW TIMELINE"],
            )
            state["current_expected_visitor"] = None
            state["progress"] = max(state["progress"], 34)
            log_event(state, "RING_EVENT", "Ring simulator reported an expected Amazon delivery.", "Ring")
            log_event(state, "DECISION_RECORDED", decision["reason"], "Decision Engine")
            return state

        if action == "start_wellness_check":
            state["wellness"] = {"active": True, "person": "Mary", "attempts": 1, "status": "waiting for response"}
            create_incident(state, "wellness", "Mary has not responded yet", "high")
            context = context_snapshot(state)
            decision = record_decision(
                state,
                "elderly_parent_no_response",
                "high",
                "ask_for_wellness_workflow_approval",
                "Mary has not responded and her normal activity has not been observed.",
                context,
                requested_actions=["contact_family"],
                requires_approval=True,
            )
            show_fire_tv_alert(
                state,
                "Wellness check active",
                "Mary has not responded. Guardian is waiting before escalating to family.",
                ["CONTACT MOM", "CALL FAMILY", "ESCALATE"],
            )
            state["progress"] = max(state["progress"], 72)
            log_event(state, "WELLNESS_CHECK_STARTED", "Guardian asked Alexa to check whether Mary is okay.", "Alexa+")
            log_event(state, "DECISION_RECORDED", decision["reason"], "Decision Engine")
            return state

        if action == "mom_second_miss":
            state["wellness"]["attempts"] = 2
            state["wellness"]["status"] = "second attempt missed"
            context = context_snapshot(state)
            decision = record_decision(
                state,
                "two_missed_wellness_responses",
                "high",
                "request_approval_to_contact_family",
                "The household rule says to notify John after two missed responses.",
                context,
                requested_actions=["contact_family"],
                requires_approval=True,
            )
            show_fire_tv_alert(
                state,
                "Family contact recommended",
                "Mary missed two check-ins. Guardian is asking before contacting family.",
                ["CALL JOHN", "TRY AGAIN", "ESCALATE"],
            )
            state["progress"] = max(state["progress"], 86)
            log_event(state, "POLICY_TRIGGERED", "Rule matched: notify John after two missed responses.", "Policy Engine")
            log_event(state, "DECISION_RECORDED", decision["reason"], "Decision Engine")
            return state

        if action == "mom_responds":
            state["wellness"] = {"active": False, "person": "Mary", "attempts": state["wellness"].get("attempts", 1), "status": "Mary confirmed she is okay"}
            resolve_incidents(state, "wellness")
            record_decision(
                state,
                "wellness_confirmed_clear",
                "low",
                "resolve_wellness_incident",
                "Mary responded through Alexa and confirmed she is okay.",
                context_snapshot(state),
            )
            show_fire_tv_alert(state, "All clear", "Mary responded. Guardian resolved the wellness incident.", ["VIEW TIMELINE"])
            state["progress"] = 100 if state["mode"] == "monitoring" else state["progress"]
            log_event(state, "INCIDENT_RESOLVED", "Mary confirmed she is okay.", "Alexa+")
            return state

        if action == "unsafe_unlock_request":
            context = context_snapshot(state)
            decision = record_decision(
                state,
                "user_requested_unlock_for_unknown_visitor",
                "moderate",
                "refuse_unsafe_action",
                "Guardian cannot unlock the door because the visitor is unidentified and policy forbids automatic unlocks.",
                context,
                requested_actions=["unlock_door"],
                requires_approval=True,
            )
            show_fire_tv_alert(state, "Unsafe action blocked", decision["reason"], ["NOTIFY OWNER", "SHOW CAMERA"])
            log_event(state, "ACTION_BLOCKED", decision["reason"], "Safety Engine")
            return state

        if action == "package_delivery":
            context = context_snapshot(state)
            decision = record_decision(
                state,
                "package_detected_at_front_door",
                "low",
                "inform_owner",
                "A package is present at the front door. No unsafe action is needed.",
                context,
            )
            show_fire_tv_alert(state, "Package detected", "Guardian logged the delivery and kept monitoring.", ["VIEW FRONT DOOR"])
            log_event(state, "RING_EVENT", "Ring simulator reported a package delivery.", "Ring")
            log_event(state, "DECISION_RECORDED", decision["reason"], "Decision Engine")
            return state

        raise ValueError(f"unknown action: {action}")


def mcp_tool_catalog() -> list[dict[str, Any]]:
    return [
        {
            "name": "guardian.get_home_status",
            "description": "Return current household mode, risk, incidents, and area status.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "guardian.get_recent_events",
            "description": "Return Guardian's auditable event timeline.",
            "inputSchema": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 50}},
                "additionalProperties": False,
            },
        },
        {
            "name": "guardian.get_household_context",
            "description": "Return routines, people, expected visitors, and active context.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "guardian.evaluate_event",
            "description": "Evaluate a household event through context, policy, risk, action, and explanation.",
            "inputSchema": {
                "type": "object",
                "properties": {"event_type": {"type": "string", "enum": ["unknown_visitor", "expected_delivery", "package_delivery", "unsafe_unlock_request"]}},
                "required": ["event_type"],
                "additionalProperties": False,
            },
        },
        {
            "name": "guardian.start_wellness_check",
            "description": "Begin a policy-governed check-in workflow for a household member.",
            "inputSchema": {
                "type": "object",
                "properties": {"person_id": {"type": "string", "default": "mary"}},
                "additionalProperties": False,
            },
        },
        {
            "name": "guardian.request_action",
            "description": "Ask the policy engine whether a consequential action should be ALLOW, ASK, or BLOCK.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["action"],
                "additionalProperties": False,
            },
        },
        {
            "name": "guardian.create_rule",
            "description": "Convert natural language household policy into a structured Guardian rule.",
            "inputSchema": {
                "type": "object",
                "properties": {"rule": {"type": "string"}},
                "required": ["rule"],
                "additionalProperties": False,
            },
        },
    ]


def mcp_result(request_id: Any, payload: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": payload}


def mcp_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def text_content(payload: Any) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(payload, indent=2)}]}


def call_guardian_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    with STATE_LOCK:
        if name == "guardian.get_home_status":
            return text_content(
                {
                    "mode": GUARDIAN["mode"],
                    "risk": GUARDIAN["risk"],
                    "progress": GUARDIAN["progress"],
                    "incidents": active_incidents(GUARDIAN),
                    "wellness": GUARDIAN["wellness"],
                    "fire_tv": GUARDIAN["fire_tv"],
                }
            )
        if name == "guardian.get_recent_events":
            limit = int(args.get("limit", 20))
            return text_content({"events": GUARDIAN["events"][-limit:]})
        if name == "guardian.get_household_context":
            return text_content({"household": GUARDIAN["household"], "context": context_snapshot(GUARDIAN), "rules": GUARDIAN["rules"]})
        if name == "guardian.evaluate_event":
            event_type = args.get("event_type")
            action_map = {
                "unknown_visitor": "unknown_visitor",
                "expected_delivery": "expected_delivery",
                "package_delivery": "package_delivery",
                "unsafe_unlock_request": "unsafe_unlock_request",
            }
            if event_type not in action_map:
                raise ValueError("unsupported event_type")
            return text_content(simulate_action(action_map[event_type]))
        if name == "guardian.start_wellness_check":
            return text_content(simulate_action("start_wellness_check"))
        if name == "guardian.request_action":
            action = str(args.get("action", "")).strip()
            blocked = policy_blocks(GUARDIAN, [action])
            if blocked:
                decision = {"decision": "BLOCK", "reason": blocked[0]["policy"], "action": action}
            elif action in {"contact_family", "escalate_incident", "unlock_door"}:
                decision = {"decision": "ASK", "reason": "Consequential action requires human approval.", "action": action}
            else:
                decision = {"decision": "ALLOW", "reason": "Informational action is allowed.", "action": action}
            mcp_call(GUARDIAN, "guardian.request_action", args, decision)
            return text_content(decision)
        if name == "guardian.create_rule":
            return text_content(add_rule_from_text(GUARDIAN, str(args.get("rule", "")).strip()))
    raise ValueError(f"unknown tool: {name}")


def handle_mcp_message(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    if not method:
        return mcp_error(request_id, -32600, "Invalid JSON-RPC request")

    if method == "initialize":
        return mcp_result(
            request_id,
            {
                "protocolVersion": message.get("params", {}).get("protocolVersion", "2025-11-25"),
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "guardian-ai-mcp", "version": "0.1.0"},
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return mcp_result(request_id, {"tools": mcp_tool_catalog()})
    if method == "tools/call":
        params = message.get("params") or {}
        try:
            result = call_guardian_tool(str(params.get("name", "")), params.get("arguments") or {})
        except ValueError as exc:
            return mcp_error(request_id, -32602, str(exc))
        return mcp_result(request_id, result)
    return mcp_error(request_id, -32601, f"Unsupported MCP method: {method}")


def verify_ring_signature(raw_body: bytes, signature: str | None) -> bool:
    secret = os.getenv("RING_WEBHOOK_SECRET")
    if not secret:
        return True
    if not signature:
        return False
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    provided = signature.removeprefix("sha256=").strip()
    return hmac.compare_digest(expected, provided)


def handle_ring_event(payload: dict[str, Any]) -> dict[str, Any]:
    webhook_id = str(payload.get("id") or payload.get("event_id") or payload.get("notification_id") or "").strip()
    if webhook_id:
        with STATE_LOCK:
            if webhook_id in GUARDIAN["processed_webhook_ids"]:
                log_event(GUARDIAN, "RING_WEBHOOK_DUPLICATE", f"Duplicate Ring webhook ignored: {webhook_id}.", "Ring")
                return GUARDIAN
            GUARDIAN["processed_webhook_ids"].append(webhook_id)

    event_type = str(payload.get("event_type") or payload.get("type") or "").lower()
    is_expected = bool(payload.get("expected")) or "expected" in event_type
    if is_expected and ("person" in event_type or "delivery" in event_type):
        return simulate_action("expected_delivery")
    if "package" in event_type:
        return simulate_action("package_delivery")
    if "person" in event_type or "motion" in event_type:
        return simulate_action("unknown_visitor")
    with STATE_LOCK:
        log_event(GUARDIAN, "RING_WEBHOOK_IGNORED", f"Unsupported Ring event: {event_type or 'unknown'}.", "Ring")
        return GUARDIAN


def json_response(handler: BaseHTTPRequestHandler, status: int, body: Any) -> None:
    payload = json.dumps(body, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def mcp_json_response(handler: BaseHTTPRequestHandler, status: int, body: Any) -> None:
    payload = json.dumps(body, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Mcp-Session-Id", handler.headers.get("Mcp-Session-Id") or new_id("sess"))
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def serve_file(handler: BaseHTTPRequestHandler, base_dir: Path, relative_path: str) -> None:
    file_path = (base_dir / relative_path).resolve()
    if not str(file_path).startswith(str(base_dir.resolve())) or not file_path.exists():
        handler.send_error(404)
        return
    content = file_path.read_bytes()
    content_type = "text/plain; charset=utf-8"
    if file_path.suffix == ".html":
        content_type = "text/html; charset=utf-8"
    elif file_path.suffix == ".css":
        content_type = "text/css; charset=utf-8"
    elif file_path.suffix == ".js":
        content_type = "application/javascript; charset=utf-8"
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(content)))
    handler.end_headers()
    handler.wfile.write(content)


class Handler(BaseHTTPRequestHandler):
    def validate_origin(self) -> bool:
        origin = self.headers.get("Origin")
        if not origin:
            return True
        allowed = os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1,http://localhost").split(",")
        return any(origin.startswith(item.strip()) for item in allowed if item.strip())

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/mcp":
            if not self.validate_origin():
                mcp_json_response(self, 403, mcp_error(None, -32003, "Forbidden origin"))
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            self.wfile.write(b'event: message\ndata: {"jsonrpc":"2.0","method":"notifications/message","params":{"level":"info","data":"Guardian MCP stream ready"}}\n\n')
            return
        if parsed.path == "/api/guardian":
            with STATE_LOCK:
                json_response(self, 200, GUARDIAN)
            return
        if parsed.path == "/api/mcp/tools":
            json_response(self, 200, {"tools": mcp_tool_catalog()})
            return
        serve_file(self, WEB_DIR, "index.html" if parsed.path == "/" else parsed.path.lstrip("/"))

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length) or b"{}"
        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            if parsed.path == "/mcp":
                mcp_json_response(self, 400, mcp_error(None, -32700, "Parse error"))
            else:
                json_response(self, 400, {"error": "invalid JSON body"})
            return

        if parsed.path == "/mcp":
            if not self.validate_origin():
                mcp_json_response(self, 403, mcp_error(body.get("id"), -32003, "Forbidden origin"))
                return
            accept = self.headers.get("Accept", "")
            if "application/json" not in accept or "text/event-stream" not in accept:
                mcp_json_response(self, 406, mcp_error(body.get("id"), -32004, "MCP requires Accept: application/json, text/event-stream"))
                return
            response = handle_mcp_message(body)
            if response is None:
                self.send_response(202)
                self.send_header("Mcp-Session-Id", self.headers.get("Mcp-Session-Id") or new_id("sess"))
                self.end_headers()
                return
            mcp_json_response(self, 200, response)
            return

        if parsed.path == "/webhooks/ring":
            if not verify_ring_signature(raw_body, self.headers.get("X-Signature")):
                json_response(self, 401, {"error": "invalid Ring webhook signature"})
                return
            state = handle_ring_event(body)
            json_response(self, 202, {"accepted": True, "event_count": len(state["events"])})
            return

        if parsed.path == "/api/simulate":
            try:
                state = simulate_action(str(body.get("action", "")), body.get("payload") or {})
            except ValueError as exc:
                json_response(self, 400, {"error": str(exc)})
                return
            json_response(self, 200, state)
            return

        if parsed.path == "/api/rules":
            text = str(body.get("rule", "")).strip()
            if len(text) < 8:
                json_response(self, 400, {"error": "rule must include at least 8 characters"})
                return
            with STATE_LOCK:
                add_rule_from_text(GUARDIAN, text)
                json_response(self, 201, GUARDIAN)
            return

        self.send_error(404)


def run_cli_demo() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for action in ["reset", "activate_guardian", "unknown_visitor", "start_wellness_check", "mom_second_miss", "unsafe_unlock_request", "mom_responds"]:
        simulate_action(action)
        time.sleep(0.05)
    with STATE_LOCK:
        latest = GUARDIAN["decisions"][-1]
        print("Guardian AI demo completed.")
        print(f"Mode: {GUARDIAN['mode']}")
        print(f"Risk: {GUARDIAN['risk']}")
        print(f"Decisions: {len(GUARDIAN['decisions'])}")
        print(f"Latest action: {latest['recommendedAction']}")
        print(f"Latest reason: {latest['reason']}")
    return 0


def main() -> None:
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Guardian AI running on http://{host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "guardian:demo":
        raise SystemExit(run_cli_demo())
    main()
