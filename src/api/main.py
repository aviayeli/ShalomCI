from fastapi import FastAPI

app = FastAPI(title="ShalomCI Mobile API", version="1.0.0")


@app.get("/")
async def root():
    return {"status": "ok", "message": "ShalomCI API is running"}
