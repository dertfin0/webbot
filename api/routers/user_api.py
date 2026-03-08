from fastapi import APIRouter
import time

from common import messages
from schemas import UserMessageSendBody

router = APIRouter(
    prefix="/user",
    tags=["User API"]
)

# TODO: User auth by password from .env

@router.post("/message", summary="Send new message")
async def send_message(body: UserMessageSendBody):
    return await messages.save_message(messages.Message(
        content=body.content,
        by_bot=False,
        handled=False,
        sent_at=int(time.time())
    ))

@router.get("/messages", summary="Get new messages by last received message id")
async def get_messages(last_received_id: int):
    return await messages.get_messages_from_id(last_received_id)
