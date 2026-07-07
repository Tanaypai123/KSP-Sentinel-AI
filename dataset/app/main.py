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
from app.api.routes import health, cases, accused, reports, chat, analytics

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

from app.core.metrics import global_metrics
from app.core.rate_limit import RateLimitMiddleware

# CORS Configuration
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Sliding Window Rate Limiting Middleware (Kept disabled by default)
app.add_middleware(RateLimitMiddleware, enabled=False, rate_limit=100, window_seconds=60)


# Error Handling Middleware
@app.middleware("http")
async def log_requests_and_handle_errors(request: Request, call_next: Callable) -> Response:
    """
    HTTP middleware executing request execution timing, capturing unhandled system errors,
    and recording diagnostics metrics.
    """
    start_time = time.time()
    logger.info(f"Method: {request.method} Path: {request.url.path} initiated.")
    
    # Initialize state variables to prevent hasattr crashes
    request.state.cache_hit = False
    request.state.intent = ""
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        latency_ms = process_time * 1000
        
        is_hit = getattr(request.state, "cache_hit", False)
        intent = getattr(request.state, "intent", "")
        global_metrics.record_request(latency_ms, is_hit=is_hit, is_error=False, intent=intent)
        
        logger.info(
            f"Method: {request.method} Path: {request.url.path} finished "
            f"in {process_time:.4f}s with code: {response.status_code}"
        )
        return response
    except Exception as exc:
        process_time = time.time() - start_time
        latency_ms = process_time * 1000
        
        is_hit = getattr(request.state, "cache_hit", False)
        intent = getattr(request.state, "intent", "")
        global_metrics.record_request(latency_ms, is_hit=is_hit, is_error=True, intent=intent)
        
        logger.error(
            f"Unhandled error processing path: {request.url.path} "
            f"after {process_time:.4f}s. Detail: {str(exc)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Internal Server Error",
                "message": "An unhandled internal server error occurred.",
                "code": "INTERNAL_SERVER_ERROR",
                "timestamp": str(int(time.time()))
            }
        )


# API Override Handlers
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"HTTP exception at {request.url.path} status={exc.status_code} detail={exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": "HTTP Exception",
            "message": exc.detail,
            "code": f"HTTP_{exc.status_code}",
            "timestamp": str(int(time.time()))
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error at {request.url.path} details={exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation Error",
            "message": "Request payload validation failed.",
            "code": "VALIDATION_ERROR",
            "timestamp": str(int(time.time())),
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
app.include_router(analytics.router, prefix=f"{api_prefix}/analytics", tags=["Global Analytics"])

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
