"""
app/routers/chat.py — /chat endpoint.
"""
from __future__ import annotations

from app.api.deps import get_current_user
from app.models.user import User
from fastapi import APIRouter, HTTPException, Request, Depends

router = APIRouter(prefix="/chat", tags=["Chat"])
log = get_logger(__name__)


@router.post("", response_model=ChatResponse, summary="AI clinical consultation")
async def chat(
    request_body: ChatRequest, 
    request: Request,
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    Generate a contextual clinical nutrition response based on patient data
    and conversation history.

    Phase 3 upgrade: Swap generate_clinical_response() with a streaming LLM call.
    """
    try:
        messages = [m.model_dump() for m in request_body.messages]
        text = await generate_clinical_response(
            request_body.patient_data, 
            messages, 
            user_id=str(current_user.id) if current_user else None
        )
        log.info("chat_response_generated", user_id=str(current_user.id) if current_user else None)
        return ChatResponse(content=[{"text": text}])
    except Exception as exc:
        log.error("chat_error", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
