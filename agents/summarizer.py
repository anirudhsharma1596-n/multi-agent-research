
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from utils.state import ResearchState
from config import Config
from utils.logger import AgentLogger


llm = ChatOpenAI(
    model=Config.MODEL_NAME,
    api_key=Config.OPENAI_API_KEY,
    temperature=0.3   # slight creativity for better writing
)
logger = AgentLogger()

def summarizer_agent(state: ResearchState) -> ResearchState:
    logger.log("Summarizer", "started", {"results_count": len(state["search_results"])})

    """
    Job: Take raw search results, produce a clean summary.
    Input:  state['search_results'], state['query']
    Output: state['summary']
    """
    print(f"\n[Summarizer] Summarizing {len(state['search_results'])} results...")

    # Guard: if no results, handle gracefully
    if not state["search_results"]:
        return {
            **state,
            "summary": "No search results were found to summarize.",
            "next_agent": "fact_checker"
        }

    # Combine all results into one block of text
    combined_text = "\n\n---\n\n".join(state["search_results"][:5])  # max 5

    messages = [
        SystemMessage(content="""You are an expert summarizer.
        Given research results and the original question, write a
        clear, structured summary that directly answers the question.
        Use bullet points for key facts. Be concise but complete.
        Always cite when a fact came from a specific source."""),

        HumanMessage(content=f"""
        Original question: {state['query']}

        Research results:
        {combined_text}

        Write a comprehensive summary answering the question.
        """)
    ]

    response = llm.invoke(messages)

    print(f"[Summarizer] Summary generated ({len(response.content)} chars)")
    logger.log("Summarizer", "completed", {"summary_length": len(response.content)})

    return {
        **state,
        "summary": response.content,
        "next_agent": "fact_checker"    # pass the baton
    }