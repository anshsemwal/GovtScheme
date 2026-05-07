"""Interaction and dialogue models"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import uuid


class MessageRole(str, Enum):
    """Message sender roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class DialogueState(str, Enum):
    """Conversation state machine states"""
    GREETING = "greeting"
    COLLECTING_PROFILE = "collecting_profile"
    RECOMMENDING = "recommending"
    CHECKING_ELIGIBILITY = "checking_eligibility"
    PROVIDING_GUIDANCE = "providing_guidance"
    COMPLETED = "completed"


class Message(BaseModel):
    """Individual message in a conversation"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole = Field(description="Who sent the message")
    content: str = Field(description="Message content")
    language: str = Field(default="en", description="Message language")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Interaction(BaseModel):
    """User interaction session tracking"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = Field(default=None, description="Associated user ID")
    messages: List[Message] = Field(default_factory=list)
    state: DialogueState = Field(default=DialogueState.GREETING)
    context: Dict[str, Any] = Field(default_factory=dict, description="Conversation context")
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    recommended_schemes: List[str] = Field(default_factory=list)
    language: str = Field(default="en", description="Session language")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def add_message(self, role: MessageRole, content: str, language: str = None) -> Message:
        """Add a message to the conversation"""
        message = Message(
            role=role,
            content=content,
            language=language or self.language
        )
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history for context"""
        recent = self.messages[-limit:] if len(self.messages) > limit else self.messages
        return [{"role": m.role.value, "content": m.content} for m in recent]
    
    def update_state(self, new_state: DialogueState) -> None:
        """Update dialogue state"""
        self.state = new_state
        self.updated_at = datetime.now()
    
    def update_context(self, **kwargs) -> None:
        """Update conversation context"""
        self.context.update(kwargs)
        self.updated_at = datetime.now()
    
    def add_extracted_entities(self, entities: Dict[str, Any]) -> None:
        """Add extracted entities from NLP"""
        self.extracted_entities.update(entities)
        self.updated_at = datetime.now()
