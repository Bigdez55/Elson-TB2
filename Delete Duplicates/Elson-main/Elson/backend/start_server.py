#!/usr/bin/env python
"""
Start the Elson Trading Bot API server.

This script starts the FastAPI application with Uvicorn server,
with proper configuration for production or development environments.
"""

import os
import sys
import argparse
import logging
import multiprocessing
import time
import uvicorn
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("server-starter")

def start_uvicorn(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    workers: int = 1,
    env_file: Optional[str] = None,
    log_level: str = "info"
):
    """Start Uvicorn server with the given configuration."""
    app_module = "app.main:app"
    
    # Set environment file if provided
    env_vars = {}
    if env_file:
        env_vars["ENV_FILE"] = env_file
    
    # Start Uvicorn server
    uvicorn.run(
        app_module,
        host=host,
        port=port,
        log_level=log_level,
        reload=reload,
        workers=workers,
        env_file=env_file
    )

def start_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    workers: Optional[int] = None,
    env_file: Optional[str] = None,
    daemonize: bool = False
):
    """Start the FastAPI server with Uvicorn."""
    # Set environment file if provided
    if env_file:
        if os.path.exists(env_file):
            logger.info(f"Loading environment from: {env_file}")
            os.environ["ENV_FILE"] = env_file
        else:
            logger.error(f"Environment file not found: {env_file}")
            sys.exit(1)
    
    # Import settings to determine environment
    try:
        from app.core.config import settings
        
        # Set worker count based on environment if not explicitly provided
        if workers is None:
            if settings.ENVIRONMENT == "production":
                workers = min(multiprocessing.cpu_count() * 2 + 1, 8)
            else:
                workers = 1
        
        # Configure Uvicorn settings based on environment
        log_level = "info"
        if settings.DEBUG:
            log_level = "debug"
            
        logger.info(f"Starting server on {host}:{port} with {workers} workers")
        logger.info(f"Environment: {settings.ENVIRONMENT}, Debug: {settings.DEBUG}")
    except ImportError:
        logger.warning("Could not import settings. Using default configuration.")
        workers = workers or 1
        log_level = "info"
        logger.info(f"Starting server on {host}:{port} with {workers} workers")
    
    if daemonize:
        # Start the server in a separate process
        server_process = multiprocessing.Process(
            target=start_uvicorn,
            kwargs={
                "host": host,
                "port": port,
                "reload": reload,
                "workers": workers,
                "env_file": env_file,
                "log_level": log_level
            }
        )
        server_process.daemon = True
        server_process.start()
        
        logger.info("Server starting in daemon mode...")
        time.sleep(2)  # Give the server a moment to start
        
        try:
            logger.info("Server is running. Press Ctrl+C to stop.")
            server_process.join()
        except KeyboardInterrupt:
            logger.info("Stopping server...")
            server_process.terminate()
            server_process.join()
            sys.exit(0)
    else:
        # Start the server directly
        start_uvicorn(
            host=host,
            port=port,
            reload=reload,
            workers=workers,
            env_file=env_file,
            log_level=log_level
        )

def find_env_file(env: str) -> Optional[str]:
    """Find the environment file based on environment name."""
    # Look for config in several locations
    config_paths = [
        # Project root config
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../config")),
        # Config relative to this file
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../config")),
        # Current directory config
        os.path.abspath(os.path.join(os.path.dirname(__file__), "config")),
        # Root directory
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ]
    
    for config_path in config_paths:
        env_file = os.path.join(config_path, f"{env}.env")
        if os.path.exists(env_file):
            return env_file
    
    # Not found
    return None

def main():
    """Parse command line arguments and start server."""
    parser = argparse.ArgumentParser(description="Start Elson Wealth Trading Platform API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind server to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (development only)")
    parser.add_argument("--workers", type=int, help="Number of worker processes")
    parser.add_argument("--env-file", help="Path to .env file to load")
    parser.add_argument("--env", default="development", 
                        choices=["development", "testing", "staging", "production"],
                        help="Environment to run in (development, testing, staging, production)")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode")
    
    args = parser.parse_args()
    
    # If env-file not provided, try to find it based on environment
    if not args.env_file:
        env_file = find_env_file(args.env)
        if env_file:
            args.env_file = env_file
            logger.info(f"Using environment file: {env_file}")
        else:
            # Set environment variable directly if no file found
            os.environ["ENVIRONMENT"] = args.env
            logger.info(f"Setting ENVIRONMENT={args.env} (no environment file found)")
    
    # Safety check for production with auto-reload
    if args.env == "production" and args.reload:
        logger.warning("Auto-reload is not recommended in production. Disabling.")
        args.reload = False
    
    # Start server
    start_server(
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        env_file=args.env_file,
        daemonize=args.daemon
    )

if __name__ == "__main__":
    main()