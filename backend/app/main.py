from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path

from app.models import ChatRequest, ChatResponse
from app.agent import SupportAgent, PLUGIN_METADATA
from app.config import settings

# Initialize FastAPI app
app = FastAPI(title="SupportBot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize support agent
support_agent = SupportAgent(
    anthropic_api_key=settings.anthropic_api_key,
    openai_api_key=settings.openai_api_key,
    zendesk_url=settings.zendesk_url,
    zendesk_email=settings.zendesk_email,
    zendesk_api_token=settings.zendesk_api_token,
    llm_provider=settings.llm_provider,
)


@app.get("/")
def root():
    return {"message": "SupportBot API is running"}


@app.get("/api/plugins")
def get_plugins():
    """Get list of available plugins."""
    return {
        "plugins": [
            {
                "id": plugin_id,
                "name": metadata["name"],
                "description": metadata["description"],
            }
            for plugin_id, metadata in PLUGIN_METADATA.items()
        ]
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Process a customer query and return code snippet or escalation."""
    try:
        result = support_agent.process_query(
            plugin_id=request.plugin_id,
            query=request.query,
            customer_email=request.email,
            conversation_id=request.conversation_id,  # Support multi-turn conversations
        )

        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
