#!/usr/bin/env python3
"""
Initialize the database schema and create initial data.

This script sets up the database schema and can optionally populate
initial data for the Elson Wealth application.

Usage:
    python init_db.py [--env ENVIRONMENT] [--seed]

Options:
    --env ENVIRONMENT   Specify the environment (development, testing, production)
    --seed              Seed the database with initial data
"""

import sys
import os
import argparse
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("init-db")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Initialize the database")
    parser.add_argument("--env", help="Environment (development, testing, production)", 
                        default="development")
    parser.add_argument("--seed", help="Seed the database with initial data",
                        action="store_true")
    return parser.parse_args()

def main():
    """Main function to initialize the database."""
    args = parse_args()
    
    # Set environment variable to control which config is loaded
    os.environ["ENVIRONMENT"] = args.env
    logger.info(f"Initializing database for environment: {args.env}")
    
    # Import after setting environment to ensure config loads correctly
    from app.db.database import init_db, get_db_context
    
    # Initialize database schema
    try:
        # First initialize the database schema
        init_db()
        logger.info("Database schema initialized successfully")
        
        # Now open a database session for additional initializations
        with get_db_context() as db:
            # Verify database connection works
            from app.db.init_db import verify_db
            if not verify_db(db):
                logger.error("Database verification failed")
                sys.exit(1)
            
            # Initialize database with required data
            from app.db.init_db import init_db as init_db_data
            init_db_data(db)
            logger.info("Database initialized with required data")
        
            # Seed data if requested
            if args.seed:
                logger.info("Seeding database with initial data...")
                try:
                    from app.db.init_db import initialize_seed_data
                    initialize_seed_data()
                    logger.info("Database seeded successfully")
                except ImportError:
                    logger.warning("Seed function not available - skipping data seeding")
            
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        sys.exit(1)
        
    logger.info("Database initialization complete")

if __name__ == "__main__":
    main()