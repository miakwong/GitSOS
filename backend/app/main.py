from fastapi import FastAPI
<<<<<<< HEAD
from app.routers import auth

app = FastAPI(title="GitSOS Backend")

@app.get("/")
def read_root():
    return {"message": "GitSOS API is running!"}
=======

from app.routers.orders import router as orders_router

app = FastAPI(title="GitSOS Backend")
>>>>>>> 8f85023a091f4302d496481aa786772173e35887

@app.get("/health")
def health():
    return {"status": "ok"}

<<<<<<< HEAD
app.include_router(auth.router)
=======
@app.get("/")
def read_root():
    return {"message": "GitSOS API is running!"}

# Include routers
app.include_router(orders_router)
>>>>>>> 8f85023a091f4302d496481aa786772173e35887
