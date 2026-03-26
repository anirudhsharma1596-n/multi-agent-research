
from typing import TypedDict, List, Optional

class ResearchState(TypedDict):
    """
    This dictionary is passed between every agent.
    Think of it as a baton in a relay race —
    each agent adds its output and hands it forward.
    """
    # Input
    query: str                        # The user's original question

    # Researcher output
    search_results: List[str]         # Raw text from web searches
    sources: List[str]                # URLs found

    # Summarizer output
    summary: str                      # Condensed version of research

    # Fact-checker output
    fact_check_result: str            # Verified / flagged claims
    is_reliable: bool                 # Final reliability verdict

    # Control flow
    next_agent: str                   # Supervisor sets this to route
    iteration: int                    # How many loops we've done
    final_answer: Optional[str]       # Set when pipeline is complete
    error: Optional[str]              # Any error that occurred