from pydantic import BaseModel, Field

class MessageSendBody(BaseModel):
    content: str = Field(max_length=2048)

class BotMessageHandleBody(BaseModel):
    id: int