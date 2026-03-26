# agents/supervisor.py
from utils.state import ResearchState

def supervisor_agent(state: ResearchState) -> ResearchState:
    """
    The supervisor doesn't call any LLM.
    It simply reads next_agent from state and returns state unchanged.
    LangGraph's conditional edges do the actual routing.

    Think of it as a roundabout — cars (state) pass through,
    and exit signs (conditional edges) direct them.
    """
    print(f"\n[Supervisor] Current next_agent: '{state.get('next_agent')}'")
    print(f"[Supervisor] Iteration: {state.get('iteration', 0)}")

    # Safety check — prevent infinite loops
    iteration = state.get("iteration", 0)
    if iteration >= 10:
        print("[Supervisor] Max iterations reached, forcing END")
        return {**state, "next_agent": "END", "error": "Max iterations reached"}

    return {**state, "iteration": iteration + 1}


def route_next(state: ResearchState) -> str:
    """
    This is the routing function LangGraph calls to decide
    which node to go to next.

    Returns a string that must exactly match a node name
    or the special value "END".

    Interview Q: Why is this a separate function from supervisor_agent?
    Because LangGraph's add_conditional_edges() needs a callable
    that returns a string — keeping it separate is cleaner.
    """
    next_agent = state.get("next_agent", "END")

    valid_routes = {"researcher", "summarizer", "fact_checker", "END"}

    if next_agent not in valid_routes:
        print(f"[Supervisor] Unknown route '{next_agent}', defaulting to END")
        return "END"

    return next_agent