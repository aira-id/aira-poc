# AIRA Voice Bot Server

FastAPI-based server for voice bot interactions with support for ASR (Automatic Speech Recognition), LLM (Large Language Model), and TTS (Text-to-Speech) modules.

## Features

- **FastAPI Framework**: High-performance async web framework
- **WebSocket Support**: Real-time bidirectional audio streaming
- **Modular Architecture**: Separate modules for ASR, LLM, and TTS
- **CORS Enabled**: Cross-origin resource sharing configured
- **Logging**: Comprehensive logging to console and file
- **Error Handling**: Global error handling middleware
- **Health Checks**: Health and readiness endpoints
- **Environment Configuration**: .env file support

## Project Structure

```
aira-server/
├── main.py                     # FastAPI application entry point
├── app/
│   ├── config.py               # Configuration management
│   ├── logging_config.py       # Logging setup
│   ├── api/
│   │   └── routes/
│   │       ├── health.py       # Health check endpoints
│   │       ├── index.py        # Index/root route
│   │       └── websocket.py    # WebSocket endpoints (/ws/asr, /ws/tts, /ws/speak)
│   ├── core/
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── middleware.py       # Custom middleware
│   └── modules/
│       └── websockets/         # WebSocket handlers
│           ├── asr_handler.py
│           ├── tts_handler.py
│           └── speak_handler.py  # Voice agent with LLM integration
├── aira/
│   ├── asr/                    # ASR (Automatic Speech Recognition) module
│   └── tts/                    # TTS (Text-to-Speech) module
├── web-ui/
│   └── index/
│       ├── index.html          # Voice agent web interface
│       └── audio_process.js    # Audio worklet processor
├── models/                     # Model files directory
├── tests/                      # Test files
├── venv/                       # Virtual environment
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore file
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

**Note:** The internal LLM module has been removed. AIRA now uses external LLM services via OpenAI-compatible APIs (see [LLM Setup](#llm-setup) section).

## Setup

### Prerequisites

- Python 3.12+
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd aira-server
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```

3. Activate the virtual environment:
   ```bash
   source venv/bin/activate  # On Linux/Mac
   # or
   venv\Scripts\activate  # On Windows
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create environment file:
   ```bash
   cp .env.example .env
   ```

6. Edit `.env` file with your configuration:
   ```bash
   nano .env  # or use your preferred editor
   ```

## Configuration

Configure the following in your `.env` file:

- **Application Settings**: `APP_NAME`, `DEBUG`, `HOST`, `PORT`
- **CORS Settings**: `CORS_ORIGINS`
- **Logging**: `LOG_LEVEL`, `LOG_FILE`

**Note:** ASR and TTS configuration is passed via WebSocket session messages, not environment variables. LLM configuration is set in the code (see [LLM Setup](#llm-setup)).

## Running the Server

### Development Mode

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Accessing the Application

Once the server is running:

- **Web Interface**: Open http://localhost:8000 in your browser
  - Interactive voice agent with real-time audio streaming
  - Visual state indicators (listening/thinking/speaking)
  - Connection status and statistics display

- **API Documentation**:
  - **Swagger UI**: http://localhost:8000/docs
  - **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Web Interface

- `GET /` - Voice agent web interface (served from `web-ui/index/`)

### Health Check

- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check with service status

### WebSocket Endpoints

- `WS /ws/asr` - ASR (Speech-to-Text) endpoint
- `WS /ws/tts` - TTS (Text-to-Speech) endpoint
- `WS /ws/speak` - Voice Agent endpoint (ASR → LLM → TTS pipeline)

#### WebSocket Message Format for `/ws/speak`

**Client → Server (Start Session):**
```json
{
  "type": "start_session",
  "asr_model": "zipformer",
  "asr_lang": "id",
  "tts_speaker": "wibowo",
  "sample_rate": 16000,
  "speed": 1.0,
  "split": true,
  "llm_model": "gemma_1b_q8_0"
}
```

**Client → Server (Audio Stream):**
- Send raw audio bytes (PCM16, 16kHz) for ASR processing

**Server → Client (State Changes):**
```json
{
  "type": "state_change",
  "state": "listening|thinking|speaking"
}
```

**Server → Client (TTS Finished):**
```json
{
  "finished": true,
  "samples": 12345
}
```

**Server → Client (Audio Stream):**
- Receive audio bytes (TTS output, PCM16, 16kHz)

## Testing

The project includes a comprehensive test suite covering configuration, middleware, exceptions, health endpoints, WebSocket routes, and the main application.

### Running Tests

**Run all tests:**
```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_config.py -v

