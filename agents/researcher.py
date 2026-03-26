from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from utils.state import ResearchState
from tools.search import run_search
from config import Config
from utils.logger import AgentLogger
from utils.cache import QueryCache
from utils.retry import with_retry

llm = ChatOpenAI(
    model=Config.MODEL_NAME,
    api_key=Config.OPENAI_API_KEY,
    temperature=0   # 0 = deterministic, best for factual research
)
logger = AgentLogger()
cache  = QueryCache()

@with_retry(max_retries=3, backoff=2.0)
def call_llm(messages):
    return llm.invoke(messages)

def researcher_agent(state: ResearchState) -> ResearchState:
    start = __import__("time").time()
    logger.log("Researcher","started",{"query":state["query"]})
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

    response = call_llm(messages)
    search_queries = response.content.strip().split("\n")
    search_queries = [q.strip() for q in search_queries if q.strip()]
    logger.log("Researcher", "queries_generated", {"queries": search_queries})


    print(f"[Researcher] Generated queries: {search_queries}")

    # Step 2: Run searches for each query
    all_results = []
    all_sources = []

    for sq in search_queries[:2]:   # max 2 searches to save API credits
        cached = cache.get(sq)
        if cached:
            logger.log("Researcher", "cache_hit", {"query": sq})
            for r in cached:
                all_results.append(r.get("content", ""))
                all_sources.append(r.get("url", ""))
            continue
        try:
            results = run_search(sq)
            cache.set(sq,results)

            print(f"[Researcher] Got {len(results)} results for: {sq}")

            for r in results:
                content = r.get("content", "").strip()
                url     = r.get("url", "")
                if content:                    # only add non-empty results
                    all_results.append(content)
                    all_sources.append(url)

        except Exception as e:
            logger.log("Researcher", "search_error", {"error": str(e)})
            print(f"[Researcher] Search error: {e}")

    elapsed = round(__import__("time").time() - start, 2)
    logger.log("Researcher", "completed", {
        "results_count": len(all_results),
        "duration_sec":  elapsed
    })

    # Step 3: Return UPDATED state — never mutate, always return new dict
    return {
        **state,                            # spread existing state
        "search_results": all_results,
        "sources": all_sources,
        "next_agent": "summarizer"          # tell supervisor who's next
    }