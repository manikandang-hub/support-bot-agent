"""
Manage conversation history for multi-turn interactions.
Stores previous messages and snippets for context in follow-up questions.
"""

from datetime import datetime
from typing import Dict, List, Optional
import uuid
from app.models import ConversationMessage


class ConversationManager:
    """Manages conversation history per user session."""

    def __init__(self):
        # Store conversations: {conversation_id: [messages]}
        self.conversations: Dict[str, List[ConversationMessage]] = {}

    def create_conversation(self) -> str:
        """Create a new conversation and return its ID."""
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = []
        return conversation_id

    def add_user_message(self, conversation_id: str, query: str) -> None:
        """Add user's question to conversation history."""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        message = ConversationMessage(
            role="user",
            content=query,
            timestamp=datetime.utcnow().isoformat()
        )
        self.conversations[conversation_id].append(message)

    def add_assistant_message(
        self,
        conversation_id: str,
        explanation: str,
        code: Optional[str] = None,
        hook_names: Optional[List[str]] = None
    ) -> None:
        """Add bot's response to conversation history."""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        message = ConversationMessage(
            role="assistant",
            content=explanation,
            code=code,
            hook_names=hook_names,
            timestamp=datetime.utcnow().isoformat()
        )
        self.conversations[conversation_id].append(message)

    def get_conversation_history(self, conversation_id: str) -> List[ConversationMessage]:
        """Get all messages in a conversation."""
        return self.conversations.get(conversation_id, [])

    def get_context_for_followup(self, conversation_id: str) -> str:
        """
        Format conversation history as context for follow-up questions.
        Includes previous snippets and explanations.
        """
        history = self.get_conversation_history(conversation_id)
        if not history:
            return ""

        context = "Previous conversation context:\n\n"
        for msg in history:
            if msg.role == "user":
                context += f"User: {msg.content}\n"
            else:
                context += f"Assistant: {msg.content}\n"
                if msg.code:
                    context += f"Previous code snippet:\n```php\n{msg.code}\n```\n"
            context += "\n"

        return context

    def get_last_snippet(self, conversation_id: str) -> Optional[str]:
        """Get the most recent code snippet from conversation."""
        history = self.get_conversation_history(conversation_id)
        for msg in reversed(history):
            if msg.code:
                return msg.code
        return None

    def clear_conversation(self, conversation_id: str) -> None:
        """Clear a conversation (when starting fresh)."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]


# Global conversation manager instance
conversation_manager = ConversationManager()
