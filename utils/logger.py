
import redis
import json
import time
from config import Config

class AgentLogger:
    def __init__(self):
        self.client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            decode_responses=True        # Returns strings, not bytes
        )
        self.session_id = f"session:{int(time.time())}"

    def log(self, agent_name: str, action: str, data: dict):
        """Log an agent's decision to Redis."""
        entry = {
            "timestamp": time.time(),
            "agent":     agent_name,
            "action":    action,
            "data":      data
        }
        # RPUSH adds to a Redis list (like append)
        self.client.rpush(self.session_id, json.dumps(entry))
        print(f"[{agent_name}] {action}")   # Also print to console

    def get_logs(self) -> list:
        """Retrieve all logs for this session."""
        raw = self.client.lrange(self.session_id, 0, -1)
        return [json.loads(r) for r in raw]