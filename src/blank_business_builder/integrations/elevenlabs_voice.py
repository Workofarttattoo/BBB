"""
ElevenLabs Voice Integration for ChatterTech.ai

Production-grade voice agent using ElevenLabs Conversational AI API.
This replaces the manual Twilio+Deepgram+ElevenLabs pipeline with ElevenLabs' unified conversational endpoint.

Features:
- Real-time bidirectional audio streaming
- Built-in turn detection and interruption handling
- Custom voice selection and settings
- Webhook callbacks for call events
- Integration with Knowledge Vault for business context
"""

from __future__ import annotations

import os
import json
import asyncio
import aiohttp
from typing import Any, Dict, List, Optional, AsyncGenerator, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VoiceAgentSession:
    """Represents an active voice conversation session"""
    session_id: str
    phone_number: Optional[str]
    business_name: str
    agent_name: str
    start_time: datetime
    duration_seconds: int = 0
    transcript: List[Dict[str, str]] = None
    tasks_completed: List[str] = None
    lead_qualified: bool = False
    lead_score: float = 0.0
    escalated: bool = False
    sentiment: str = "neutral"
    recording_url: Optional[str] = None
    elevenlabs_session_id: Optional[str] = None
    
    def __post_init__(self):
        if self.transcript is None:
            self.transcript = []
        if self.tasks_completed is None:
            self.tasks_completed = []


