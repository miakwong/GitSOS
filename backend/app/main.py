from fastapi import FastAPI

from app.routers import auth

app = FastAPI(title="GitSOS Backend")

@app.get("/")
def read_root():
    return {"message": "GitSOS API is running!"}

app.include_router(auth.router)