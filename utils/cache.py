# utils/cache.py
import redis
import json
import hashlib
from config import Config

class QueryCache:
    TTL = 86400  # 24 hours in seconds

    def __init__(self):
        self.client = None
        try:
            self.client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                decode_responses=True,
                socket_connect_timeout=3
            )
            self.client.ping()
        except Exception:
            self.client = None

    def _key(self, query: str) -> str:
        """Deterministic cache key from query string."""
        h = hashlib.md5(query.lower().strip().encode()).hexdigest()
        return f"cache:{h}"

    def get(self, query: str) -> list | None:
        """Return cached results or None if not found."""
        if not self.client:
            return None
        try:
            val = self.client.get(self._key(query))
            if val:
                print(f"[Cache] HIT for: '{query[:50]}...'")
                return json.loads(val)
        except Exception:
            pass
        return None

    def set(self, query: str, results: list):
        """Cache results with TTL."""
        if not self.client or not results:
            return
        try:
            self.client.setex(
                self._key(query),
                self.TTL,
                json.dumps(results)
            )
            print(f"[Cache] Stored {len(results)} results · TTL=24h")
        except Exception:
            pass