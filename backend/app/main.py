from app.routers import admin, auth, payments, restaurants
from app.routers.delivery import router as delivery_router
from app.routers.notifications import router as notifications_router
from app.routers.orders import router as orders_router
from app.routers.pricing_router import router as pricing_router
from app.routers.reviews import router as reviews_router
from app.routers.search_router import router as search_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="GitSOS Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
app.include_router(admin.router)
app.include_router(delivery_router)
app.include_router(pricing_router)
app.include_router(notifications_router)
app.include_router(reviews_router)
