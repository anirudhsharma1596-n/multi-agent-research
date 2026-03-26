# test_search.py — run this to debug
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_tavily import TavilySearch

tool = TavilySearch(max_results=2, topic="general")
raw = tool.invoke({"query": "latest AI breakthroughs 2025"})

print("=== RAW RESPONSE TYPE ===")
print(type(raw))

print("\n=== RAW RESPONSE ===")
print(raw)

print("\n=== PARSED RESULTS ===")
if isinstance(raw, dict) and "results" in raw:
    for i, r in enumerate(raw["results"]):
        print(f"\nResult {i+1}:")
        print(f"  URL:     {r.get('url', 'N/A')}")
        print(f"  Content: {r.get('content', 'N/A')[:100]}...")
elif isinstance(raw, list):
    for i, r in enumerate(raw):
        print(f"\nResult {i+1}: {r.get('url', 'N/A')}")