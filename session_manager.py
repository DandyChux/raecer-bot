import datetime
import json
import os
import uuid
from dataclasses import dataclass, field
from typing import List, Optional

from anthropic.types import MessageParam
from redis import ConnectionError, Redis

# Redis configuration - can be overwritten via environment variables
REDIS_URL = os.environ.get("REDIS_URL", "redis://:raecer123@localhost:6379/0")
SESSION_TTL_HOURS = int(os.environ.get("SESSION_TTL_HOURS", "24"))


@dataclass
class ConversationSession:
    """Represents a single conversation session"""

    session_id: str
    messages: List[MessageParam] = field(default_factory=list)
    status: str = "active"  # active, completed, error
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    patient_data: Optional[dict] = None
    pro_ctcae_data: Optional[dict] = None
    error_message: Optional[str] = None

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "session_id": self.session_id,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": len(self.messages),
            "patient_data": self.patient_data,
            "pro_ctcae_data": self.pro_ctcae_data,
            "error_message": self.error_message,
        }

    def to_json(self):
        """Serialize entire session to JSON format for Redis storage"""
        return json.dumps(
            {
                "session_id": self.session_id,
                "messages": self.messages,
                "status": self.status,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "patient_data": self.patient_data,
                "pro_ctcae_data": self.pro_ctcae_data,
                "error_message": self.error_message,
            }
        )

    @classmethod
    def from_json(cls, json_str: str) -> "ConversationSession":
        """Deserialize session from JSON"""
        data = json.loads(json_str)
        return cls(
            session_id=data["session_id"],
            messages=data["messages"],
            status=data["status"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            patient_data=data["patient_data"],
            pro_ctcae_data=data["pro_ctcae_data"],
            error_message=data["error_message"],
        )


class SessionManager:
    """Manages multiple conversation sessions using Redis for persistence"""

    # Redis key prefix for session data
    KEY_PREFIX = "raecer:session:"

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize the session manager with Redis connection.

        Args:
            redis_url: Redis connection URL. Defaults to REDIS_URL env var or localhost.
        """
        self.redis_url = redis_url or REDIS_URL
        self.redis_client = Redis.from_url(self.redis_url, decode_responses=True)
        self.session_ttl = SESSION_TTL_HOURS * 3600  # Convert hours to seconds

        # Test connection
        try:
            self.redis_client.ping()
            print(f"✅ Redis connected: {self._sanitize_url(self.redis_url)}")
        except ConnectionError as e:
            print(f"❌ Redis connection failed: {e}")
            raise

    def _sanitize_url(self, url: str) -> str:
        """Remove password from URL for logging"""
        if "@" in url:
            parts = url.split("@")
            return f"redis://***@{parts[-1]}"
        return url

    def _session_key(self, session_id: str) -> str:
        """Generate Redis key for a session"""
        return f"{self.KEY_PREFIX}{session_id}"

    def _save_session(self, session: ConversationSession) -> None:
        """Save session to Redis with TTL"""
        key = self._session_key(session.session_id)
        self.redis_client.setex(key, self.session_ttl, session.to_json())

    def create_session(
        self, initial_message: Optional[MessageParam] = None
    ) -> ConversationSession:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())
        session = ConversationSession(session_id=session_id)

        if initial_message:
            session.messages.append(initial_message)

        self._save_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get a session by ID"""
        key = self._session_key(session_id)
        data = self.redis_client.get(key)

        if data is None:
            return None

        return ConversationSession.from_json(data)

    def update_session(self, session_id: str, **kwargs) -> bool:
        """Update session attributes"""
        session = self.get_session(session_id)
        if not session:
            return False

        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)

        session.updated_at = datetime.datetime.now().isoformat()
        self._save_session(session)
        return True

    def add_message(self, session_id: str, message: MessageParam) -> bool:
        """Add a message to a session's conversation history"""
        session = self.get_session(session_id)
        if not session:
            return False

        session.messages.append(message)
        session.updated_at = datetime.datetime.now().isoformat()
        self._save_session(session)
        return True

    def append_message(
        self, session: ConversationSession, message: MessageParam
    ) -> None:
        """Append a message to an existing session object and save to Redis"""
        session.messages.append(message)
        session.updated_at = datetime.datetime.now().isoformat()
        self._save_session(session)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        key = self._session_key(session_id)
        deleted = self.redis_client.delete(key)
        return deleted > 0

    def list_sessions(self) -> List[dict]:
        """List all sessions (summary only)"""
        pattern = f"{self.KEY_PREFIX}*"
        keys: list[str] = self.redis_client.keys(pattern)  # ty:ignore[invalid-assignment]

        sessions = []
        for key in keys:
            data: str | None = self.redis_client.get(key)  # ty:ignore[invalid-assignment]
            if data:
                session = ConversationSession.from_json(data)
                sessions.append(
                    {
                        "session_id": session.session_id,
                        "status": session.status,
                        "created_at": session.created_at,
                        "updated_at": session.updated_at,
                        "message_count": len(session.messages),
                    }
                )

        return sessions

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Remove sessions older than max_age_hours.

        Note: With Redis TTL, sessions auto-expire. This method is kept for
        compatibility and for manually cleaning up sessions sooner than TTL.
        """
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=max_age_hours)

        pattern = f"{self.KEY_PREFIX}*"
        keys = self.redis_client.keys(pattern)

        deleted_count = 0
        for key in keys:
            data = self.redis_client.get(key)
            if data:
                session = ConversationSession.from_json(data)
                session_time = datetime.datetime.fromisoformat(session.updated_at)
                if session_time < cutoff_time:
                    self.redis_client.delete(key)
                    deleted_count += 1

        return deleted_count
