import argparse
from typing import NotRequired, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from src.circuit_breaker import stop_reason, tool_call_fingerprint
from src.tools import (
    check_billing_balance,
    execute_wire_transfer,
    query_service_metrics,
    scale_kubernetes_cluster,
)


class MetricsState(TypedDict):
    service_name: str
    metrics: NotRequired[dict[str, str | float]]
    next_action: NotRequired[str]
    previous_fingerprint: NotRequired[str]
    completed_iterations: NotRequired[int]
    retry_demo: NotRequired[bool]
    use_saved_metrics: NotRequired[bool]
    billing_account_id: NotRequired[str | None]
    wire_demo: NotRequired[bool]


def circuit_breaker_node(state: MetricsState) -> Command:
    fingerprint = tool_call_fingerprint(
        "query_service_metrics",
        {"service_name": state["service_name"]},
    )
    reason = stop_reason(
        state.get("completed_iterations", 0),
        state.get("previous_fingerprint"),
        fingerprint,
    )

    if reason is not None:
        return Command(update={"next_action": reason}, goto=END)

    return Command(
        update={"previous_fingerprint": fingerprint},
        goto="tool_executor",
    )


def tool_executor_node(state: MetricsState):
    metrics = query_service_metrics(state["service_name"])
    return {
        "metrics": metrics,
        "completed_iterations": state.get("completed_iterations", 0) + 1,
    }


def request_wire_approval(state: MetricsState):
    recipient_id = "V-8812"
    amount_usd = 1500.0

    approved = interrupt(
        {
            "tool": "execute_wire_transfer",
            "recipient_id": recipient_id,
            "amount_usd": amount_usd,
            "risk": "HIGH",
        }
    )

    if approved is True:
        message = execute_wire_transfer(recipient_id, amount_usd)
        return {"next_action": message, "wire_demo": False}

    return {"next_action": "Wire transfer canceled.", "wire_demo": False}


def choose_next_node(state: MetricsState) -> str:
    if state.get("retry_demo", False):
        return "circuit_breaker"

    error_rate = float(state["metrics"]["error_rate_percent"])
    if error_rate > 5:
        return "request_approval"

    return "report_normal"


def request_approval(state: MetricsState):
    replica_count = 10
    approval = interrupt(
        {
            "service_name": state["service_name"],
            "replica_count": replica_count,
            "question": f"Approve scaling to {replica_count} replicas",
        }
    )

    if approval is True:
        message = scale_kubernetes_cluster(state["service_name"], replica_count)
        return {"next_action": message}

    return {"next_action": "Scaling canceled."}


def report_normal(state: MetricsState):
    return {"next_action": "No scaling needed."}


def report_saved(state: MetricsState):
    metrics = state.get("metrics")
    if metrics is None:
        return {
            "next_action": "Check a service first.",
            "use_saved_metrics": False,
        }

    service_name = metrics["service_name"]
    error_rate = float(metrics["error_rate_percent"])
    return {
        "next_action": f"{service_name} had a {error_rate:g}% error rate.",
        "use_saved_metrics": False,
    }


def report_billing_balance(state: MetricsState):
    account_id = state.get("billing_account_id")
    if not account_id:
        return {
            "next_action": "Enter an account ID.",
            "billing_account_id": None,
        }

    balance = check_billing_balance(account_id)
    return {
        "next_action": (
            f"{account_id} has a simulated balance of "
            f"${balance['balance_usd']:,.2f}."
        ),
        "billing_account_id": None,
    }


def choose_start_node(state: MetricsState) -> str:
    if state.get("wire_demo"):
        return "request_wire_approval"

    if state.get("billing_account_id") is not None:
        return "report_billing_balance"

    if state.get("use_saved_metrics"):
        return "report_saved"

    return "circuit_breaker"


builder = StateGraph(MetricsState)

builder.add_node("circuit_breaker", circuit_breaker_node)
builder.add_node("tool_executor", tool_executor_node)
builder.add_node("request_approval", request_approval)
builder.add_node("request_wire_approval", request_wire_approval)
builder.add_node("report_normal", report_normal)
builder.add_node("report_saved", report_saved)
builder.add_node("report_billing_balance", report_billing_balance)

builder.add_conditional_edges(START, choose_start_node)
builder.add_conditional_edges("tool_executor", choose_next_node)
builder.add_edge("request_approval", END)
builder.add_edge("request_wire_approval", END)
builder.add_edge("report_normal", END)
builder.add_edge("report_saved", END)
builder.add_edge("report_billing_balance", END)

graph = builder.compile(checkpointer=InMemorySaver())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--wire",
        action="store_true",
        help="Run the simulated wire transfer approval demo.",
    )
    args = parser.parse_args()

    config = {"configurable": {"thread_id": "approval-demo"}}
    paused = graph.invoke(
        {"service_name": "auth-service", "wire_demo": args.wire},
        config,
    )

    print("Approval request:", paused["__interrupt__"][0].value)
    decision = input("Type approve or reject: ").strip().lower()

    if decision not in {"approve", "reject"}:
        raise SystemExit("Please run again and type approve or reject.")

    result = graph.invoke(Command(resume=decision == "approve"), config)
    print(result["next_action"])