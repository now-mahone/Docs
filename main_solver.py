#!/usr/bin/env python3
"""
Kerne CoW Swap Solver - Render Entry Point
Production-ready FastAPI server for CoW Protocol solver competition.
"""

import os
import sys
import json
import logging

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add bot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))

# Set environment variables from Render
PORT = int(os.environ.get('PORT', 8080))
HOST = os.environ.get('HOST', '0.0.0.0')

def create_app():
    """Create and configure the FastAPI application."""
    try:
        # Import the solver API module
        from solver.cowswap_solver_api import app, solver
        
        logger.info(f"Solver API loaded successfully")
        logger.info(f"Solver name: {solver.__class__.__name__}")
        
        # Add exception handler for all unhandled exceptions
        from fastapi import Request
        from fastapi.responses import JSONResponse
        
        @app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            logger.error(f"Global exception handler caught: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "detail": str(exc),
                    "solutions": []  # Always return valid SolveResponse structure
                }
            )
        
        return app
        
    except Exception as e:
        logger.error(f"Failed to create app: {e}", exc_info=True)
        raise

def main():
    """Run the solver server."""
    import uvicorn
    
    logger.info("Starting Kerne CoW Swap Solver...")
    
    # Create the app
    app = create_app()
    
    # Configure uvicorn logging
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Run the server
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_config=log_config,
        access_log=True,
        proxy_headers=True,
        forwarded_allow_ips='*'
    )

if __name__ == "__main__":
    main()