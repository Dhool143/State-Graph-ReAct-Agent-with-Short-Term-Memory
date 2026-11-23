from uuid import uuid4

import streamlit as st
from langgraph.types import Command

from src.graph import graph


st.title("Service Metrics Agent")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = uuid4().hex

config = {"configurable": {"thread_id": st.session_state.thread_id}}
pending = st.session_state.get("pending_approval")

if pending is None:
    service = st.selectbox("Service", ["billing-service", "auth-service"])

    check = st.button("Check service")
    retry = st.button("Test repeated tool call")

    if check or retry:
        result = graph.invoke(
            {
                "service_name": service,
                "retry_demo": retry,
                "completed_iterations": 0,
                "previous_fingerprint": "",
            },
            config,
        )

        if result.get("__interrupt__"):
            st.session_state.pending_approval = result["__interrupt__"][0].value
            st.session_state.pop("result", None)
            st.rerun()

        st.session_state.result = result["next_action"]

    if st.button("Recall last error rate"):
        result = graph.invoke({"use_saved_metrics": True}, config)
        st.session_state.result = result["next_action"]

else:
    st.warning(
        f"Approve simulated scaling for {pending['service_name']} "
        f"to {pending['replica_count']} replicas?"
    )

    approve = st.button("Approve")
    reject = st.button("Reject")

    if approve or reject:
        result = graph.invoke(Command(resume=approve), config)
        st.session_state.result = result["next_action"]
        del st.session_state.pending_approval
        st.rerun()

if "result" in st.session_state:
    st.info(st.session_state.result)

with st.expander("Graph state"):
    snapshot = graph.get_state(config)
    st.write("Next node:", ", ".join(snapshot.next) or "None")
    st.json(snapshot.values)