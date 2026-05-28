"""
ChatterTech.ai Voice Agent Engine

Real-time AI phone agent using Twilio (telephony), Deepgram (STT), and ElevenLabs (TTS).
Handles inbound calls, FAQ answering, appointment booking, lead qualification, and human escalation.

Architecture:
1. Twilio webhook receives incoming call → streams audio to Deepgram
2. Deepgram transcribes speech → text sent to LLM (Ollama)
3. LLM generates response → text sent to ElevenLabs for TTS
4. ElevenLabs returns audio → streamed back to Twilio → played to caller
5. Task execution (booking, CRM sync) happens async during conversation

Viktor-style autonomous operation:
- Assume forward: Handle calls without asking permission
- Escalate only when: customer requests human, frustration detected, complex issue
- Memory: Conversation context persisted across call session
- Judge: Post-call quality scoring + revision if needed
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CallSession:
    """Represents an active phone call session"""
    call_id: str
    phone_number: str
    business_name: str
    start_time: datetime
    duration_seconds: int = 0
    transcript: List[Dict[str, str]] = None
    tasks_completed: List[str] = None
    lead_qualified: bool = False
    lead_score: float = 0.0
    escalated: bool = False
    sentiment: str = "neutral"
    recording_url: Optional[str] = None
    
    def __post_init__(self):
        if self.transcript is None:
            self.transcript = []
        if self.tasks_completed is None:
            self.tasks_completed = []


class ChatterTechVoiceAgent:
    """
    Autonomous AI voice agent for ChatterTech.ai
    
    Integrates:
    - Twilio: Phone numbers, call routing, recordings
    - Deepgram: Real-time speech-to-text
    - ElevenLabs: Natural text-to-speech
    - Ollama: LLM brain (qwen3.5:9b for reasoning)
    - Knowledge Vault: Business-specific Q&A
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # API endpoints
        self.deepgram_url = self.config.get("DEEPGRAM_URL", "https://api.deepgram.com/v1/listen")
        self.elevenlabs_url = self.config.get("ELEVENLABS_URL", "https://api.elevenlabs.io/v1/text-to-speech")
        self.ollama_url = self.config.get("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # API keys (from env)
        self.deepgram_key = os.getenv("DEEPGRAM_API_KEY")
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        self.twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        
        # Model config
        self.llm_model = self.config.get("LLM_MODEL", "qwen3.5:9b")
        self.voice_id = self.config.get("VOICE_ID", "Rachel")  # ElevenLabs voice
        
        # Session storage
        self.active_sessions: Dict[str, CallSession] = {}
        
        # Knowledge vault (injected at runtime)
        self.knowledge_vault = None
    
    async def handle_incoming_call(self, call_data: Dict) -> AsyncGenerator[str, None]:
        """
        Handle incoming Twilio webhook for new call
        
        Args:
            call_data: Twilio webhook payload (CallSid, From, To, etc.)
        
        Yields:
            Audio chunks to stream back to caller
        """
        call_sid = call_data.get("CallSid")
        from_number = call_data.get("From")
        to_number = call_data.get("To")
        
        # Create session
        session = CallSession(
            call_id=call_sid,
            phone_number=from_number,
            business_name=self._get_business_name(to_number),
            start_time=datetime.utcnow()
        )
        self.active_sessions[call_sid] = session
        
        logger.info(f"New call: {call_sid} from {from_number}")
        
        # Greeting (with recording disclaimer if required)
        greeting = self._build_greeting(session.business_name)
        async for audio_chunk in self._text_to_speech(greeting):
            yield audio_chunk
        
        # Add to transcript
        session.transcript.append({
            "role": "assistant",
            "content": greeting,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Main conversation loop
        async with aiohttp.ClientSession() as http_session:
            # Connect to Deepgram WebSocket for real-time STT
            async with http_session.ws_connect(
                f"{self.deepgram_url}?encoding=linear16&sample_rate=8000&interim_results=false",
                headers={"Authorization": f"Token {self.deepgram_key}"}
            ) as dg_ws:
                
                # Stream audio bidirectionally
                async def send_audio(audio_chunk):
                    await dg_ws.send_bytes(audio_chunk)
                
                async def receive_transcript():
                    async for msg in dg_ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            result = json.loads(msg.data)
                            if result.get("is_final"):
                                transcript = result["channel"]["alternatives"][0]["transcript"]
                                if transcript.strip():
                                    return transcript
                    return None
                
                # Conversation loop (max 30 minutes)
                max_duration = 1800  # seconds
                while session.duration_seconds < max_duration:
                    # Receive user speech
                    user_speech = await receive_transcript()
                    if not user_speech:
                        continue
                    
                    # Add to transcript
                    session.transcript.append({
                        "role": "user",
                        "content": user_speech,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    logger.info(f"User said: {user_speech}")
                    
                    # Generate response
                    response = await self._generate_response(session, user_speech)
                    
                    # Check for escalation
                    if response.get("escalate"):
                        await self._transfer_to_human(call_sid)
                        session.escalated = True
                        break
                    
                    # Speak response
                    assistant_response = response["content"]
                    async for audio_chunk in self._text_to_speech(assistant_response):
                        yield audio_chunk
                    
                    # Add to transcript
                    session.transcript.append({
                        "role": "assistant",
                        "content": assistant_response,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    # Execute tasks (booking, CRM sync)
                    if response.get("tasks"):
                        for task in response["tasks"]:
                            await self._execute_task(session, task)
                            session.tasks_completed.append(task["type"])
                    
                    # Update sentiment
                    session.sentiment = self._analyze_sentiment(user_speech)
                    if session.sentiment == "frustrated":
                        # Offer escalation
                        escalation_offer = "I apologize for any frustration. Would you like me to transfer you to a human?"
                        async for audio_chunk in self._text_to_speech(escalation_offer):
                            yield audio_chunk
                    
                    # Update duration
                    session.duration_seconds = (datetime.utcnow() - session.start_time).total_seconds()
        
        # Call ended - save session
        await self._finalize_session(session)
    
    async def _generate_response(self, session: CallSession, user_input: str) -> Dict:
        """
        Generate AI response using LLM + Knowledge Vault
        
        Returns dict with:
        - content: Response text
        - escalate: Boolean (transfer to human?)
        - tasks: List of tasks to execute
        """
        # Build context from knowledge vault
        context = ""
        if self.knowledge_vault:
            context = self.knowledge_vault.get_system_prompt_context()
        
        # Build prompt
        system_prompt = f"""You are a professional AI receptionist for {session.business_name}, powered by ChatterTech.ai.

ROLE:
- Answer calls warmly and professionally
- Handle FAQs, book appointments, qualify leads
- Escalate to human when: customer asks, frustration detected, complex issue
- Be honest about being AI if asked

CONTEXT:
{context}

CONVERSATION HISTORY:
{json.dumps(session.transcript[-6:], indent=2)}

USER SAID: {user_input}

Respond in JSON format:
{{
  "content": "Your spoken response",
  "escalate": false,
  "tasks": [{{"type": "book_appointment", "details": {{...}}}}],
  "lead_info": {{...}}  // If lead qualification happened
}}
"""
        
        # Call LLM
        async with aiohttp.ClientSession() as http_session:
            async with http_session.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": system_prompt,
                    "stream": False,
                    "format": "json"
                }
            ) as resp:
                result = await resp.json()
                response_text = result.get("response", "")
                
                try:
                    return json.loads(response_text)
                except:
                    # Fallback if JSON parsing fails
                    return {
                        "content": response_text,
                        "escalate": False,
                        "tasks": []
                    }
    
    async def _text_to_speech(self, text: str) -> AsyncGenerator[bytes, None]:
        """Convert text to speech using ElevenLabs"""
        async with aiohttp.ClientSession() as http_session:
            async with http_session.post(
                f"{self.elevenlabs_url}/{self.voice_id}",
                headers={
                    "xi-api-key": self.elevenlabs_key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                }
            ) as resp:
                async for chunk in resp.content.iter_chunked(4096):
                    yield chunk
    
    def _build_greeting(self, business_name: str) -> str:
        """Build professional greeting with recording disclaimer"""
        return (
            f"Thank you for calling {business_name}, this is Alex with ChatterTech AI. "
            f"This call may be recorded for quality assurance. How can I help you today?"
        )
    
    def _get_business_name(self, phone_number: str) -> str:
        """Lookup business name from phone number (inject from Knowledge Vault)"""
        # TODO: Query knowledge vault for business config
        return "our office"
    
    async def _execute_task(self, session: CallSession, task: Dict):
        """Execute task: booking, CRM sync, etc."""
        task_type = task.get("type")
        
        if task_type == "book_appointment":
            # Integrate with Calendly/Google Calendar
            logger.info(f"Booking appointment: {task.get('details')}")
            # TODO: Actual calendar integration
        
        elif task_type == "sync_crm":
            # Sync lead to HubSpot/Salesforce
            logger.info(f"Syncing to CRM: {task.get('details')}")
            # TODO: Actual CRM integration
    
    async def _transfer_to_human(self, call_sid: str):
        """Transfer call to human operator via Twilio"""
        # TODO: Twilio conference/transfer API
        logger.info(f"Transferring call {call_sid} to human")
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis (can use LLM or rule-based)"""
        frustrated_keywords = ["frustrated", "angry", "unacceptable", "terrible", "worst"]
        if any(word in text.lower() for word in frustrated_keywords):
            return "frustrated"
        
        positive_keywords = ["great", "awesome", "thank", "perfect", "excellent"]
        if any(word in text.lower() for word in positive_keywords):
            return "positive"
        
        return "neutral"
    
    async def _finalize_session(self, session: CallSession):
        """Save call session, trigger judge evaluation"""
        logger.info(f"Call {session.call_id} ended. Duration: {session.duration_seconds}s")
        
        # Calculate lead score
        if session.lead_qualified:
            session.lead_score = self._calculate_lead_score(session)
        
        # Save to database
        # TODO: Persist session
        
        # Trigger judge evaluation (async)
        # TODO: Send to auto_judge_loop for quality scoring
        
        # Remove from active sessions
        del self.active_sessions[session.call_id]
    
    def _calculate_lead_score(self, session: CallSession) -> float:
        """Calculate lead score based on BANT criteria"""
        score = 0.0
        
        # Budget mentioned?
        # Authority (decision maker)?
        # Need (pain point identified)?
        # Timeline (when they want service)?
        
        # TODO: Implement BANT scoring
        return score


# FastAPI webhook endpoint for Twilio
from fastapi import APIRouter, Request, Response

router = APIRouter()

agent_instance = None

@router.post("/twilio/webhook")
async def twilio_webhook(request: Request):
    """Twilio incoming call webhook"""
    global agent_instance
    
    form_data = await request.form()
    call_data = dict(form_data)
    
    if agent_instance is None:
        agent_instance = ChatterTechVoiceAgent()
    
    # Stream audio back to Twilio
    from starlette.responses import StreamingResponse
    
    async def audio_stream():
        async for chunk in agent_instance.handle_incoming_call(call_data):
            yield chunk
    
    return StreamingResponse(
        audio_stream(),
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=audio.wav"}
    )
