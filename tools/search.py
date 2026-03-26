# tools/search.py
from langchain_tavily import TavilySearch
from config import Config
import os

os.environ["TAVILY_API_KEY"] = Config.TAVILY_API_KEY

def get_search_tool():
    """
    Returns a configured Tavily search tool.
    max_results=5 means we get 5 web results per query.
    """
    return TavilySearch(max_results=Config.MAX_SEARCH_RESULTS)


def run_search(query: str) -> dict:
    """
    Runs a raw Tavily search and returns results.
    Used directly by the Researcher agent.
    """
    tool = get_search_tool()
    results = tool.invoke({"query": query})
    return results