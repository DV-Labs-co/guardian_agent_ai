from __future__ import annotations

import importlib.util
from pathlib import Path


APP_PATH = Path(__file__).resolve().parents[1] / "server" / "app.py"
SPEC = importlib.util.spec_from_file_location("guardian_app", APP_PATH)
assert SPEC and SPEC.loader
guardian = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guardian)


def reset() -> None:
    guardian.simulate_action("reset")


def test_expected_delivery_stays_low_risk() -> None:
    reset()
    state = guardian.simulate_action("expected_delivery")
    assert state["risk"] == "low"
    assert state["decisions"][-1]["recommendedAction"] == "log_event_without_interrupting_owner"
    assert state["decisions"][-1]["context"]["expectedVisitor"] is True


def test_unknown_visitor_blocks_unlock() -> None:
    reset()
    state = guardian.simulate_action("unknown_visitor")
    latest = state["decisions"][-1]
    assert latest["risk"] == "moderate"
    assert latest["blockedActions"][0]["action"] == "unlock_door"


def test_policy_request_action_blocks_door_unlock() -> None:
    reset()
    result = guardian.call_guardian_tool("guardian.request_action", {"action": "unlock_door"})
    assert '"decision": "BLOCK"' in result["content"][0]["text"]


def test_mcp_lists_guardian_tools() -> None:
    response = guardian.handle_mcp_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    names = [tool["name"] for tool in response["result"]["tools"]]
    assert "guardian.evaluate_event" in names
    assert "guardian.request_action" in names


def test_ring_webhook_idempotency() -> None:
    reset()
    first = guardian.handle_ring_event({"event_id": "ring-1", "event_type": "PERSON_DETECTED"})
    first_event_count = len(first["events"])
    second = guardian.handle_ring_event({"event_id": "ring-1", "event_type": "PERSON_DETECTED"})
    assert len(second["events"]) == first_event_count + 1
    assert second["events"][-1]["event"] == "RING_WEBHOOK_DUPLICATE"


if __name__ == "__main__":
    tests = [
        test_expected_delivery_stays_low_risk,
        test_unknown_visitor_blocks_unlock,
        test_policy_request_action_blocks_door_unlock,
        test_mcp_lists_guardian_tools,
        test_ring_webhook_idempotency,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
