import datetime
import threading
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from openai.types.chat import ChatCompletionMessageParam


@dataclass
class ConversationSession:
    """Represents a single conversation session"""

    session_id: str
    messages: List[ChatCompletionMessageParam] = field(default_factory=list)
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


class SessionManager:
    """Manages multiple conversation sessions"""

    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
        self._lock = threading.Lock()

    def create_session(
        self, initial_message: Optional[ChatCompletionMessageParam] = None
    ) -> ConversationSession:
        """Create a new conversation session"""
        with self._lock:
            session_id = str(uuid.uuid4())
            session = ConversationSession(session_id=session_id)

            if initial_message:
                session.messages.append(initial_message)

            self.sessions[session_id] = session
            return session

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get a session by ID"""
        with self._lock:
            return self.sessions.get(session_id)

    def update_session(self, session_id: str, **kwargs) -> bool:
        """Update session attributes"""
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return False

            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)

            session.updated_at = datetime.datetime.now().isoformat()
            return True

    def add_message(self, session_id: str, message: ChatCompletionMessageParam) -> bool:
        """Add a message to a session's conversation history"""
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return False

            session.messages.append(message)
            session.updated_at = datetime.datetime.now().isoformat()
            return True

    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False

    def list_sessions(self) -> List[dict]:
        """List all sessions (summary only)"""
        with self._lock:
            return [
                {
                    "session_id": session.session_id,
                    "status": session.status,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "message_count": len(session.messages),
                }
                for session in self.sessions.values()
            ]

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove sessions older than max_age_hours"""
        with self._lock:
            cutoff_time = datetime.datetime.now() - datetime.timedelta(
                hours=max_age_hours
            )
            to_delete = []

            for session_id, session in self.sessions.items():
                session_time = datetime.datetime.fromisoformat(session.updated_at)
                if session_time < cutoff_time:
                    to_delete.append(session_id)

            for session_id in to_delete:
                del self.sessions[session_id]

            return len(to_delete)
