from fastapi import APIRouter, Depends
from core.schemas import CurrentUser
from core.dependencies import require_role
from core.enums import Role
from modules.ai.schemas import ChatRequest, ChatResponse
from modules.ai.service import AiService

router = APIRouter()
ai_service = AiService()

@router.post("/chat", response_model=ChatResponse)
def chat_with_ai(
    request: ChatRequest,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    reply = ai_service.get_chat_response(request.message)
    return ChatResponse(reply=reply)
