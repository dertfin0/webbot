import dotenv
import hashlib

bot_token: str
bot_token_hash: str
user_password: str
user_password_hash: str

def load():
    global bot_token
    global bot_token_hash
    global user_password
    global user_password_hash

    bot_token = dotenv.get_key(".env", "BOT_TOKEN")
    bot_token_hash = hashlib.sha256(bot_token.encode("UTF-8")).hexdigest()

    user_password = dotenv.get_key(".env", "USER_PASSWORD")
    user_password_hash = hashlib.sha256(user_password.encode("UTF-8")).hexdigest()