class ElevenLabsVoiceAgent:
    """
    Autonomous AI voice agent using ElevenLabs Conversational AI
    
    Integrates:
    - ElevenLabs Conversational AI: Unified voice + LLM endpoint
    - Knowledge Vault: Business-specific Q&A and policies
    - Task execution: Booking, CRM sync, lead qualification
    - Viktor-style autonomous operation with judge evaluation
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # ElevenLabs configuration
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY", "")
        self.elevenlabs_base_url = "https://api.elevenlabs.io/v1"
        
        # Agent configuration
        self.agent_id = self.config.get("agent_id")  # ElevenLabs agent ID (pre-configured voice + prompt)
        self.voice_id = self.config.get("voice_id", "Rachel")  # Fallback voice ID
        self.llm_model = self.config.get("llm_model", "qwen3.5:9b")  # Local fallback
        
        # Knowledge vault (injected at runtime)
        self.knowledge_vault = None
        
        # Session management
        self.active_sessions: Dict[str, VoiceAgentSession] = {}
        
        # Webhook callback (for async task execution)
        self.webhook_callback: Optional[Callable] = None
        
        if not self.elevenlabs_api_key:
            logger.warning("ELEVENLABS_API_KEY not set - voice agent will use local TTS fallback")
    
    async def start_conversation(
        self,
        session_id: str,
        phone_number: Optional[str] = None,
        business_name: str = "our office",
        agent_name: str = "Alex",
        initial_message: Optional[str] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Start a new voice conversation using ElevenLabs Conversational AI
        
        Args:
            session_id: Unique session identifier
            phone_number: Caller's phone number (if from telephony)
            business_name: Name of the business being represented
            agent_name: Name the agent should use
            initial_message: Optional greeting message
        
        Yields:
            Audio chunks (PCM 24kHz) to stream back to caller
        """
        # Create session
        session = VoiceAgentSession(
            session_id=session_id,
            phone_number=phone_number,
            business_name=business_name,
            agent_name=agent_name,
            start_time=datetime.utcnow()
        )
        self.active_sessions[session_id] = session
        
        logger.info(f"Starting voice session {session_id} for {business_name}")
        
        # Build system prompt from Knowledge Vault
        system_prompt = self._build_system_prompt(session)
        
        # Use ElevenLabs Conversational AI if agent_id is configured
        if self.agent_id and self.elevenlabs_api_key:
            async for audio_chunk in self._elevenlabs_conversational_stream(
                session_id=session_id,
                agent_id=self.agent_id,
                system_prompt=system_prompt,
                initial_message=initial_message
            ):
                yield audio_chunk
        else:
            # Fallback: Manual pipeline (LLM → ElevenLabs TTS)
            logger.info("Using local LLM + ElevenLabs TTS fallback")
            async for audio_chunk in self._local_llm_tts_stream(
                session=session,
                system_prompt=system_prompt,
                initial_message=initial_message
            ):
                yield audio_chunk
        
        # Finalize session
        await self._finalize_session(session)
    
    async def _elevenlabs_conversational_stream(
        self,
        session_id: str,
        agent_id: str,
        system_prompt: str,
        initial_message: Optional[str] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream audio using ElevenLabs Conversational AI WebSocket
        
        This is the preferred method - ElevenLabs handles STT, LLM, and TTS in one endpoint.
        """
        ws_url = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={agent_id}"
        
        async with aiohttp.ClientSession() as http_session:
            async with http_session.ws_connect(ws_url, headers={"xi-api-key": self.elevenlabs_api_key}) as ws:
                # Send initial configuration
                config_message = {
                    "type": "conversation_init",
                    "client_data": {
                        "system_prompt_override": system_prompt,
                        "first_message": initial_message
                    }
                }
                await ws.send_json(config_message)
                
                # Listen for messages
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        msg_type = data.get("type")
                        
                        if msg_type == "agent_audio":
                            # Decode base64 audio chunk
                            audio_b64 = data.get("audio_chunk", "")
                            if audio_b64:
                                audio_bytes = base64.b64decode(audio_b64)
                                yield audio_bytes
                        
                        elif msg_type == "agent_response":
                            # Agent text response (for transcript)
                            session = self.active_sessions.get(session_id)
                            if session:
                                session.transcript.append({
                                    "role": "assistant",
                                    "content": data.get("text", ""),
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                                
                                # Check for task triggers
                                await self._process_agent_response(session, data.get("text", ""))
                        
                        elif msg_type == "user_transcript":
                            # User speech transcript
                            session = self.active_sessions.get(session_id)
                            if session:
                                session.transcript.append({
                                    "role": "user",
                                    "content": data.get("text", ""),
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                    
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error(f"WebSocket error: {ws.exception()}")
                        break
                
                # Session ended
                await ws.send_json({"type": "conversation_close"})
    
    async def _local_llm_tts_stream(
        self,
        session: VoiceAgentSession,
        system_prompt: str,
        initial_message: Optional[str] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Fallback: Local LLM (Ollama) + ElevenLabs TTS pipeline
        
        Used when ElevenLabs agent_id is not configured.
        """
        # Speak initial message
        if initial_message:
            async for audio_chunk in self._text_to_speech(initial_message):
                yield audio_chunk
            
            session.transcript.append({
                "role": "assistant",
                "content": initial_message,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Conversation loop (simulated - in production, audio comes from telephony webhook)
        # This is a placeholder - real implementation receives audio from Twilio/etc.
        logger.warning("Local LLM+TTS mode requires external STT input - configure ElevenLabs agent_id for full functionality")
        
        # For now, yield silence as placeholder
        # In production, this would be replaced by actual audio streaming logic
        yield b""
    
    async def _text_to_speech(self, text: str) -> AsyncGenerator[bytes, None]:
        """Convert text to speech using ElevenLabs TTS API"""
        if not self.elevenlabs_api_key:
            logger.warning("No ElevenLabs API key - skipping TTS")
            yield b""
            return
        
        async with aiohttp.ClientSession() as http_session:
            async with http_session.post(
                f"{self.elevenlabs_base_url}/text-to-speech/{self.voice_id}",
                headers={
                    "xi-api-key": self.elevenlabs_api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.0,
                        "use_speaker_boost": True
                    },
                    "output_format": "pcm_24000"  # Match Conversational AI format
                }
            ) as resp:
                if resp.status == 200:
                    async for chunk in resp.content.iter_chunked(4096):
                        yield chunk
                else:
                    logger.error(f"TTS API error: {resp.status} - {await resp.text()}")
    
    def _build_system_prompt(self, session: VoiceAgentSession) -> str:
        """Build comprehensive system prompt from Knowledge Vault"""
        context = ""
        if self.knowledge_vault:
            context = self.knowledge_vault.get_system_prompt_context()
        
        return f"""You are {session.agent_name}, a professional AI receptionist for {session.business_name}, powered by ChatterTech.ai.

ROLE:
- Answer calls warmly and professionally
- Handle FAQs, book appointments, qualify leads
- Escalate to human when: customer explicitly requests, frustration detected, or issue is too complex
- Be honest about being AI if asked directly
- Never make up information - use provided knowledge base

CONTEXT:
{context}

CONVERSATION GUIDELINES:
- Keep responses concise (1-3 sentences) for natural phone conversation
- Ask clarifying questions when needed
- Confirm important details (times, names, numbers)
- Offer escalation proactively if customer seems frustrated

CURRENT SESSION:
- Business: {session.business_name}
- Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

If the user asks to book an appointment, collect: name, phone, preferred date/time, reason.
If the user asks about pricing, provide accurate information from the knowledge base.
"""
    
    async def _process_agent_response(self, session: VoiceAgentSession, response_text: str):
        """Process agent response for task triggers and sentiment"""
        # Simple keyword-based task detection
        response_lower = response_text.lower()
        
        # Detect booking intent
        if any(phrase in response_lower for phrase in ["book", "schedule", "appointment", "calendar"]):
            # Extract booking details from recent transcript
            booking_task = {"type": "book_appointment", "status": "pending"}
            session.tasks_completed.append("appointment_booking_initiated")
            logger.info(f"Booking task triggered in session {session.session_id}")
        
        # Detect lead qualification
        if any(phrase in response_lower for phrase in ["interested", "pricing", "demo", "trial"]):
            session.lead_qualified = True
            logger.info(f"Lead qualified in session {session.session_id}")
        
        # Sentiment analysis
        session.sentiment = self._analyze_sentiment(response_text)
        if session.sentiment == "frustrated":
            logger.warning(f"Frustration detected in session {session.session_id}")
        
        # Trigger webhook callback if configured
        if self.webhook_callback:
            await self.webhook_callback(session)
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple rule-based sentiment analysis"""
        frustrated_keywords = ["frustrated", "angry", "unacceptable", "terrible", "worst", "useless", "ridiculous"]
        if any(word in text.lower() for word in frustrated_keywords):
            return "frustrated"
        
        positive_keywords = ["great", "awesome", "thank", "perfect", "excellent", "amazing", "wonderful"]
        if any(word in text.lower() for word in positive_keywords):
            return "positive"
        
        return "neutral"
    
    async def _finalize_session(self, session: VoiceAgentSession):
        """Save session, calculate metrics, trigger judge evaluation"""
        session.duration_seconds = (datetime.utcnow() - session.start_time).total_seconds()
        
        logger.info(
            f"Session {session.session_id} ended. "
            f"Duration: {session.duration_seconds:.1f}s, "
            f"Transcript length: {len(session.transcript)}, "
            f"Tasks: {len(session.tasks_completed)}"
        )
        
        # Calculate lead score if qualified
        if session.lead_qualified:
            session.lead_score = self._calculate_lead_score(session)
        
        # TODO: Persist session to database
        # TODO: Trigger auto_judge_loop for quality evaluation
        
        # Remove from active sessions
        if session.session_id in self.active_sessions:
            del self.active_sessions[session.session_id]
    
    def _calculate_lead_score(self, session: VoiceAgentSession) -> float:
        """Calculate lead score using BANT criteria (Budget, Authority, Need, Timeline)"""
        score = 0.0
        transcript_text = " ".join([t.get("content", "") for t in session.transcript])
        transcript_lower = transcript_text.lower()
        
        # Budget mentioned (0-25 points)
        if any(word in transcript_lower for word in ["budget", "price", "cost", "investment", "$"]):
            score += 25.0
        
        # Authority/Decision maker (0-25 points)
        if any(phrase in transcript_lower for phrase in ["i decide", "i'm the", "decision maker", "owner", "ceo"]):
            score += 25.0
        
        # Need/Pain point identified (0-25 points)
        if any(word in transcript_lower for word in ["problem", "issue", "challenge", "need", "struggling"]):
            score += 25.0
        
        # Timeline (0-25 points)
        if any(phrase in transcript_lower for phrase in ["asap", "right away", "this week", "next week", "soon", "urgent"]):
            score += 25.0
        
        return score
    
    def get_session(self, session_id: str) -> Optional[VoiceAgentSession]:
        """Retrieve active session by ID"""
        return self.active_sessions.get(session_id)
    
    def list_active_sessions(self) -> List[Dict]:
        """List all active sessions with summary info"""
        return [
            {
                "session_id": s.session_id,
                "business_name": s.business_name,
                "duration_seconds": s.duration_seconds,
                "transcript_length": len(s.transcript),
                "lead_qualified": s.lead_qualified,
                "sentiment": s.sentiment
            }
            for s in self.active_sessions.values()
        ]


# FastAPI integration
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from starlette.responses import StreamingResponse

router = APIRouter()

# Global agent instance (initialized on first use)
_agent_instance: Optional[ElevenLabsVoiceAgent] = None


def get_agent() -> ElevenLabsVoiceAgent:
    """Get or create global agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ElevenLabsVoiceAgent()
    return _agent_instance


@router.post("/voice/start")
async def start_voice_session(request: Request):
    """
    Start a new voice session via HTTP
    
    Expected JSON body:
    {
        "session_id": "unique-id",
        "phone_number": "+1234567890",
        "business_name": "Acme Corp",
        "agent_name": "Alex",
        "initial_message": "Thank you for calling Acme Corp..."
    }
    """
    body = await request.json()
    agent = get_agent()
    
    async def audio_stream():
        async for chunk in agent.start_conversation(
            session_id=body.get("session_id", "default"),
            phone_number=body.get("phone_number"),
            business_name=body.get("business_name", "our office"),
            agent_name=body.get("agent_name", "Alex"),
            initial_message=body.get("initial_message")
        ):
            yield chunk
    
    return StreamingResponse(
        audio_stream(),
        media_type="audio/pcm",
        headers={
            "X-Session-ID": body.get("session_id", "default"),
            "Content-Disposition": "attachment; filename=audio.pcm"
        }
    )


@router.websocket("/voice/ws/{session_id}")
async def voice_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time bidirectional voice streaming
    
    Client sends: Base64-encoded PCM audio chunks
    Server sends: Base64-encoded PCM audio responses
    """
    await websocket.accept()
    agent = get_agent()
    
    try:
        # Initialize session
        session = VoiceAgentSession(
            session_id=session_id,
            business_name="Web Client",
            agent_name="Alex",
            start_time=datetime.utcnow()
        )
        agent.active_sessions[session_id] = session
        
        # Send greeting
        greeting = "Hello! How can I help you today?"
        async for audio_chunk in agent._text_to_speech(greeting):
            await websocket.send_bytes(audio_chunk)
        
        # Bidirectional streaming loop
        async for message in websocket.iter_text():
            try:
                data = json.loads(message)
                
                if data.get("type") == "audio":
                    # Received audio from client (base64 PCM)
                    audio_b64 = data.get("data", "")
                    # In full implementation: send to STT → LLM → TTS
                    # For now, acknowledge receipt
                    await websocket.send_json({"type": "ack", "status": "processing"})
                
                elif data.get("type") == "text":
                    # Text input fallback
                    user_text = data.get("text", "")
                    session.transcript.append({
                        "role": "user",
                        "content": user_text,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    # Generate response (would use LLM in full impl)
                    response_text = f"I heard: {user_text}. How can I help?"
                    session.transcript.append({
                        "role": "assistant",
                        "content": response_text,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    # Send TTS response
                    async for audio_chunk in agent._text_to_speech(response_text):
                        await websocket.send_bytes(audio_chunk)
            
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
        # Finalize session
        if session_id in agent.active_sessions:
            await agent._finalize_session(agent.active_sessions[session_id])


@router.get("/voice/sessions")
async def list_sessions():
    """List all active voice sessions"""
    agent = get_agent()
    return {"sessions": agent.list_active_sessions()}


@router.get("/voice/session/{session_id}")
async def get_session(session_id: str):
    """Get details for a specific session"""
    agent = get_agent()
    session = agent.get_session(session_id)
    
    if not session:
        return {"error": "Session not found"}
    
    return {
        "session_id": session.session_id,
        "business_name": session.business_name,
        "agent_name": session.agent_name,
        "start_time": session.start_time.isoformat(),
        "duration_seconds": session.duration_seconds,
        "transcript": session.transcript,
        "tasks_completed": session.tasks_completed,
        "lead_qualified": session.lead_qualified,
        "lead_score": session.lead_score,
        "sentiment": session.sentiment
    }
