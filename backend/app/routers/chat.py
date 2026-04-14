"""
app/routers/chat.py — /chat endpoint.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.core.logging import get_logger
from app.schemas.responses import ChatRequest, ChatResponse
from app.services.chat_service import generate_clinical_response

router = APIRouter(prefix="/chat", tags=["Chat"])
log = get_logger(__name__)


@router.post("", response_model=ChatResponse, summary="AI clinical consultation")
async def chat(request_body: ChatRequest, request: Request) -> ChatResponse:
    """
    Generate a contextual clinical nutrition response based on patient data
    and conversation history.

    Phase 3 upgrade: Swap generate_clinical_response() with a streaming LLM call.
    """
    try:
        messages = [m.model_dump() for m in request_body.messages]
        text = generate_clinical_response(request_body.patient_data, messages)
        log.info("chat_response_generated", n_turns=len(messages))
        return ChatResponse(content=[{"text": text}])
    except Exception as exc:
        log.error("chat_error", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
