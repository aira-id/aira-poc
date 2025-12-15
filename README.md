# AIRA Voice Bot Server

FastAPI-based server for AI voice agent with integrated ASR (Automatic Speech Recognition), LLM (Large Language Model), and TTS (Text-to-Speech) pipeline.

## Features

- **WebSocket Support**: Real-time bidirectional audio streaming
- **Voice Agent Pipeline**: Integrated ASR → LLM → TTS for conversational AI

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
│   │       └── websocket.py    # WebSocket endpoint (/ws/speak)
│   ├── core/
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── middleware.py       # Custom middleware
│   └── modules/
│       └── websockets/         # WebSocket handlers
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

## Setup

### Prerequisites

- Python 3.12+
- pip (Python package manager)
- Git (for cloning models)
- Git LFS (for downloading large model files from HuggingFace)

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

5. Download models:
   ```bash
   # Create models directory
   mkdir -p models

   # Download Indonesian ASR model (Sherpa-ONNX Zipformer)
   git clone https://huggingface.co/spacewave/sherpa-onnx-streaming-zipformer2-id models/sherpa-onnx-streaming-zipformer2-id

   # Download Indonesian TTS model (VITS)
   git clone https://huggingface.co/jerichosiahaya/vits-tts-id models/vits-tts-id

   # Move speaker configuration to main directory
   mv models/vits-tts-id/speaker.pth ./speaker.pth
   ```

6. Create environment file:
   ```bash
   cp .env.example .env
   ```

7. Edit `.env` file with your configuration:
   ```bash
   nano .env  # or use your preferred editor
   ```

   **Important:** Update the following settings:
   - `LLM_ENDPOINT`: Point to your LLM service
   - `MODELS_ROOT`: Verify the path matches your setup (default: `/home/fitra/Workspaces/aira-server/models`)
   - Other ASR/TTS settings as needed

## Configuration

Configure the following in your `.env` file:

- **Application Settings**: `APP_NAME`, `DEBUG`, `HOST`, `PORT`
- **CORS Settings**: `CORS_ORIGINS`
- **Logging**: `LOG_LEVEL`, `LOG_FILE`
- **ASR Settings**: `ASR_MODEL`, `ASR_LANG`, `ASR_SAMPLE_RATE`
- **LLM Settings**: `LLM_ENDPOINT`, `LLM_MODEL`, `LLM_SYSTEM_PROMPT`, `LLM_MAX_TOKENS`, `LLM_TEMPERATURE`
- **TTS Settings**: `TTS_MODEL`, `TTS_SPEAKER`, `TTS_SAMPLE_RATE`, `TTS_SPEED`, `TTS_SPLIT`, `TTS_PROVIDER`, `TTS_THREADS`, `MODELS_ROOT`

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

## API Endpoints

### Web Interface

- `GET /` - Voice agent web interface (served from `web-ui/index/`)

### Health Check

- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check with service status

### WebSocket Endpoint

- `WS /ws/speak` - Voice Agent endpoint (ASR → LLM → TTS pipeline)

#### WebSocket Message Format for `/ws/speak`

**Client → Server (Start Session):**
```json
{
  "type": "start_session"
}
```

All configuration is read from the server's `.env` file. You can optionally override settings by including them in the start_session message:

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

The LLM endpoint and other LLM settings are configured in your `.env` file:

```bash
LLM_ENDPOINT=http://localhost:8080/v1/chat/completions
LLM_MODEL=gemma_1b_q8_0
LLM_SYSTEM_PROMPT=You are a helpful assistant.
LLM_MAX_TOKENS=150
LLM_TEMPERATURE=0.7
```

Update these values to match your LLM service configuration.

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

## Model Setup

The voice agent requires ASR and TTS models to function. Models are not included in the repository and must be downloaded separately.

### TTS Model Setup

Download the Indonesian TTS model from HuggingFace:

1. **Download the TTS model:**
   ```bash
   # Create models directory if it doesn't exist
   mkdir -p models

   # Clone the model repository
   git clone https://huggingface.co/jerichosiahaya/vits-tts-id models/vits-tts-id
   ```

2. **Move speaker configuration:**
   ```bash
   # Move speaker.pth to the main project directory
   mv models/vits-tts-id/speaker.pth ./speaker.pth
   ```

3. **Verify model structure:**
   ```
   aira-server/
   ├── models/
   │   └── vits-tts-id/
   │       ├── config.json
   │       ├── model.pth
   │       └── (other model files)
   ├── speaker.pth          # Speaker configuration
   └── ...
   ```

**Model Information:**
- **Source**: [jerichosiahaya/vits-tts-id](https://huggingface.co/jerichosiahaya/vits-tts-id)
- **Type**: VITS (Variational Inference with adversarial learning for end-to-end Text-to-Speech)
- **Language**: Indonesian (ID)
- **Speakers**: Multiple Indonesian voices

### ASR Model Setup

Download the Indonesian ASR model from HuggingFace:

1. **Download the ASR model:**
   ```bash
   # Create models directory if it doesn't exist
   mkdir -p models

   # Clone the model repository
   git clone https://huggingface.co/spacewave/sherpa-onnx-streaming-zipformer2-id models/sherpa-onnx-streaming-zipformer2-id
   ```

2. **Verify model structure:**
   ```
   aira-server/
   ├── models/
   │   ├── sherpa-onnx-streaming-zipformer2-id/
   │   │   ├── encoder-epoch-99-avg-1.onnx
   │   │   ├── decoder-epoch-99-avg-1.onnx
   │   │   ├── joiner-epoch-99-avg-1.onnx
   │   │   ├── tokens.txt
   │   │   └── (other model files)
   │   └── vits-tts-id/
   │       └── ...
   └── ...
   ```

3. **Configure in `.env` file:**
   ```bash
   ASR_MODEL=zipformer
   ASR_LANG=id
   MODELS_ROOT=/home/fitra/Workspaces/aira-server/models
   ```

**Model Information:**
- **Source**: [spacewave/sherpa-onnx-streaming-zipformer2-id](https://huggingface.co/spacewave/sherpa-onnx-streaming-zipformer2-id)
- **Type**: Sherpa-ONNX Streaming Zipformer2
- **Framework**: ONNX Runtime (optimized for CPU/GPU inference)
- **Language**: Indonesian (ID)
- **Features**: Real-time streaming ASR with low latency

## Voice Pipeline Modules

The voice agent pipeline consists of three main components:

### ASR Module

The ASR module is located in `aira/asr/`. This handles speech-to-text conversion.

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

The TTS module is located in `aira/tts/`. This handles text-to-speech synthesis.

```python
# Example structure
async def initialize(self):
    # Load your TTS model (e.g., Piper, Coqui TTS)
    pass

async def synthesize(self, text: str, **kwargs) -> bytes:
    # Implement audio synthesis logic
    pass
```

### Integration

All three components (ASR, LLM, TTS) are integrated in the voice agent handler at `app/modules/websockets/speak_handler.py`, which orchestrates the complete conversational pipeline.

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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions to this project.
