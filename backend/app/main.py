from fastapi import FastAPI
from app.routers import auth
from app.routers.orders import router as orders_router

app = FastAPI(title="GitSOS Backend")


@app.get("/")
def read_root():
    return {"message": "GitSOS API is running!"}


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(orders_router)