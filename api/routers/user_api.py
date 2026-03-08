from fastapi import APIRouter, HTTPException
from fastapi.params import Header, Depends
import time
from typing import Optional

import config
from common import messages
from schemas import MessageSendBody

def auth_check(authorization: Optional[str] = Header(None, alias="authorization")):
    print(authorization)
    print(config.bot_token)
    if not authorization or authorization != config.user_password_hash:
        raise HTTPException(status_code=403, detail="Invalid token")

router = APIRouter(
    prefix="/user",
    tags=["User API"],
    dependencies=[Depends(auth_check)]
)

# TODO: User auth by password from .env

@router.post("/message", summary="Send new message")
async def send_message(body: MessageSendBody):
    return await messages.save_message(messages.Message(
        content=body.content,
        by_bot=False,
        handled=False,
        sent_at=int(time.time())
    ))

@router.get("/messages", summary="Get new messages by last received message id")
async def get_messages(last_received_id: int):
    return await messages.get_messages_from_id(last_received_id)
