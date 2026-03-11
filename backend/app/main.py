from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.routers.search_router import router as search_router

app = FastAPI()


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


app.include_router(search_router)