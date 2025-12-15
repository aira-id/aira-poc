"""
Speak WebSocket Handler.

This module handles WebSocket connections for AI voice agent interactions.
It creates an audio-to-audio pipeline where spoken input is automatically
transcribed (ASR), processed by an LLM, and synthesized back as speech (TTS).

The handler supports:
- Voice agent mode: audio in -> ASR -> LLM -> TTS -> audio out (full AI pipeline)
- Session lifecycle management for ASR, LLM, and TTS
- Real-time audio streaming and processing
- Chat history management for contextual conversations
- Automatic text-to-speech conversion of LLM responses
- Configurable ASR, LLM, and TTS parameters

Architecture:
    Audio Pipeline Flow:
    Client sends audio -> ASR transcribes -> LLM processes with context -> TTS synthesis -> Audio back to client

    Three concurrent tasks:
    1. Receiving audio messages from client
    2. Reading ASR results, sending to LLM, and feeding responses to TTS (pipeline connector)
    3. Sending TTS audio chunks back to client
"""

import asyncio
import json
import httpx
from enum import Enum
from fastapi import WebSocket, WebSocketDisconnect
from app.config import settings
from app.logging_config import logger
from app.modules.websockets.manager import ws_manager
from aira.asr.sherpa_onnx.asr import start_asr_stream
from aira.asr.sherpa_onnx.result import ASRResult
from aira.tts.coqui_tts.tts import start_tts_stream
from aira.tts.coqui_tts.result import TTSResult


class AgentState(Enum):
    """
    Voice agent states for managing pipeline flow.

    States:
    - LISTENING: System is idle and ready to receive audio stream
    - THINKING: ASR is transcribing, sending to LLM, and receiving response
    - SPEAKING: TTS is processing text into audio and sending to WebSocket
    """
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


