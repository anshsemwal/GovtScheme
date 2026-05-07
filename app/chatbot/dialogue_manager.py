"""Dialogue Manager for conversation state management"""

from typing import Dict, Optional
from app.models.interaction import Interaction, DialogueState, MessageRole


class DialogueManager:
    """Manages dialogue state and context across conversations"""
    
    def __init__(self):
        # In-memory session store (use Redis in production)
        self.sessions: Dict[str, Interaction] = {}
    
    def get_or_create_session(self, session_id: str, language: str = "en") -> Interaction:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            self.sessions[session_id] = Interaction(
                session_id=session_id,
                language=language
            )
        return self.sessions[session_id]
    
    def get_session(self, session_id: str) -> Optional[Interaction]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def update_state(self, session_id: str, new_state: DialogueState) -> None:
        """Update session state"""
        session = self.sessions.get(session_id)
        if session:
            session.update_state(new_state)
    
    def add_user_message(self, session_id: str, content: str) -> None:
        """Add user message to session"""
        session = self.get_or_create_session(session_id)
        session.add_message(MessageRole.USER, content)
    
    def add_assistant_message(self, session_id: str, content: str) -> None:
        """Add assistant message to session"""
        session = self.sessions.get(session_id)
        if session:
            session.add_message(MessageRole.ASSISTANT, content)
    
    def get_context(self, session_id: str) -> Dict:
        """Get session context"""
        session = self.sessions.get(session_id)
        return session.context if session else {}
    
    def update_context(self, session_id: str, **kwargs) -> None:
        """Update session context"""
        session = self.sessions.get(session_id)
        if session:
            session.update_context(**kwargs)
    
    def set_language(self, session_id: str, language: str) -> None:
        """Set session language"""
        session = self.sessions.get(session_id)
        if session:
            session.language = language
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> list:
        """Get recent conversation history"""
        session = self.sessions.get(session_id)
        if session:
            return session.get_conversation_history(limit)
        return []
    
    def clear_session(self, session_id: str) -> bool:
        """Clear session data"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def get_all_sessions(self) -> Dict[str, Interaction]:
        """Get all active sessions"""
        return self.sessions


# Singleton instance
dialogue_manager = DialogueManager()
