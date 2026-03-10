from fastapi import FastAPI
from app.routers.search_router import router as search_router

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(search_router)