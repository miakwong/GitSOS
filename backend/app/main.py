from app.routers import auth, payments, restaurants
from app.routers.delivery import router as delivery_router
from app.routers.notifications import router as notifications_router
from app.routers.orders import router as orders_router
from app.routers.search_router import router as search_router
from fastapi import FastAPI

app = FastAPI(title="GitSOS Backend")


@app.get("/")
def read_root():
    return {"message": "GitSOS API is running!"}


@app.get("/health")
def health():
    return {"status": "ok"}


# Include routers
app.include_router(orders_router)
app.include_router(payments.router)
app.include_router(auth.router)
app.include_router(restaurants.router)
app.include_router(search_router)
app.include_router(delivery_router)
app.include_router(notifications_router)
