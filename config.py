import os
from dotenv import load_dotenv


load_dotenv()

class Config:
    OPEN_API_KEY = os.getenv("OPEN_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

    MODEL_NAME     = "gpt-4o-mini"        # cheap & fast for dev

    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

    # Agent behaviour
    MAX_SEARCH_RESULTS = 5
    MAX_RETRIES        = 3