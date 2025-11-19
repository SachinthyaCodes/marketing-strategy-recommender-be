# app/main.py
"""
Marketing Strategy Recommender Backend
FastAPI application with Profile Builder Agent
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.api.profile import router as profile_router
from app.utils.llm import validate_llm_configuration, get_model_info

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Marketing Strategy Recommender - Profile Builder Agent",
    description="""
    AI-powered Profile Builder Agent for Sri Lankan SMEs.
    
    This API helps Small and Medium Enterprises (SMEs) create comprehensive business profiles 
    from simple, unstructured input. Perfect for businesses that want to:
    
    - 📝 Describe their business in any format (English, Sinhala, or mixed)
    - 🎯 Get structured business profiles for marketing planning
    - 🚀 Build the foundation for AI-powered marketing strategies
    
    **Key Features:**
    - Mixed language support (Sinhala + English) 
    - Intelligent data extraction and normalization
    - Sri Lankan business context awareness
    - Automatic gap filling with smart assumptions
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(profile_router, prefix="/api")

@app.get("/")
async def root():
    """
    Root endpoint with API information and health status
    """
    llm_config = validate_llm_configuration()
    
    return {
        "message": "🚀 Marketing Strategy Recommender - Profile Builder Agent",
        "version": "1.0.0",
        "status": "healthy",
        "features": [
            "Mixed language support (Sinhala + English)",
            "Intelligent business profile extraction", 
            "Sri Lankan SME context awareness",
            "Automatic data gap filling"
        ],
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "build_profile": "/api/profile/build",
            "analyze_input": "/api/profile/analyze"
        },
        "llm_status": {
            "configured": llm_config["is_valid"],
            "model_type": llm_config["model_type"],
            "ready": llm_config["is_valid"]
        }
    }

@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    """
    try:
        # Check LLM configuration
        llm_config = validate_llm_configuration()
        model_info = get_model_info()
        
        health_status = {
            "status": "healthy" if llm_config["is_valid"] else "degraded",
            "service": "profile-builder-agent",
            "version": "1.0.0",
            "timestamp": os.popen("date").read().strip(),
            "components": {
                "api": "healthy",
                "llm": "healthy" if llm_config["is_valid"] else "error",
                "database": "memory"  # Using in-memory storage for demo
            },
            "llm_configuration": model_info,
            "capabilities": [
                "Business profile extraction",
                "Sinhala-English mixed input processing",
                "Sri Lankan market context",
                "Intelligent assumptions"
            ]
        }
        
        if not llm_config["is_valid"]:
            health_status["warnings"] = [
                f"LLM configuration issue: {llm_config['error']}"
            ]
            health_status["recommendations"] = llm_config["recommendations"]
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "service": "profile-builder-agent", 
            "error": str(e)
        }

@app.get("/config")
async def get_configuration():
    """
    Get current system configuration (for development)
    """
    try:
        return {
            "llm_config": validate_llm_configuration(),
            "model_info": get_model_info(),
            "environment": {
                "cors_origins": allowed_origins,
                "debug_mode": os.getenv("DEBUG", "False").lower() == "true"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {e}")

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "status_code": exc.status_code,
            "type": "http_error"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "status_code": 500,
            "type": "server_error"
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    logger.info(f"Starting Profile Builder Agent on {host}:{port}")
    logger.info(f"LLM Configuration: {get_model_info()}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )