from fastapi import APIRouter

import config

router = APIRouter(
    prefix="/auth",
    tags=["Auth API"]
)

@router.get("/validate-token")
def validate_token(token_hash: str):
    return { "valid" : token_hash == config.bot_token_hash }

@router.get("/validate-user-password")
def validate_token(password_hash: str):
    return { "valid" : password_hash == config.user_password_hash }
