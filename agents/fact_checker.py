
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from utils.state import ResearchState
from config import Config
from utils.logger import AgentLogger

llm = ChatOpenAI(
    model=Config.MODEL_NAME,
    api_key=Config.OPENAI_API_KEY,
    temperature=0   # facts must be deterministic
)

logger=AgentLogger()

def fact_checker_agent(state: ResearchState) -> ResearchState:
    logger.log("FactChecker", "started", {"results_count": len(state["summary"])})

    """
    Job: Verify the summary against raw sources, flag issues.
    Input:  state['summary'], state['search_results']
    Output: state['fact_check_result'], state['is_reliable']
    """
    print(f"\n[Fact-Checker] Verifying summary...")

    if not state.get("summary"):
        return {
            **state,
            "fact_check_result": "Nothing to fact-check.",
            "is_reliable": False,
            "next_agent": "END"
        }

    # Build the source context for comparison
    source_context = "\n\n".join(state["search_results"][:3])

    messages = [
        SystemMessage(content="""You are a rigorous fact-checker.
        Compare the summary against the source material.
        Identify:
        1. Claims that are SUPPORTED by sources
        2. Claims that are UNSUPPORTED or potentially hallucinated
        3. Any important facts MISSING from the summary
        4. An overall reliability score: HIGH / MEDIUM / LOW

        End your response with exactly one line:
        RELIABILITY: HIGH  or  RELIABILITY: MEDIUM  or  RELIABILITY: LOW"""),

        HumanMessage(content=f"""
        Summary to check:
        {state['summary']}

        Source material:
        {source_context}
        """)
    ]

    response = llm.invoke(messages)
    result_text = response.content

    # Parse reliability from response
    is_reliable = False
    if "RELIABILITY: HIGH" in result_text:
        is_reliable = True
    elif "RELIABILITY: MEDIUM" in result_text:
        is_reliable = True  # medium is acceptable

    print(f"[Fact-Checker] Reliable: {is_reliable}")
    logger.log("FactChecker", "completed", {"results": state["fact_check_result"]})

    return {
        **state,
        "fact_check_result": result_text,
        "is_reliable": is_reliable,
        "final_answer": state["summary"],  # summary becomes final answer
        "next_agent": "END"                # pipeline complete
    }
