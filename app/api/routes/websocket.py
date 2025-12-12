"""
WebSocket Route Definitions.

This module defines WebSocket endpoints for real-time voice processing:
- /ws/speak: AI Voice Agent endpoint with LLM integration (ASR→LLM→TTS audio pipeline)

Each endpoint generates a unique client ID and delegates connection handling
to specialized handler classes.
"""

import uuid
from fastapi import APIRouter, WebSocket
from app.modules.websockets import speak_ws_handler

router = APIRouter(tags=["websocket"])

@router.websocket("/ws/speak")
async def websocket_speak_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for AI Voice Agent with LLM Integration.

    Accepts WebSocket connections for AI voice agent interactions where audio input
    is automatically transcribed (ASR), processed by an LLM for intelligent responses,
    and synthesized back as audio (TTS), creating a complete conversational voice AI.
    The system maintains chat history for context-aware conversations.

    Pipeline Flow:
        Client audio → ASR transcription → LLM chat completion → TTS synthesis → Audio back to client

    Protocol:
        1. Client connects to /ws/speak
        2. Client sends start_session message with ASR, LLM, and TTS configuration
        3. Client streams audio bytes (PCM format, 16kHz recommended)
        4. Server automatically:
           a. Transcribes audio to text (ASR)
           b. Sends transcription result to client (optional visibility)
           c. Forwards transcription to LLM with conversation history
           d. Gets intelligent response from LLM
           e. Sends LLM response to client (optional visibility)
           f. Forwards LLM response to TTS for synthesis
           g. Streams synthesized audio back to client
        5. Client sends end_session to close the session

    Message Types:
        Input (Client → Server):
        - start_session: Initialize voice agent pipeline with LLM
          {
            "type": "start_session",
            "asr_model": "zipformer",
            "asr_lang": "id",
            "llm_model": "qwen2.5-0.5b-instruct",
            "llm_system_prompt": "You are a helpful assistant.",
            "llm_max_tokens": 512,
            "llm_temperature": 0.7,
            "sample_rate": 16000,
            "speed": 1.0,
            "tts_model": "vits",
            "tts_speaker": "speaker_id"
          }
        - audio bytes: Raw PCM audio for ASR processing (auto-forwarded to LLM then TTS)
        - end_session: Close voice agent pipeline and clear chat history
          {
            "type": "end_session"
          }
        - ping: Heartbeat message
          {
            "type": "ping"
          }

        Output (Server → Client):
        - session_started: Confirmation that voice agent pipeline is ready
          {
            "type": "session_started",
            "client_id": "uuid",
            "mode": "voice_agent_llm",
            "pipeline": "audio -> ASR -> LLM -> TTS -> audio",
            "llm_model": "qwen2.5-0.5b-instruct",
            "has_system_prompt": true
          }
        - ASR results: JSON with transcription (for visibility/logging)
          {
            "type": "asr_result",
            "text": "transcribed text",
            "finished": true
          }
        - LLM response: JSON with intelligent response (for visibility/logging)
          {
            "type": "llm_response",
            "text": "assistant response"
          }
        - TTS audio: Binary PCM audio chunks (synthesized LLM response)
        - TTS finished: JSON notification when synthesis completes
          {
            "finished": true
          }
        - session_ended: Confirmation of session closure
          {
            "type": "session_ended"
          }
        - pong: Heartbeat response
          {
            "type": "pong"
          }
        - error: Error notification
          {
            "type": "error",
            "message": "error description"
          }

    Features:
        - Automatic ASR → LLM → TTS pipeline (fully automated conversation)
        - LLM-powered intelligent responses with context awareness
        - Conversation history management per session
        - Configurable system prompts for AI personality
        - Real-time audio streaming with configurable voice and speed
        - Transparent intermediate results (ASR, LLM) for monitoring
        - Low-latency streaming for natural conversation flow

    Args:
        websocket: The WebSocket connection from the client
    """
    client_id = str(uuid.uuid4())
    await speak_ws_handler.handle_connection(websocket, client_id)
