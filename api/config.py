import dotenv
import hashlib

bot_token: str
bot_token_hash: str
user_password: str
user_password_hash: str
port: int

def load():
    global bot_token
    global bot_token_hash
    global user_password
    global user_password_hash
    global port

    if not dotenv.load_dotenv(".env"):
        raise ValueError(".env file not found")

    bot_token = dotenv.get_key(".env", "BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN not set")
    bot_token_hash = hashlib.sha256(bot_token.encode("UTF-8")).hexdigest()

    user_password = dotenv.get_key(".env", "USER_PASSWORD")
    if not user_password:
        raise ValueError("USER_PASSWORD not set")
    user_password_hash = hashlib.sha256(user_password.encode("UTF-8")).hexdigest()

    port = dotenv.get_key(".env", "PORT")
    if not port:
        print("Using default port 8000")
        port = 8000