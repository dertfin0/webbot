from fastapi import APIRouter
import time

from common import messages
from schemas import MessageSendBody, BotMessageHandleBody

router = APIRouter(
    prefix="/bot",
    tags=["Bot API"]
)

# TODO: Bot auth by token from .env

@router.post("/message", summary="Send new bot message")
async def send_message(body: MessageSendBody):
    return await messages.save_message(messages.Message(
        content=body.content,
        by_bot=True,
        handled=True,
        sent_at=int(time.time())
    ))

@router.get("/update", summary="Get not handled messages")
async def update():
    return await messages.get_not_handled_messages()

@router.patch("/handled", summary="Mark user message as handled")
async def mark_as_handled(body: BotMessageHandleBody):
    status = await messages.mark_as_handled(body.id)
    return { "status": status }