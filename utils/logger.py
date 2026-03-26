# utils/logger.py — full upgrade
import redis
import json
import time
from config import Config

class AgentLogger:
    def __init__(self):
        self.client     = None
        self.session_id = f"session:{int(time.time())}"
        self._connect()

    def _connect(self):
        try:
            self.client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                decode_responses=True,
                socket_connect_timeout=3
            )
            self.client.ping()
            print(f"[Logger] Connected · session = {self.session_id}")
        except redis.ConnectionError:
            print("[Logger] Redis unavailable — logging disabled")
            self.client = None

    def log(self, agent_name: str, action: str, data: dict = {}):
        """Log one agent action with timestamp and duration tracking."""
        entry = {
            "timestamp": round(time.time(), 3),
            "agent":     agent_name,
            "action":    action,
            "data":      data
        }
        print(f"  [{agent_name}] {action}")
        if not self.client:
            return
        try:
            self.client.rpush(self.session_id, json.dumps(entry))
            # Keep session keys for 48 hours then auto-delete
            self.client.expire(self.session_id, 172800)
        except redis.ConnectionError:
            pass

    def get_logs(self) -> list:
        """Retrieve all logs for this session."""
        if not self.client:
            return []
        try:
            raw = self.client.lrange(self.session_id, 0, -1)
            return [json.loads(r) for r in raw]
        except Exception:
            return []

    def list_sessions(self) -> list:
        """Return all session keys sorted newest first."""
        if not self.client:
            return []
        try:
            keys = self.client.keys("session:*")
            return sorted(keys, reverse=True)
        except Exception:
            return []

    def get_session_logs(self, session_id: str) -> list:
        """Retrieve logs for any session by its key."""
        if not self.client:
            return []
        try:
            raw = self.client.lrange(session_id, 0, -1)
            return [json.loads(r) for r in raw]
        except Exception:
            return []

    @property
    def is_connected(self) -> bool:
        return self.client is not None