class SpeakWebSocketHandler:
    """
    Handles WebSocket connections for AI voice agent (audio-to-audio with LLM).

    Manages the complete voice pipeline including:
    - WebSocket connection handling
    - Audio input streaming and ASR processing
    - Chat history management for contextual conversations
    - LLM integration for intelligent responses
    - Automatic LLM response forwarding to TTS
    - Audio output streaming back to client
    - Unified session management

    The handler runs three concurrent tasks:
    1. Receiving audio from the client
    2. Processing ASR results, sending to LLM with context, and feeding responses to TTS (pipeline connector)
    3. Sending TTS audio chunks back to the client
    """

    def __init__(self):
        """Initialize the Speak WebSocket handler."""
        # Store chat history per client
        self.chat_histories = {}
        # Store agent state per client
        self.agent_states = {}
        # LLM API endpoint from config
        self.llm_endpoint = settings.llm_endpoint

    async def handle_connection(self, websocket: WebSocket, client_id: str):
        """
        Handle WebSocket connection lifecycle.

        Manages the full lifecycle of a voice agent WebSocket connection by running
        three concurrent tasks: one for receiving audio, one for the ASR->TTS pipeline,
        and one for sending audio back. Ensures proper cleanup on disconnection or errors.

        Args:
            websocket: The WebSocket connection
            client_id: Unique identifier for the client
        """
        await ws_manager.connect(websocket, client_id)

        # Initialize chat history for this client
        self.chat_histories[client_id] = []

        # Initialize agent state (start with LISTENING when session starts)
        self.agent_states[client_id] = AgentState.LISTENING

        # Use dictionaries to make streams mutable for nested functions
        asr_stream_container = {"stream": None}
        tts_stream_container = {"stream": None}
        llm_config = {"model_name": settings.llm_model}  # Default LLM model from config

        async def task_receive_audio():
            """Continuously receive and process audio from the client."""
            while True:
                data = await websocket.receive()

                if "text" in data:
                    # Handle control messages (ping, start_session, end_session)
                    await self.handle_control_message(
                        client_id,
                        asr_stream_container,
                        tts_stream_container,
                        llm_config,
                        data["text"]
                    )
                elif "bytes" in data:
                    # Handle audio data for ASR processing
                    await self.handle_audio_data(
                        client_id,
                        asr_stream_container,
                        data["bytes"]
                    )

        async def task_asr_to_tts_pipeline():
            """
            Pipeline connector: Read ASR results, send to LLM, and feed response to TTS.

            Manages state transitions through the pipeline:
            1. LISTENING -> THINKING: When ASR produces final transcription
            2. THINKING: During LLM processing
            3. THINKING -> SPEAKING: When TTS starts synthesis
            4. Getting transcribed text from ASR
            5. Sending it to LLM with chat history
            6. Getting LLM response
            7. Sending response to TTS for synthesis
            """
            while True:
                if asr_stream_container["stream"] is not None:
                    result: ASRResult = await asr_stream_container["stream"].read()
                    if not result:
                        return

                    # Send ASR result to client for visibility (optional)
                    result_dict = result.to_dict()
                    await websocket.send_json(result_dict)

                    # Auto-forward final transcriptions to LLM then TTS
                    if result_dict.get("finished") and result_dict.get("text"):
                        user_text = result_dict["text"].strip()
                        if user_text and tts_stream_container["stream"] is not None:
                            # Only process if in LISTENING state (prevent overlapping conversations)
                            if self.agent_states.get(client_id) != AgentState.LISTENING:
                                logger.warning(f"Ignoring transcription - agent is {self.agent_states.get(client_id).value}")
                                continue

                            # Transition to THINKING state
                            await self.set_agent_state(client_id, AgentState.THINKING)

                            logger.info(f"Pipeline: User said for {client_id}: {user_text}")

                            # Add user message to chat history
                            self.chat_histories[client_id].append({
                                "role": "user",
                                "content": user_text.lower()
                            })

                            try:
                                # Send to LLM and get response (still in THINKING state)
                                llm_response = await self.get_llm_response(
                                    client_id,
                                    llm_config["model_name"]
                                )

                                if llm_response:
                                    logger.info(f"Pipeline: LLM responded for {client_id}: {llm_response}")

                                    # Add assistant message to chat history
                                    self.chat_histories[client_id].append({
                                        "role": "assistant",
                                        "content": llm_response.lower()
                                    })

                                    # Transition to SPEAKING state before sending to TTS
                                    await self.set_agent_state(client_id, AgentState.SPEAKING)

                                    # Send LLM response to TTS
                                    await tts_stream_container["stream"].write(llm_response, True)
                                else:
                                    logger.warning(f"Pipeline: No LLM response for {client_id}")
                                    # Return to LISTENING if LLM fails
                                    await self.set_agent_state(client_id, AgentState.LISTENING)
                            except Exception as e:
                                logger.error(f"Pipeline: Error getting LLM response for {client_id}: {str(e)}")
                                # Return to LISTENING on error
                                await self.set_agent_state(client_id, AgentState.LISTENING)
                                # Fallback to echo if LLM fails
                                await tts_stream_container["stream"].write(user_text, True)
                else:
                    await asyncio.sleep(0.5)

        async def task_send_tts_audio():
            """
            Continuously read TTS results and stream audio to the client.

            Manages state transition:
            - SPEAKING -> LISTENING: When TTS finishes synthesis
            """
            while not tts_stream_container["stream"]:
                # Wait for TTS stream to be created
                await asyncio.sleep(0.1)

            while True:
                result: TTSResult = await tts_stream_container["stream"].read()

                if not result:
                    return

                if result.finished:
                    # Send finished notification as JSON
                    result_dict = result.to_dict()
                    await websocket.send_json(result_dict)

                    # Transition back to LISTENING state (ready for next user input)
                    await self.set_agent_state(client_id, AgentState.LISTENING)
                else:
                    # Stream audio in chunks for better real-time performance
                    await websocket.send_bytes(result.pcm_bytes)

        try:
            await asyncio.gather(
                task_receive_audio(),
                task_asr_to_tts_pipeline(),
                task_send_tts_audio()
            )
        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected")
            ws_manager.disconnect(client_id)
        except Exception as e:
            logger.error(f"Error handling WebSocket for {client_id}: {str(e)}")
            ws_manager.disconnect(client_id)
        finally:
            # Cleanup both streams
            if asr_stream_container["stream"] is not None:
                await asr_stream_container["stream"].close()
            if tts_stream_container["stream"] is not None:
                await tts_stream_container["stream"].close()
            # Cleanup chat history
            if client_id in self.chat_histories:
                del self.chat_histories[client_id]
            # Cleanup agent state
            if client_id in self.agent_states:
                del self.agent_states[client_id]

    async def handle_control_message(
        self,
        client_id: str,
        asr_stream_container: dict,
        tts_stream_container: dict,
        llm_config: dict,
        message: str
    ):
        """
        Handle control messages from client.

        Processes JSON-formatted control messages including ping, start_session,
        and end_session. Invalid JSON or unknown message types are logged.

        Args:
            client_id: Unique identifier for the client
            asr_stream_container: Container holding the ASR stream
            tts_stream_container: Container holding the TTS stream
            llm_config: Container holding the LLM configuration
            message: JSON-formatted control message from client
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")

            logger.info(f"Received control message from {client_id}: type={message_type}")

            if message_type == "ping":
                await ws_manager.send_text(
                    client_id,
                    json.dumps({"type": "pong"})
                )
            elif message_type == "start_session":
                await self.start_session(
                    client_id,
                    asr_stream_container,
                    tts_stream_container,
                    llm_config,
                    data
                )
            elif message_type == "end_session":
                await self.end_session(
                    client_id,
                    asr_stream_container,
                    tts_stream_container
                )
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from {client_id}")
        except Exception as e:
            logger.error(f"Error handling control message: {str(e)}")

    async def handle_audio_data(
        self,
        client_id: str,
        asr_stream_container: dict,
        audio_data: bytes
    ):
        """
        Handle audio data from client for ASR processing.

        Only processes audio if agent is in LISTENING state to prevent overlapping operations
        and ensure proper conversation flow (user/assistant alternation).

        Args:
            client_id: Unique identifier for the client
            asr_stream_container: Container holding the ASR stream
            audio_data: Raw audio bytes from client (PCM format, 16kHz expected)
        """
        try:
            # Only accept audio when in LISTENING state
            if self.agent_states.get(client_id) != AgentState.LISTENING:
                logger.debug(f"Ignoring audio data for {client_id} - state is {self.agent_states.get(client_id).value}")
                return

            logger.debug(f"Received audio data from {client_id}: {len(audio_data)} bytes")

            if asr_stream_container["stream"] is not None:
                await asr_stream_container["stream"].write(audio_data)
        except Exception as e:
            logger.error(f"Error handling audio data: {str(e)}")
            await ws_manager.send_text(
                client_id,
                json.dumps({
                    "type": "error",
                    "message": f"Error processing audio: {str(e)}"
                })
            )

    async def set_agent_state(self, client_id: str, state: AgentState):
        """
        Set agent state and notify client.

        Args:
            client_id: Unique identifier for the client
            state: New state to set
        """
        self.agent_states[client_id] = state
        logger.info(f"Agent state changed for {client_id}: {state.value}")

        # Notify client of state change
        await ws_manager.send_text(
            client_id,
            json.dumps({
                "type": "state_change",
                "state": state.value
            })
        )

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text.
        Uses a simple approximation: ~4 characters per token for English/Indonesian.

        Args:
            text: The text to estimate tokens for

        Returns:
            Estimated number of tokens
        """
        return len(text) // 4

    def trim_chat_history(self, client_id: str, max_tokens: int = 800) -> list:
        """
        Trim chat history to fit within token limit, keeping most recent messages.

        Args:
            client_id: Unique identifier for the client
            max_tokens: Maximum tokens to keep in history (default: 800)

        Returns:
            Trimmed list of messages
        """
        chat_history = self.chat_histories[client_id]

        if not chat_history:
            return []

        # Start from the end (most recent) and work backwards
        trimmed_messages = []
        current_tokens = 0

        for message in reversed(chat_history):
            message_tokens = self.estimate_tokens(message["content"])

            if current_tokens + message_tokens <= max_tokens:
                trimmed_messages.insert(0, message)
                current_tokens += message_tokens
            else:
                # Stop adding messages if we exceed the limit
                break

        logger.info(f"Trimmed chat history for {client_id}: kept {len(trimmed_messages)}/{len(chat_history)} messages (~{current_tokens} tokens)")
        return trimmed_messages

    async def get_llm_response(self, client_id: str, model_name: str) -> str:
        """
        Send chat history to LLM and get response.

        Args:
            client_id: Unique identifier for the client
            model_name: Name of the LLM model to use

        Returns:
            The LLM response text, or empty string if error occurs
        """
        try:
            # Prepare system prompt from config
            system_prompt = {
                "role": "system",
                "content": settings.llm_system_prompt
            }

            # Trim chat history to fit within token limit (keeping most recent)
            trimmed_history = self.trim_chat_history(client_id, max_tokens=800)

            # Prepare messages with system prompt at the beginning
            messages = [system_prompt] + trimmed_history

            # Prepare chat completion request with config values
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": settings.llm_temperature,
                "max_tokens": settings.llm_max_tokens,
                "stream": False
            }

            logger.debug(f"LLM request payload: {payload}")

            # Send request to LLM endpoint
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.llm_endpoint,
                    json=payload
                )
                response.raise_for_status()

                # Parse response
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    message = result["choices"][0].get("message", {})
                    return message.get("content", "").strip()

            return ""
        except httpx.TimeoutException:
            logger.error(f"LLM request timeout for {client_id}")
            return ""
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM HTTP error for {client_id}: {e.response.status_code}")
            return ""
        except Exception as e:
            logger.error(f"LLM request error for {client_id}: {str(e)}")
            return ""

    async def start_session(
        self,
        client_id: str,
        asr_stream_container: dict,
        tts_stream_container: dict,
        llm_config: dict,
        data: dict
    ):
        """
        Start a new voice agent session.

        Initializes ASR, LLM, and TTS with the specified configuration and sends
        a session_started confirmation to the client. The streams will be connected in
        a pipeline where ASR output feeds into LLM, then LLM output feeds into TTS.

        Args:
            client_id: Unique identifier for the client
            asr_stream_container: Container to store the initialized ASR stream
            tts_stream_container: Container to store the initialized TTS stream
            llm_config: Container to store the LLM configuration
            data: Session configuration containing:
                ASR parameters:
                - asr_model: ASR model to use (e.g., "zipformer", "sensevoice")
                - asr_lang: Language code (e.g., "id" for Indonesian)

                LLM parameters:
                - llm_model: LLM model to use (optional, defaults to gemma_270m_q8_0)

                TTS parameters:
                - sample_rate: Audio sample rate (e.g., 16000, 22050)
                - speed: Speech speed multiplier (e.g., 1.0 for normal)
                - tts_model: TTS model to use
                - tts_speaker: Speaker voice identifier
        """
        logger.info(f"Starting voice agent session for {client_id}")

        # Update LLM model name from session data or use config default
        llm_config["model_name"] = data.get("llm_model", settings.llm_model)
        logger.info(f"Using LLM model: {llm_config['model_name']}")

        # Initialize ASR stream with config defaults, allow session override
        asr_config = {
            "threads": settings.tts_threads,
            "models_root": settings.models_root,
            "asr_provider": "cpu",
            "asr_model": data.get("asr_model", settings.asr_model),
            "asr_lang": data.get("asr_lang", settings.asr_lang)
        }

        asr_sample_rate = data.get("sample_rate", settings.asr_sample_rate)
        asr_stream_container["stream"] = await start_asr_stream(asr_sample_rate, asr_config)
        if not asr_stream_container["stream"]:
            logger.error(f"Failed to start ASR stream for {client_id}")
            await ws_manager.disconnect(client_id)
            return

        # Initialize TTS stream with config defaults, allow session override
        tts_config = {
            "threads": settings.tts_threads,
            "models_root": settings.models_root,
            "tts_provider": settings.tts_provider,
            "tts_model": data.get("tts_model", settings.tts_model),
            "tts_speaker": data.get("tts_speaker", settings.tts_speaker),
            "split": data.get("split", settings.tts_split)
        }

        tts_sample_rate = data.get("sample_rate", settings.tts_sample_rate)
        tts_speed = data.get("speed", settings.tts_speed)
        tts_stream_container["stream"] = await start_tts_stream(
            tts_sample_rate,
            tts_speed,
            tts_config
        )
        if not tts_stream_container["stream"]:
            logger.error(f"Failed to start TTS stream for {client_id}")
            # Cleanup ASR stream if TTS fails
            if asr_stream_container["stream"] is not None:
                await asr_stream_container["stream"].close()
            await ws_manager.disconnect(client_id)
            return

        await ws_manager.send_text(
            client_id,
            json.dumps({
                "type": "session_started",
                "client_id": client_id,
                "mode": "voice_agent",
                "pipeline": "audio -> ASR -> LLM -> TTS -> audio",
                "llm_model": llm_config["model_name"]
            })
        )

        # Send initial state notification (LISTENING)
        await self.set_agent_state(client_id, AgentState.LISTENING)

    async def end_session(
        self,
        client_id: str,
        asr_stream_container: dict,
        tts_stream_container: dict
    ):
        """
        End a voice agent session.

        Closes both ASR and TTS streams and sends a session_ended confirmation to the client.

        Args:
            client_id: Unique identifier for the client
            asr_stream_container: Container holding the ASR stream to close
            tts_stream_container: Container holding the TTS stream to close
        """
        logger.info(f"Ending voice agent session for {client_id}")

        # Close ASR stream
        if asr_stream_container["stream"] is not None:
            await asr_stream_container["stream"].close()

        # Close TTS stream
        if tts_stream_container["stream"] is not None:
            await tts_stream_container["stream"].close()

        await ws_manager.send_text(
            client_id,
            json.dumps({
                "type": "session_ended"
            })
        )


# Global handler instance
speak_ws_handler = SpeakWebSocketHandler()
