from app.routers import restaurants
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(restaurants.router)
