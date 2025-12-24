from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum
from typing import Dict
from .routers import upload, training, models, datasets, predict
from .utils.helpers import get_settings

settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="AWS AutoML Lite API",
    description="Lightweight AutoML platform on AWS",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(datasets.router)
app.include_router(training.router)
app.include_router(models.router)
app.include_router(predict.router)


@app.get("/")
async def root() -> Dict[str, str]:
    """Health check endpoint"""
    return {
        "message": "AWS AutoML Lite API",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "automl-api",
        "region": settings.aws_region
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "detail": str(exc)
        }
    )


# Lambda handler
handler = Mangum(app, lifespan="off")
