from fastapi import FastAPI
from routers.search_router import router as search_router

app = FastAPI(title="GitSOS Backend")

@app.get("/")
def read_root():
    return {"message": "GitSOS API is running!"}

app = FastAPI()
app.include_router(search_router)