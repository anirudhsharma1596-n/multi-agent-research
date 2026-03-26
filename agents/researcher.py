from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from utils.state import ResearchState
from tools.search import run_search
from config import Config

llm = ChatOpenAI(
    model=Config.MODEL_NAME,
    api_key=Config.OPENAI_API_KEY,
    temperature=0   # 0 = deterministic, best for factual research
)

def researcher_agent(state: ResearchState) -> ResearchState:
    """
    Job: Take the user query, search the web, return raw results.
    Input:  state['query']
    Output: state['search_results'], state['sources']
    """
    print(f"\n[Researcher] Searching for: {state['query']}")

    # Step 1: Ask the LLM to generate better search queries
    messages = [
        SystemMessage(content="""You are a research assistant.
        Given a user question, generate 2 focused search queries
        to find comprehensive information. Return only the queries,
        one per line, nothing else."""),
        HumanMessage(content=state["query"])
    ]

    response = llm.invoke(messages)
    search_queries = response.content.strip().split("\n")
    search_queries = [q.strip() for q in search_queries if q.strip()]

    print(f"[Researcher] Generated queries: {search_queries}")

    # Step 2: Run searches for each query
    all_results = []
    all_sources = []

    for sq in search_queries[:2]:   # max 2 searches to save API credits
        try:
            results = run_search(sq)

            # Tavily returns a list of dicts with 'content' and 'url'
            if isinstance(results, list):
                for r in results:
                    if isinstance(r, dict):
                        all_results.append(r.get("content", ""))
                        all_sources.append(r.get("url", ""))
            elif isinstance(results, str):
                all_results.append(results)

        except Exception as e:
            print(f"[Researcher] Search error: {e}")

    # Step 3: Return UPDATED state — never mutate, always return new dict
    return {
        **state,                            # spread existing state
        "search_results": all_results,
        "sources": all_sources,
        "next_agent": "summarizer"          # tell supervisor who's next
    }