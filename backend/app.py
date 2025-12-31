"""
RAG Chatbot API Application
FastAPI application for AI-powered chatbot with RAG capabilities
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import chatbot
from .config.config import APP_NAME, APP_VERSION

# Initialize FastAPI application
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="AI-powered chatbot with Retrieval-Augmented Generation (RAG) using Gemini AI and Pinecone",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - configure based on your frontend requirements
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include chatbot router
app.include_router(
    chatbot.router, 
    prefix="/api/v1/chatbot", 
    tags=["chatbot"]
)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "description": "RAG Chatbot API with Gemini AI and Pinecone",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["monitoring"])
async def health_check():
    """Health check endpoint for monitoring and CI/CD.
    
    Returns:
        dict: Service status information
    """
    return {
        "service": APP_NAME,
        "status": "running",
        "version": APP_VERSION
    }


@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    print(f"{APP_NAME} v{APP_VERSION} starting up...")
    print("RAG Chatbot API is ready to serve requests")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    try:
        print(f"{APP_NAME} shutting down...")
    except Exception:
        pass