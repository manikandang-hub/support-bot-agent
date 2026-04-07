from typing import Literal, Optional, List
from pydantic import BaseModel, EmailStr
import uuid


class ChatRequest(BaseModel):
    plugin_id: str
    query: str
    email: str
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None  # Track conversation history


class ConversationMessage(BaseModel):
    """Single message in a conversation"""
    role: Literal["user", "assistant"]
    content: str
    code: Optional[str] = None
    hook_names: Optional[List[str]] = None
    timestamp: str


class CodeSnippetResponse(BaseModel):
    action: Literal["snippet"]
    explanation: str
    code: str
    hook_names: List[str]


class EscalationResponse(BaseModel):
    action: Literal["escalate"]
    explanation: str
    ticket_id: Optional[str] = None
    ticket_url: Optional[str] = None
    reason: str


class ChatResponse(BaseModel):
    action: Literal["snippet", "escalate"]
    explanation: str
    code: Optional[str] = None
    hook_names: Optional[List[str]] = None
    ticket_id: Optional[str] = None
    ticket_url: Optional[str] = None
    reason: Optional[str] = None
    conversation_id: str  # Track conversation for follow-ups
    conversation_history: Optional[List[ConversationMessage]] = None  # Previous messages for context


class Hook(BaseModel):
    name: str
    type: Literal["action", "filter"]
    params: List[str]
    description: str
    file: str


class PluginHooks(BaseModel):
    hooks: List[Hook]


class ZendeskTicketResponse(BaseModel):
    ticket_id: str
    ticket_url: str
    created: bool
