from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.application.use_cases.chat.chat_with_llm import ChatModelUnavailable, ChatWithLLM
from app.domain.entities.user import User
from app.infrastructure.database.chat_repo_impl import ChatRepositorySQL
from app.infrastructure.database.chat_session_repo_impl import ChatSessionRepositorySQL
from app.infrastructure.dependencies import get_chat_repo, get_chat_session_repo, get_chat_use_case
from app.infrastructure.security.auth_jwt import get_current_user
from app.infrastructure.security.authz import require_permissions
from app.presentation.schemas.chat import ChatIn, ChatMessageOut, ChatOut, ChatSessionOut

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/send", response_model=ChatOut, dependencies=[Depends(require_permissions(["chat:use"]))])
async def send_message(
    body: ChatIn,
    current_user: User = Depends(get_current_user),
    use_case: ChatWithLLM = Depends(get_chat_use_case),
    chat_session_repo: ChatSessionRepositorySQL = Depends(get_chat_session_repo),
):
    effective_chat_id = chat_session_repo.get_or_create_default(current_user.id).id

    try:
        answer = await use_case.execute_async(
            user_id=current_user.id,
            user_message=body.message,
            chat_id=effective_chat_id,
            user_profile=current_user,
        )
    except ChatModelUnavailable:
        raise HTTPException(status_code=503, detail="CHAT_MODEL_UNAVAILABLE")
    return ChatOut(answer=answer, chat_id=effective_chat_id)


@router.get(
    "/history", response_model=List[ChatMessageOut], dependencies=[Depends(require_permissions(["chat:history_read"]))]
)
def get_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    repo: ChatRepositorySQL = Depends(get_chat_repo),
    chat_session_repo: ChatSessionRepositorySQL = Depends(get_chat_session_repo),
):
    effective_chat_id = chat_session_repo.get_or_create_default(current_user.id).id

    messages = repo.get_last_messages(user_id=current_user.id, limit=limit, chat_id=effective_chat_id)
    return [ChatMessageOut(id=m.id, role=m.role, content=m.content, created_at=m.timestamp) for m in messages]


@router.delete("/history", dependencies=[Depends(require_permissions(["chat:use"]))])
def clear_history(
    current_user: User = Depends(get_current_user),
    repo: ChatRepositorySQL = Depends(get_chat_repo),
    chat_session_repo: ChatSessionRepositorySQL = Depends(get_chat_session_repo),
):
    effective_chat_id = chat_session_repo.get_or_create_default(current_user.id).id
    deleted = repo.clear_messages(user_id=current_user.id, chat_id=effective_chat_id)
    return {"ok": True, "deleted": deleted}


@router.get("", response_model=List[ChatSessionOut], dependencies=[Depends(require_permissions(["chat:use"]))])
def list_chats(
    current_user: User = Depends(get_current_user),
    chat_repo: ChatSessionRepositorySQL = Depends(get_chat_session_repo),
):
    default = chat_repo.get_or_create_default(current_user.id)
    return [ChatSessionOut(id=default.id, title=default.title, topic=default.topic, is_default=True)]
