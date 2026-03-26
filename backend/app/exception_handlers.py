from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def request_validation_exception_handler(request, exc: RequestValidationError):
    del request
    return JSONResponse(
        status_code=422,
        content={
            "message": "Invalid request parameters.",
            "details": exc.errors(),
        },
    )