# Run specific test function
pytest tests/test_health.py::test_health_check_status -v
```

**Run tests with coverage:**
```bash
# Install pytest-cov if not already installed
pip install pytest-cov

# Run with coverage report
pytest --cov=app --cov-report=html --cov-report=term-missing

# View HTML coverage report
open htmlcov/index.html  # On macOS
xdg-open htmlcov/index.html  # On Linux
```

**Run tests by category:**
```bash
# Run only unit tests (when marked)
pytest -m unit

# Run only integration tests (when marked)
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_config.py           # Configuration and settings tests
├── test_exceptions.py       # Custom exception tests
├── test_middleware.py       # Middleware tests
├── test_health.py           # Health endpoint tests
├── test_main.py             # Main application tests
└── test_websocket.py        # WebSocket endpoint tests
```

### Test Coverage

- **67 tests** covering:
  - Configuration loading and validation (6 tests)
  - Custom exceptions and error handling (7 tests)
  - Middleware functionality (9 tests)
  - Health check endpoints (11 tests)
  - Main application setup (17 tests)
  - WebSocket endpoints (17 tests)

### Writing New Tests

Add new test files to the `tests/` directory following the naming convention `test_*.py`. Use the fixtures from `conftest.py`:

```python
def test_example(client):
    """Test using the test client fixture."""
    response = client.get("/your-endpoint")
    assert response.status_code == 200
```

## LLM Setup

AIRA uses external LLM services via **OpenAI-compatible APIs**. The system communicates with any LLM provider that implements the OpenAI Chat Completions API format.

### Requirements

Your LLM service must support the OpenAI Chat Completions API endpoint:

```
POST /v1/chat/completions
```

### Compatible LLM Providers

AIRA works with any OpenAI API-compatible service, including:

- **llama.cpp server** - Lightweight local inference
- **Ollama** - Easy local model management
- **LM Studio** - GUI-based local inference
- **vLLM** - High-throughput inference server
- **LocalAI** - OpenAI alternative
- **OpenAI API** - Official OpenAI service
- **Azure OpenAI** - Microsoft's OpenAI service
- **Together.ai** - Cloud-hosted inference
- **Groq** - Ultra-fast inference API
- **Any other OpenAI-compatible API**

### Configuration

The LLM endpoint is configured in [app/modules/websockets/speak_handler.py](app/modules/websockets/speak_handler.py):

```python
# Line ~79
self.llm_endpoint = "http://localhost:8080/v1/chat/completions"
```

Update this URL to point to your LLM service endpoint.

### API Format

The system sends requests in OpenAI Chat Completions format:

```json
{
  "model": "model-name",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi there!"}
  ],
  "temperature": 0.7,
  "max_tokens": 150
}
```

Expected response format:

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Response text here"
      }
    }
  ]
}
```

### Testing Your LLM Service

Test your LLM endpoint with curl:

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-model-name",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

## Voice Agent Features

The voice agent (`/ws/speak`) includes:

- **Real-time Audio Processing**: Continuous audio stream from microphone
- **State Management**: Visual feedback with three states:
  - **Listening**: Ready to receive user speech
  - **Thinking**: Processing speech through ASR and LLM
  - **Speaking**: Generating and playing TTS audio
- **Audio Feedback Prevention**: Automatic microphone muting during TTS playback
- **Chat History**: Maintains conversation context for LLM
- **Token-based Trimming**: Automatically trims old messages when context limit reached

## Implementing ASR/TTS Modules

### ASR Module

The ASR module is located in `aira/asr/`. Implement your ASR provider there.

```python
# Example structure
async def initialize(self):
    # Load your ASR model (e.g., Whisper, Faster-Whisper, Zipformer)
    pass

async def transcribe(self, audio_data: bytes) -> str:
    # Implement transcription logic
    pass
```

### TTS Module

The TTS module is located in `aira/tts/`. Implement your TTS provider there.

```python
# Example structure
async def initialize(self):
    # Load your TTS model (e.g., Piper, Coqui TTS)
    pass

async def synthesize(self, text: str, **kwargs) -> bytes:
    # Implement audio synthesis logic
    pass
```

## Development

### Adding New Dependencies

```bash
pip install <package-name>
pip freeze > requirements.txt
```

### Logging

Logs are written to:
- Console (stdout)
- File specified in `LOG_FILE` environment variable

Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
