# SupportBot - AI-Powered WordPress Plugin Support

SupportBot is an intelligent customer support agent that answers WordPress/WooCommerce plugin questions in natural language, provides instant code solutions, and escalates complex issues to your development team via Zendesk.

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Anthropic API key (Claude)
- Zendesk account (for escalations)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your credentials
cp .env.example .env
# Edit .env with your API keys:
#   ANTHROPIC_API_KEY=sk-ant-...
#   ZENDESK_URL=https://yoursubdomain.zendesk.com
#   ZENDESK_EMAIL=bot@company.com
#   ZENDESK_API_TOKEN=your_token

# Run the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

The backend will be available at `http://localhost:8001`
- API: `http://localhost:8001/api`
- Docs: `http://localhost:8001/docs`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Architecture

### How It Works

1. **Customer asks a question** via the chat interface
2. **Backend validates** the query and selected plugin
3. **Code generator (Claude API)** creates a solution based on available hooks
4. **Hook validator** checks if all hooks used actually exist in the plugin
5. **Decision:**
   - ✅ Valid solution → Return code snippet
   - ❌ Invalid hooks → Escalate to Zendesk ticket
6. **Zendesk ticket** created with full context if escalation needed

### Directory Structure

```
supportbot-hackathon/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── agent.py             # Support agent orchestration
│   │   ├── code_generator.py    # Claude API code generation
│   │   ├── hooks_validator.py   # Hook validation logic
│   │   ├── zendesk_client.py    # Zendesk API wrapper
│   │   ├── models.py            # Pydantic schemas
│   │   └── config.py            # Configuration
│   ├── knowledge_base/
│   │   ├── product-feed/        # Plugin 1 hooks
│   │   └── invoice-plugin/      # Plugin 2 hooks
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/
    ├── src/
    │   ├── components/          # React components
    │   ├── services/            # API client
    │   ├── App.jsx
    │   └── main.jsx
    ├── vite.config.js
    └── package.json
```

## Key Features

### ✅ Implemented
- **Chat Interface** - Clean, responsive UI for customer support
- **Code Generation** - Claude API generates PHP solutions based on hooks
- **Hook Validation** - Prevents hallucinated hooks through validation
- **Zendesk Integration** - Auto-escalate with full context
- **Multi-plugin Support** - Works with any plugin (product-feed, invoice-plugin, etc.)
- **Hardcoded Hooks** - Quick MVP using static JSON hooks list

### 🚀 Planned (Post-Hackathon)
- **RAG Knowledge Base** - Semantic search over plugin source code
- **Chat History** - Persist conversations
- **Authentication** - Customer accounts
- **Feedback Loop** - Learn from resolved tickets
- **Analytics** - Track common issues and escalations

## Adding a New Plugin

1. **Create hooks file:**
```bash
mkdir -p backend/knowledge_base/your-plugin
```

2. **Add hooks_list.json:**
```json
{
  "hooks": [
    {
      "name": "your_hook_name",
      "type": "filter" | "action",
      "params": ["param1", "param2"],
      "description": "What this hook does",
      "file": "class-file.php"
    }
  ]
}
```

3. **Update PLUGIN_METADATA in backend/app/agent.py:**
```python
PLUGIN_METADATA = {
    "your-plugin": {
        "name": "Your Plugin Display Name",
        "description": "Plugin description"
    }
}
```

4. **Restart backend** - hooks will be automatically loaded

## Testing

### Manual Testing

1. Start both backend and frontend servers
2. Navigate to `http://localhost:5173`
3. Try a test query:
   - **Plugin:** Product Feed
   - **Email:** test@example.com
   - **Query:** "How do I filter products before export?"

Expected: Code snippet showing `add_filter('wt_product_feed_filter_product', ...)`

4. Try an out-of-scope query:
   - **Query:** "How do I add custom database tables?"

Expected: Escalation with Zendesk ticket creation (if configured)

## API Endpoints

### GET /api/plugins
Returns list of available plugins

### POST /api/chat
Process customer query

**Request:**
```json
{
  "plugin_id": "product-feed",
  "query": "How do I filter products?",
  "email": "customer@example.com"
}
```

**Response (Code Snippet):**
```json
{
  "action": "snippet",
  "explanation": "...",
  "code": "<?php...",
  "hook_names": ["wt_product_feed_filter_product"]
}
```

**Response (Escalation):**
```json
{
  "action": "escalate",
  "explanation": "...",
  "ticket_id": "12345",
  "ticket_url": "https://...",
  "reason": "invalid_hooks"
}
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-...` |
| `ZENDESK_URL` | Zendesk subdomain URL | `https://mycompany.zendesk.com` |
| `ZENDESK_EMAIL` | Bot email for Zendesk | `bot@company.com` |
| `ZENDESK_API_TOKEN` | Zendesk API token | `your_token` |
| `CORS_ORIGINS` | Allowed origins | `["http://localhost:5173"]` |

## Troubleshooting

### Backend won't start
```bash
# Check Python version (3.8+)
python --version

# Verify virtual environment
source venv/bin/activate

# Check port 8001 is available
lsof -i :8001
```

### Frontend won't connect to backend
- Verify backend is running on `http://localhost:8001`
- Check CORS is configured correctly in `backend/app/main.py`
- Check browser console for network errors

### Claude API errors
- Verify `ANTHROPIC_API_KEY` is set correctly
- Check API key has sufficient credits
- Look for rate limiting errors

### Zendesk integration failing
- Verify Zendesk credentials in `.env`
- Test endpoint: `curl -u email/token:token https://subdomain.zendesk.com/api/v2/tickets.json`
- Check Zendesk account has API access enabled

## Development Notes

### Code Generation Quality
- Claude model: `claude-3-5-sonnet-20241022` (best code generation)
- Max tokens: 2000 (sufficient for most PHP solutions)
- Response format: Strict JSON validation

### Hook Validation Strategy
- **Triple-layer prevention:**
  1. System prompt forbids non-existent hooks
  2. Available hooks list passed to Claude
  3. Post-processing regex validation

### Zendesk Escalation
- Automatic ticket creation with full context
- Tags: `[plugin-name, supportbot, escalation]`
- Includes customer email for follow-up

## Future Enhancements

1. **RAG with Vector Search** - Semantic search over plugin source code
2. **Streaming Responses** - Real-time LLM output to frontend
3. **Multi-language** - Support non-English queries
4. **Chat History** - Persistent conversation database
5. **Feedback Ratings** - Customer feedback on solutions
6. **Performance Analytics** - Dashboard of common issues

## License

Built for hackathon 2026
