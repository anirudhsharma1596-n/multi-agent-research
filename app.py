import streamlit as st
import time
import json
from datetime import datetime
from main import build_graph
from utils.state import ResearchState
from utils.logger import AgentLogger

# ─── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Multi-Agent Research Assistant",
    page_icon="🤖",
    layout="centered"
)

# ─── Shared logger instance ───────────────────────────────────
logger = AgentLogger()

# ─── Pipeline status helper ───────────────────────────────────
def show_pipeline_status(current_agent: str):
    agents = ["researcher", "summarizer", "fact_checker", "done"]
    labels = ["Researcher", "Summarizer", "Fact-Checker", "Done"]
    cols   = st.columns(4)
    for i, (col, agent, label) in enumerate(zip(cols, agents, labels)):
        with col:
            order = agents.index(current_agent) if current_agent in agents else -1
            if i < order:
                st.success(f"✅ {label}")
            elif i == order:
                st.info(f"⏳ {label}")
            else:
                st.markdown(
                    f"<div style='text-align:center;padding:8px;background:#f5f5f5;"
                    f"border-radius:8px;font-size:13px;color:#888'>⬜ {label}</div>",
                    unsafe_allow_html=True
                )

# ─── Run research helper ──────────────────────────────────────
def run_research_ui(query: str):
    """Runs the full pipeline with live Streamlit updates."""
    st.divider()
    log_placeholder    = st.empty()
    agent_logs         = []

    st.subheader("Pipeline status")
    status_placeholder = st.empty()

    st.subheader("Results")
    col1, col2, col3   = st.columns(3)
    sources_metric     = col1.empty()
    reliability_metric = col2.empty()
    time_metric        = col3.empty()

    answer_placeholder  = st.empty()
    sources_placeholder = st.empty()
    verdict_placeholder = st.empty()

    start_time = time.time()

    initial_state: ResearchState = {
        "query":             query.strip(),
        "search_results":    [],
        "sources":           [],
        "summary":           "",
        "fact_check_result": "",
        "is_reliable":       False,
        "next_agent":        "researcher",
        "iteration":         0,
        "final_answer":      None,
        "error":             None
    }

    app = build_graph()

    try:
        for update in app.stream(initial_state, stream_mode="updates"):
            for node_name, state in update.items():
                agent_logs.append(f"[{node_name.upper()}] running...")
                with status_placeholder.container():
                    show_pipeline_status(node_name)
                with log_placeholder.container():
                    with st.expander("Agent log", expanded=True):
                        for line in agent_logs:
                            st.caption(line)
                elapsed = round(time.time() - start_time, 1)
                sources_metric.metric("Sources found", len(state.get("search_results", [])) or "—")
                time_metric.metric("Time elapsed", f"{elapsed}s")
                reliability_metric.metric("Reliability", "—")

        final_state = state
        elapsed     = round(time.time() - start_time, 1)

        sources_metric.metric("Sources found", len(final_state.get("sources", [])))
        reliability_metric.metric("Reliability", "HIGH ✅" if final_state.get("is_reliable") else "LOW ⚠️")
        time_metric.metric("Time taken", f"{elapsed}s")

        with status_placeholder.container():
            show_pipeline_status("done")

        if final_state.get("final_answer"):
            with answer_placeholder.container():
                st.subheader("Final answer")
                st.markdown(final_state["final_answer"])

        sources = final_state.get("sources", [])
        if sources:
            with sources_placeholder.container():
                st.subheader("Sources")
                for i, url in enumerate(sources[:6], 1):
                    if url:
                        st.markdown(f"{i}. [{url}]({url})")

        if final_state.get("fact_check_result"):
            with verdict_placeholder.container():
                st.subheader("Fact-check report")
                color   = "green" if final_state.get("is_reliable") else "red"
                verdict = "✅ RELIABLE" if final_state.get("is_reliable") else "⚠️ UNRELIABLE"
                st.markdown(f"**Verdict: :{color}[{verdict}]**")
                with st.expander("Full fact-check details"):
                    st.write(final_state["fact_check_result"])

        with log_placeholder.container():
            with st.expander("Agent log", expanded=False):
                for line in agent_logs:
                    st.caption(line)

    except Exception as e:
        st.error(f"Something went wrong: {str(e)}")
        st.exception(e)


# ─── Tabs ─────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🔍 Research", "🕓 Session History"])


