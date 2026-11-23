# Service Metrics Agent

A Python application built with LangGraph and Streamlit that demonstrates service monitoring, human approval, saved state, and protection against repeated tool calls.

The project uses simulated service metrics, billing balances, scaling actions, and wire transfers.

## Features

- Check service error rates.
- Request human approval when the error rate exceeds 5%.
- Approve or reject simulated scaling.
- Recall previously saved service metrics.
- Look up a simulated billing balance.
- Approve or reject a simulated wire transfer.
- Stop repeated tool calls and enforce a six-iteration limit.
- Inspect graph state through the Streamlit interface.

## Technologies

- Python 3.11
- LangGraph
- Streamlit
- pytest
- uv

## Project Files

| File | Purpose |
| --- | --- |
| `src/tools.py` | Defines the simulated metrics, scaling, billing, and wire transfer tools. |
| `src/graph.py` | Defines the graph state, nodes, routing, approval pauses, and checkpoints. |
| `src/circuit_breaker.py` | Creates tool-call fingerprints and checks stopping conditions. |
| `src/app.py` | Provides the Streamlit interface and graph state display. |
| `tests/test_cycle_breaker.py` | Tests repeated calls, iteration limits, and fingerprint consistency. |
| `tests/test_graph_flow.py` | Tests service checks, saved metrics, and follow-up requests. |
| `tests/test_hitl_approval.py` | Tests approval and rejection of simulated scaling. |
| `pyproject.toml` | Lists project dependencies and configuration. |
| `uv.lock` | Records resolved dependency versions. |

## Installation

Install Python 3.11 and uv. Open a terminal in the project folder and run:

```bash
uv sync
```

## Run the Website

```bash
uv run python -m streamlit run src/app.py
```

Open http://localhost:8501.

### Check a Service

1. Select `billing-service`.
2. Click **Check service**.
3. The sample error rate is 3%, so the result is **No scaling needed.**
4. Click **Recall last error rate** to retrieve the saved metrics.

### Test Human Approval

1. Select `auth-service`.
2. Click **Check service**.
3. Its sample error rate is 8%, so the graph requests approval.
4. Click **Reject** to cancel scaling.
5. Repeat the check and click **Approve** to run simulated scaling.

### Test Repeated Calls

Click **Test repeated tool call**.

The expected result is:

```text
Detected a repeated tool call.
```

Expand **Graph state** to inspect the saved metrics, fingerprint, and completed iteration count.

## Run the Terminal Demos

### Scaling Approval

```bash
uv run python -m src.graph
```

Enter `approve` or `reject` when prompted.

### Wire Transfer Approval

```bash
uv run python -m src.graph --wire
```

The graph requests approval for a simulated transfer of $1,500.00 to `V-8812`.

Entering `reject` produces:

```text
Wire transfer canceled.
```

Entering `approve` produces:

```text
Simulated wire transfer of $1,500.00 to V-8812.
```

### Billing Balance

```bash
uv run python -c 'from src.graph import graph; result = graph.invoke({"billing_account_id": "ACC-1001"}, {"configurable": {"thread_id": "billing-demo"}}); print(result["next_action"])'
```

Expected output:

```text
ACC-1001 has a simulated balance of $2,500.00.
```

## How the Graph Works

The graph routes requests according to the supplied state.

For a service check, the circuit breaker checks the proposed tool call before the metrics tool runs. The graph then evaluates the error rate.

- An error rate above 5% routes to human approval.
- An error rate of 5% or less finishes without scaling.
- A repeated tool call stops execution.
- Reaching six completed iterations stops further tool execution.

Wire transfer requests have a separate approval node. Billing balance requests and saved-metrics requests route to their own reporting nodes.

## State and Memory

`MetricsState` stores the service name, metrics, latest response, previous tool-call fingerprint, completed iteration count, and request flags.

`InMemorySaver` stores checkpoints using a thread ID. The same thread can recall saved metrics or resume an interrupted request.

Checkpoints are stored in memory and are cleared when the Python process restarts.

## Automated Tests

Run all tests:

```bash
uv run python -m pytest -v
```

The tests cover:

- Repeated tool-call detection.
- The six-iteration limit.
- Consistent fingerprints when argument order changes.
- Service checks that finish without approval.
- Metrics saved in checkpoints.
- Follow-up requests using saved metrics.
- Approval that runs simulated scaling.
- Rejection that skips simulated scaling.

The wire transfer approval and rejection paths can also be demonstrated using the terminal command above.

## Current Scope

This version uses conditional routing and predefined sample data. Scaling and wire transfers return simulation messages. Service checks do not connect to a live monitoring system.

## Author

Fathiya Yoosef