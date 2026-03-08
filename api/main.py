from fastapi import FastAPI
import uvicorn
import asyncio
import dotenv

import config
from common import database
from routers import user_api, bot_api

app = FastAPI()
VERSION = "0.1.0"

app.include_router(user_api.router)
app.include_router(bot_api.router)

@app.get("/version", summary="Get version of WebBot API")
async def version():
    return VERSION

if __name__ == "__main__":
    if not dotenv.load_dotenv(".env"):
        print(".env file not found")
        exit(-1)
    config.load()

    asyncio.run(database.init())
    uvicorn.run(app, host="0.0.0.0", port=8000)
