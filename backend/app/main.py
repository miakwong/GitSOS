from app.routers import auth, payments, restaurants
from app.routers.orders import router as orders_router
from app.routers.search_router import router as search_router
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI(title="GitSOS Backend")


@app.get("/")
def read_root():
    return {"message": "GitSOS API is running!"}


@app.get("/health")
def health():
    return {"status": "ok"}

@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    del request

    return JSONResponse(
        status_code=400,
        content={
            "message": "Invalid request parameters.",
            "details": exc.errors(),
        },
    )

# Include routers
app.include_router(orders_router)
app.include_router(payments.router)
app.include_router(auth.router)
app.include_router(restaurants.router)
app.include_router(search_router)