# ══════════════════════════════════════════════════════════════
# TAB 1 — RESEARCH
# ══════════════════════════════════════════════════════════════
with tab1:
    st.title("🤖 Multi-Agent Research Assistant")
    st.caption("Powered by LangGraph · Tavily · GPT-4o-mini · Redis")
    st.divider()

    # Pre-fill from session state if example was clicked
    default_query = st.session_state.pop("prefill_query", "")

    query   = st.text_input(
        label="Your research question",
        value=default_query,
        placeholder="e.g. What are the latest AI breakthroughs in 2025?",
        label_visibility="collapsed"
    )
    run_btn = st.button("🔍 Research", type="primary", use_container_width=True)

    if run_btn and query.strip():
        run_research_ui(query)
    elif run_btn:
        st.warning("Please enter a research question first.")


# ══════════════════════════════════════════════════════════════
# TAB 2 — SESSION HISTORY
# ══════════════════════════════════════════════════════════════
with tab2:
    st.title("🕓 Session History")
    st.caption("All past research runs stored in Redis")
    st.divider()

    if not logger.is_connected:
        st.error("Redis is not connected. Start it with: `docker compose up -d`")
    else:
        sessions = logger.list_sessions()

        if not sessions:
            st.info("No sessions yet. Run a research query first!")
        else:
            st.markdown(f"**{len(sessions)} session(s) found**")

            for session_id in sessions[:20]:        # show latest 20
                logs = logger.get_session_logs(session_id)
                if not logs:
                    continue

                # ── Parse session summary from logs ──
                ts        = int(session_id.split(":")[1])
                dt        = datetime.fromtimestamp(ts).strftime("%d %b %Y · %H:%M:%S")
                query_log = next((l for l in logs if l.get("action") == "started"
                                  and l.get("agent") == "Researcher"), None)
                query_txt = query_log["data"].get("query", "Unknown query") if query_log else "Unknown query"

                result_log   = next((l for l in reversed(logs) if l.get("agent") == "Fact-Checker"
                                     and l.get("action") == "completed"), None)
                is_reliable  = result_log["data"].get("is_reliable", None) if result_log else None
                duration_log = next((l for l in reversed(logs) if l.get("action") == "completed"), None)
                duration     = duration_log["data"].get("duration_sec", "—") if duration_log else "—"

                cache_hits   = sum(1 for l in logs if l.get("action") == "cache_hit")

                # ── Session card ──
                with st.expander(f"🕓 {dt}  —  {query_txt[:60]}{'...' if len(query_txt) > 60 else ''}"):

                    # Metrics row
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Log entries", len(logs))
                    m2.metric("Duration",    f"{duration}s" if duration != "—" else "—")
                    m3.metric("Cache hits",  cache_hits)
                    if is_reliable is not None:
                        m4.metric("Reliable", "Yes ✅" if is_reliable else "No ⚠️")
                    else:
                        m4.metric("Reliable", "—")

                    st.divider()

                    # Agent timeline
                    st.markdown("**Agent timeline**")
                    agent_colors = {
                        "Researcher":   "🟢",
                        "Summarizer":   "🔵",
                        "Fact-Checker": "🟣",
                        "Supervisor":   "🟡",
                    }
                    for log in logs:
                        agent  = log.get("agent", "")
                        action = log.get("action", "")
                        data   = log.get("data", {})
                        ts_log = log.get("timestamp", 0)
                        t_str  = datetime.fromtimestamp(ts_log).strftime("%H:%M:%S")
                        icon   = agent_colors.get(agent, "⚪")
                        detail = ""
                        if "results_count" in data:
                            detail = f" · {data['results_count']} results"
                        if "duration_sec" in data:
                            detail += f" · {data['duration_sec']}s"
                        if "query" in data and action == "started":
                            detail = f" · \"{data['query'][:40]}...\""
                        st.caption(f"`{t_str}` {icon} **{agent}** → {action}{detail}")

                    st.divider()

                    # Replay button
                    if st.button(f"▶️ Re-run this query", key=f"replay_{session_id}"):
                        st.session_state["prefill_query"] = query_txt
                        st.rerun()


# ─── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.header("About")
    st.markdown("""
    This app uses **4 AI agents** working together:

    - 🔎 **Researcher** — searches the web via Tavily
    - 📝 **Summarizer** — condenses findings
    - ✅ **Fact-Checker** — verifies claims
    - 🧭 **Supervisor** — routes between agents

    Built with **LangGraph** + **LangChain**.
    """)

    st.divider()

    # Redis status indicator
    st.header("System status")
    if logger.is_connected:
        st.success("Redis connected")
    else:
        st.error("Redis offline")
        st.caption("Run: `docker compose up -d`")

    st.divider()

    st.header("Example queries")
    examples = [
        "What is quantum computing used for today?",
        "Latest breakthroughs in cancer research 2025",
        "How does Retrieval Augmented Generation work?",
        "What are the risks of artificial general intelligence?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state["prefill_query"] = ex
            st.rerun()