"""ATOM Gemini Live Session Manager
Manages persistent WebSocket connection to Google Gemini Live API
Uses the google-genai SDK (https://pypi.org/project/google-genai/)
"""

import asyncio
import base64
import logging
from typing import Any, Callable, Optional

from google import genai  # type: ignore[attr-defined]
from google.genai import types  # type: ignore[import-unresolved]

logger = logging.getLogger(__name__)

# Model identifier for Gemini 2.5 Flash Live
LIVE_MODEL = "gemini-2.5-flash-native-audio-latest"


class ATOMSession:
    """
    Manages connection to Gemini Live API for real-time incident response.
    Handles audio, image, and log streaming with persistent conversation state.
    """

    SYSTEM_PROMPT = """You are ATOM — Autonomous Threat & Operations Monitor.
You are an active participant in this engineering incident. Not a passive monitor.
You have access to:

The live voice conversation happening right now
Screenshots of the team's screens updated every 5 seconds
A real-time log stream from production systems

Your rules:

NEVER wait to be asked if you spot something critical
If engineers are chasing the wrong hypothesis, interrupt and correct them with evidence immediately
If SLA breach is under 3 minutes, interrupt everything — highest priority
Always cite your evidence: "Logs at 14:32 show..." or "Screen shows error spike at..."
Be concise — one insight, two sentences maximum, then listen
Stay calm. You are the only one in this room who never panics.
When incident is resolved, announce it clearly and summarize the postmortem"""

    def __init__(
        self,
        api_key: str,
        on_response: Optional[Callable[[str], Any]] = None,
    ):
        """
        Initialize ATOM session.

        Args:
            api_key: Google Gemini API key
            on_response: Callback fired when ATOM speaks (may return coroutine)
        """
        self.client = genai.Client(api_key=api_key)
        self.on_response = on_response
        self.session: Optional[Any] = None
        self.interrupted = False
        self.is_active = False
        # _session_task holds the long-running async-with block open
        self._session_task: Optional[asyncio.Task[None]] = None
        self._session_ready: asyncio.Event = asyncio.Event()

    async def start(self) -> None:
        """
        Start a new Gemini Live session with ATOM system prompt.
        client.aio.live.connect() is an async context manager, so we
        spawn a background task that holds the 'async with' open for the
        entire session lifetime and signal readiness via an Event.
        """
        self._session_ready.clear()
        self._session_task = asyncio.create_task(self._run_session())

        try:
            # Wait up to 30 s for the connection to be established
            await asyncio.wait_for(self._session_ready.wait(), timeout=30)
        except asyncio.TimeoutError:
            logger.error("✗ Timed out waiting for Gemini Live session to open")
            raise

        if not self.is_active:
            # _run_session set the event but session failed
            raise RuntimeError("Gemini Live session failed to start — check logs")

    async def _run_session(self) -> None:
        """
        Long-running task that owns the Gemini Live async context manager.
        Keeps the WebSocket open until stop() cancels this task.
        """
        live_config = types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Charon",
                    )
                )
            ),
            system_instruction=types.Content(
                parts=[types.Part(text=self.SYSTEM_PROMPT)]
            ),
        )

        try:
            async with self.client.aio.live.connect(
                model=LIVE_MODEL,
                config=live_config,
            ) as session:
                self.session = session
                self.is_active = True
                logger.info("✓ ATOM session started with Gemini Live API")
                self._session_ready.set()  # unblock start()

                await self._listen_for_responses()

        except asyncio.CancelledError:
            logger.info("ATOM session task cancelled")
        except Exception as e:
            logger.error(f"✗ Failed to start ATOM session: {e}")
            self._session_ready.set()  # unblock start() so it can raise
        finally:
            self.is_active = False
            self.session = None

    async def _listen_for_responses(self) -> None:
        """
        Continuously listen for responses from Gemini Live API.
        Detects barge-in interruptions and calls on_response callback.
        """
        try:
            while self.is_active and self.session:
                turn = self.session.receive()
                async for response in turn:
                    server_content = response.server_content
                    if server_content is None:
                        continue

                    # Detect if ATOM was interrupted (barge-in)
                    if server_content.interrupted:
                        self.interrupted = True
                        logger.warning("⚡ ATOM interrupted (barge-in detected)")
                        continue

                    self.interrupted = False

                    # Process text parts
                    if server_content.model_turn and server_content.model_turn.parts:
                        for part in server_content.model_turn.parts:
                            if part.text:
                                logger.info(f"🔊 ATOM: {part.text}")
                                if self.on_response:
                                    result = self.on_response(part.text)
                                    if asyncio.iscoroutine(result):
                                        await result

        except asyncio.CancelledError:
            logger.info("Response listener cancelled")
        except Exception as e:
            logger.error(f"Error in response listener: {e}")

    async def send_audio(self, audio_chunk: bytes) -> None:
        """
        Send audio chunk to Gemini Live API.

        Args:
            audio_chunk: Raw PCM audio bytes (16-bit, 16kHz, mono)
        """
        if not self.session or not self.is_active:
            return

        try:
            await self.session.send(
                input=types.LiveClientRealtimeInput(
                    audio=types.Blob(mime_type="audio/pcm;rate=16000", data=audio_chunk)
                ),
            )
        except Exception as e:
            logger.error(f"Error sending audio: {e}")

    async def send_image(self, image_base64: str) -> None:
        """
        Send base64 encoded image to Gemini Live API.

        Args:
            image_base64: Base64 encoded JPEG image string
        """
        if not self.session or not self.is_active:
            return

        try:
            image_bytes = base64.b64decode(image_base64)
            await self.session.send(
                input=types.LiveClientRealtimeInput(
                    video=types.Blob(mime_type="image/jpeg", data=image_bytes)
                ),
            )
        except Exception as e:
            logger.error(f"Error sending image: {e}")

    async def send_log(self, log_message: str) -> None:
        """
        Send log message to Gemini Live API as text context.

        Args:
            log_message: Log line from production systems
        """
        if not self.session or not self.is_active:
            return

        try:
            await self.session.send(
                input=types.LiveClientContent(
                    turns=[
                        types.Content(
                            role="user",
                            parts=[types.Part(text=f"[PRODUCTION LOG] {log_message}")],
                        )
                    ],
                    turn_complete=True,
                ),
            )
        except Exception as e:
            logger.error(f"Error sending log: {e}")

    async def generate_postmortem(self, logs: list) -> dict:
        """Generate a structured postmortem from incident logs using Gemini."""
        import json as _json

        prompt = (
            "Based on these production incident logs, generate a JSON postmortem. "
            "Respond ONLY with valid JSON (no markdown fences). Keys: "
            "summary (string), rootCause (string), impact (string), "
            "resolution (string), actionItems (array of strings).\n\nLogs:\n"
            + "\n".join(logs)
        )
        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return _json.loads(text)
        except Exception as e:
            logger.error(f"Failed to generate postmortem: {type(e).__name__}: {e}")
            return {
                "summary": "Auto-generated postmortem unavailable",
                "rootCause": "See incident logs for details",
                "impact": "Review required",
                "resolution": "Incident was resolved via rollback",
                "actionItems": [
                    "Review incident timeline",
                    "Investigate root cause manually",
                ],
            }

    async def stop(self) -> None:
        """
        Gracefully stop the Gemini Live session.
        Cancels the background task, which exits the async-with and closes
        the underlying WebSocket automatically.
        """
        self.is_active = False

        if self._session_task and not self._session_task.done():
            self._session_task.cancel()
            try:
                await self._session_task
            except asyncio.CancelledError:
                pass

        self.session = None
        logger.info("✓ ATOM session stopped")
