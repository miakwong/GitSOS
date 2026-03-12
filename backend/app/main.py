
from fastapi import FastAPI
from app.routers import payments

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(payments.router)
