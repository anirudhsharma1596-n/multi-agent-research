
import redis
import json
import time
from config import Config

class AgentLogger:
    def __init__(self):
        self.client=None
        self.session_id = f"session:{int(time.time())}"
        self._connect()


    def _connect(self):
        """Try to connect to Redis, fail gracefully if Docker isn't up."""
        try:
            self.client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                decode_responses=True,
                socket_connect_timeout=3    # don't hang forever
            )
            self.client.ping()              # test the connection
            print(f"[Logger] Redis connected at {Config.REDIS_HOST}:{Config.REDIS_PORT}")
        except redis.ConnectionError:
            print("[Logger] WARNING: Redis not available. Logging disabled.")
            print("[Logger] Start Redis with: docker compose up -d")
            self.client = None     

       

    def log(self, agent_name: str, action: str, data: dict):
        """Log an agent's decision to Redis."""
        if not self.client:
            return
        
        entry = {
            "timestamp": time.time(),
            "agent":     agent_name,
            "action":    action,
            "data":      data
        }
        try:
            self.client.rpush(self.session_id, json.dumps(entry))
            print(f"[{agent_name}] {action}")
        except redis.ConnectionError:
            pass    # Redis went down mid-run — keep going

    def get_logs(self) -> list:
        """Retrieve all logs for this session."""
        if not self.client:
            return []
        raw = self.client.lrange(self.session_id, 0, -1)
        return [json.loads(r) for r in raw]
    
    def is_connected(self) -> bool:
        return self.client is not None