
from fastapi import FastAPI

from app.routers import payments
from app.routers.orders import router as orders_router

app = FastAPI(title="GitSOS Backend")

@app.get("/")
def read_root():
    return {"message": "GitSOS API is running!"}

# Include routers
app.include_router(orders_router)
app.include_router(payments.router)
