from app.routers import restaurants
from fastapi import FastAPI

from app.routers.orders import router as orders_router

app = FastAPI(title="GitSOS Backend")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(restaurants.router)
@app.get("/")
def read_root():
    return {"message": "GitSOS API is running!"}

# Include routers
app.include_router(orders_router)
