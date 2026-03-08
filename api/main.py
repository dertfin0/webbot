from fastapi import FastAPI
import uvicorn

app = FastAPI()
VERSION = "0.1.0"

@app.get("/version")
async def version():
    return version

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
