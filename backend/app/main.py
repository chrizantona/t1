"""
VibeCode Backend - AI Interview Platform
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import settings
from app.core.db import init_db
from app.api import interview, admin, resume, anti_cheat, questions, claude, vacancy

# Create FastAPI app
app = FastAPI(
    title="VibeCode API",
    description="AI-powered technical interview platform using SciBox LLM",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    print("✅ Database initialized")
    print(f"✅ SciBox API configured: {settings.SCIBOX_BASE_URL}")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "VibeCode Backend",
        "version": "1.0.0"
    }


# API routes
app.include_router(interview.router, prefix="/api/interview", tags=["Interview"])
app.include_router(vacancy.router, prefix="/api/vacancy", tags=["Vacancy"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(resume.router, prefix="/api/resume", tags=["Resume"])
app.include_router(anti_cheat.router, prefix="/api/anti-cheat", tags=["Anti-Cheat"])
app.include_router(questions.router, prefix="/api/questions", tags=["Questions"])
app.include_router(claude.router, prefix="/api/claude", tags=["Claude LLM"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "VibeCode API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True
    )

