from pydantic import BaseModel, Field

class UserMessageSendBody(BaseModel):
    content: str = Field(max_length=2048)
