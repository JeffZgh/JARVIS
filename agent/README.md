# JARVIS Agent

A modular, extensible AI agent system with web interface, comprehensive conversation memory, and configurable LLM settings.

## Features

- 🤖 **Conversational AI Assistant** with context-aware memory
- 🌐 **Web Interface** with real-time WebSocket communication
- 🔧 **Configurable LLM Settings** (model, temperature, tokens, etc.)
- 📝 **Comprehensive Memory System** with event tracking
- 🛡️ **Safety & Permission Model** (policy layer for tool execution)
- 🔄 **Modular Architecture** for easy extension
- 📊 **REST API** with WebSocket support
- 🎯 **Session Management** with isolated conversation contexts

## Quick Start

### 1. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Required: OpenAI API Key
export OPENAI_API_KEY="your-openai-api-key-here"

# Optional: LLM Configuration
export LLM_MODEL="gpt-4o-mini"
export LLM_TEMPERATURE="0.7"
export LLM_MAX_TOKENS="2000"

# Optional: Agent Configuration
export AGENT_NAME="JARVIS Assistant"
export MAX_CONVERSATION_HISTORY="100"
```

### 3. Run the Server

```bash
# Start the server
python3 server_main.py

# Or with uvicorn directly
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access the Interface

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/api

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | Required | OpenAI API key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI API base URL |
| `LLM_MODEL` | `gpt-4o-mini` | LLM model to use |
| `LLM_TEMPERATURE` | `0.7` | Response creativity (0.0-2.0) |
| `LLM_MAX_TOKENS` | `2000` | Maximum response tokens |
| `LLM_TOP_P` | `1.0` | Nucleus sampling (0.0-1.0) |
| `LLM_FREQUENCY_PENALTY` | `0.0` | Frequency penalty (-2.0-2.0) |
| `LLM_PRESENCE_PENALTY` | `0.0` | Presence penalty (-2.0-2.0) |
| `AGENT_NAME` | `JARVIS Assistant` | Agent display name |
| `MAX_CONVERSATION_HISTORY` | `100` | Max messages in memory |
| `CONTEXT_WINDOW_SIZE` | `20` | Messages for AI context |
| `ENABLE_GUARDRAILS` | `true` | Enable safety checks |
| `DEFAULT_PERMISSION_LEVEL` | `read` | Default tool permission |

### LLM Settings Examples

```bash
# Creative responses
export LLM_TEMPERATURE="1.2"

# Analytical responses
export LLM_TEMPERATURE="0.2"

# Use GPT-4
export LLM_MODEL="gpt-4"

# Longer responses
export LLM_MAX_TOKENS="4000"
```

## API Usage

### Chat API

```bash
# Send a message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello JARVIS!", "session_id": "user123"}'

# Get chat history
curl http://localhost:8000/chat/history/user123

# Clear session
curl -X DELETE http://localhost:8000/sessions/user123
```

### Configuration API

```bash
# Get current LLM settings
curl http://localhost:8000/config/llm

# Update LLM settings
curl -X PUT http://localhost:8000/config/llm \
  -H "Content-Type: application/json" \
  -d '{"temperature": 0.9, "max_tokens": 1500}'

# Get full configuration
curl http://localhost:8000/config
```

### WebSocket API

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/session123');

// Send message
ws.send(JSON.stringify({
  message: "Hello JARVIS!",
  message_type: "text"
}));

// Receive messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.response);
};
```

## Project Structure

```
agent/
├── core/                   # Core agent logic
│   ├── agent.py          # Main agent class
│   ├── memory.py         # Conversation memory system
│   └── config.py         # Configuration management
├── server/                # FastAPI server
│   ├── app.py            # Main application
│   └── routes/           # API routes
├── interfaces/            # User interfaces
│   ├── web_interface.py  # Web interface handler
│   └── web/              # Web UI files
│       ├── static/       # CSS/JS assets
│       └── templates/    # HTML templates
├── tools/                 # Atomic tools (future)
├── skills/                # Multi-step workflows (future)
├── main.py               # Command-line interface
├── server_main.py        # Server entry point
└── requirements.txt      # Python dependencies
```

## Architecture

The JARVIS Agent follows a modular architecture with clear separation of concerns:

1. **Core Layer**: Agent orchestration and memory management
2. **Policy Layer**: Safety checks and permission controls
3. **Interface Layer**: Web, voice, and API interfaces
4. **Execution Layer**: Tools and skills for agent capabilities
5. **Memory System**: Layered memory (short-term, long-term, event logs)

## Development

### Running Tests

```bash
# Run unit tests (when implemented)
python -m pytest tests/

# Run with coverage
python -m pytest --cov=agent tests/
```

### Code Style

```bash
# Format code
black .

# Check linting
flake8 agent/
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **API Key Issues**
   - Ensure `OPENAI_API_KEY` is set correctly
   - Check if the key has sufficient credits

3. **Port Already in Use**
   ```bash
   # Kill process on port 8000
   lsof -ti:8000 | xargs kill -9
   
   # Or use different port
   uvicorn server.app:app --port 8001
   ```

4. **Memory Issues**
   - Reduce `MAX_CONVERSATION_HISTORY`
   - Clear old sessions regularly

### Debug Mode

```bash
# Enable debug logging
export DEBUG=true
python server_main.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Roadmap

- [ ] Voice interface support
- [ ] Tool execution system
- [ ] Advanced guardrails
- [ ] Multi-language support
- [ ] Docker deployment
- [ ] Monitoring and analytics
