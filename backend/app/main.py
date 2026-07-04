import logging
import time
from typing import Callable
from fastapi import FastAPI, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.api.routes import health, cases, accused, reports, chat

# Set up logging configuration with structured formatting
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("ksp-sentinel-backend")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="KSP Sentinel AI Investigation Operations Engine Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Error Handling Middleware
@app.middleware("http")
async def log_requests_and_handle_errors(request: Request, call_next: Callable) -> Response:
    """
    HTTP middleware executing request execution timing and capturing unhandled system errors
    to prevent container stack traces from being sent to API consumers.
    """
    start_time = time.time()
    logger.info(f"Method: {request.method} Path: {request.url.path} initiated.")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"Method: {request.method} Path: {request.url.path} finished "
            f"in {process_time:.4f}s with code: {response.status_code}"
        )
        return response
    except Exception as exc:
        process_time = time.time() - start_time
        logger.error(
            f"Unhandled error processing path: {request.url.path} "
            f"after {process_time:.4f}s. Detail: {str(exc)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred while processing the request.",
                "trace_reference": f"err-{int(time.time())}"
            }
        )


# API Override Handlers
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"HTTP exception at {request.url.path} status={exc.status_code} detail={exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error at {request.url.path} details={exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request payload validation failed.",
            "errors": jsonable_encoder(exc.errors())
        },
    )


# Include API routers under prefix /api/v1
api_prefix = settings.API_V1_STR
app.include_router(health.router, prefix=f"{api_prefix}/health", tags=["Health Ops"])
app.include_router(cases.router, prefix=f"{api_prefix}/cases", tags=["FIR Cases"])
app.include_router(accused.router, prefix=f"{api_prefix}/accused", tags=["Suspect Dossiers"])
app.include_router(reports.router, prefix=f"{api_prefix}/reports", tags=["Briefing Reports"])
app.include_router(chat.router, prefix=f"{api_prefix}/chat", tags=["AI Copilot Workspace"])

# Top-level Health endpoint (Requested as /health)
app.include_router(health.router, prefix="/health", tags=["Health Ops"])


@app.get("/")
def read_root():
    return {
        "message": "Welcome to KSP Sentinel AI API Portal",
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
