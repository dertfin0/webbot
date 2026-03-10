from fastapi import FastAPI
import uvicorn
import asyncio

import config
from common import database
from routers import user_api, bot_api, auth_api

app = FastAPI()
VERSION = "0.1.1"

app.include_router(user_api.router)
app.include_router(bot_api.router)
app.include_router(auth_api.router)

@app.get("/version", summary="Get version of WebBot API")
async def version():
    return VERSION

if __name__ == "__main__":
    try:
        config.load()
    except ValueError as e:
        print(e)
        exit(-1)

    asyncio.run(database.init())
    uvicorn.run(app, host="0.0.0.0", port=config.port)
