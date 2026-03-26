# main.py
from langgraph.graph import StateGraph, END

from utils.state import ResearchState
from agents.researcher    import researcher_agent
from agents.summarizer    import summarizer_agent
from agents.fact_checker  import fact_checker_agent
from agents.supervisor    import supervisor_agent, route_next

def build_graph() -> StateGraph:
    """
    Builds and compiles the LangGraph StateGraph.

    Think of this like wiring a circuit:
    - add_node()  = place a component
    - add_edge()  = wire always-on connection
    - add_conditional_edges() = wire a switch
    - compile()   = flip the power on
    """

    # Step 1: Create graph, tell it what state shape to use
    graph = StateGraph(ResearchState)

    # Step 2: Register every agent as a node
    # format: graph.add_node("node_name", function)
    graph.add_node("supervisor",    supervisor_agent)
    graph.add_node("researcher",    researcher_agent)
    graph.add_node("summarizer",    summarizer_agent)
    graph.add_node("fact_checker",  fact_checker_agent)

    # Step 3: Set the entry point — where the graph starts
    graph.set_entry_point("supervisor")

    # Step 4: Add conditional edges FROM supervisor
    # route_next() is called after supervisor runs,
    # its return value picks the next node
    graph.add_conditional_edges(
        "supervisor",       # from this node...
        route_next,         # call this function to decide...
        {                   # map return values to node names
            "researcher":   "researcher",
            "summarizer":   "summarizer",
            "fact_checker": "fact_checker",
            "END":          END
        }
    )

    # Step 5: After each agent runs, always go back to supervisor
    graph.add_edge("researcher",   "supervisor")
    graph.add_edge("summarizer",   "supervisor")
    graph.add_edge("fact_checker", "supervisor")

    # Step 6: Compile — validates graph, returns a runnable
    return graph.compile()


def run_research(query: str) -> dict:
    """
    Entry point for running the full pipeline.
    """
    print(f"\n{'='*50}")
    print(f"Query: {query}")
    print(f"{'='*50}")

    # Build the compiled graph
    app = build_graph()

    # Create the initial state — only query is set
    initial_state: ResearchState = {
        "query":             query,
        "search_results":    [],
        "sources":           [],
        "summary":           "",
        "fact_check_result": "",
        "is_reliable":       False,
        "next_agent":        "researcher",   # start with researcher
        "iteration":         0,
        "final_answer":      None,
        "error":             None
    }

    # Run the graph — blocks until END is reached
    final_state = app.invoke(initial_state)

    print(f"\n{'='*50}")
    print("FINAL ANSWER:")
    print(final_state.get("final_answer", "No answer generated"))
    print(f"\nReliable: {final_state.get('is_reliable')}")
    print(f"Sources:  {final_state.get('sources', [])[:3]}")
    print(f"{'='*50}\n")

    return final_state


# Entry point
if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else \
            "What are the latest AI breakthroughs in 2025?"
    run_research(query)