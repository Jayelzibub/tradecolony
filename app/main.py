"""
main.py

Entry point for the FastAPI application.

- Loads environment variables
- Initializes the FastAPI app
- Registers all API routers
- Defines root "/" endpoint for basic health check
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI

from app.api import routes, protected, users

# --- Load environment variables ---
load_dotenv()

# --- Initialize FastAPI app ---
app = FastAPI(title=os.getenv("PROJECT_NAME", "TradeColony API"))

# --- Register routers ---
#app.include_router(protected.router)
#app.include_router(users.router)
app.include_router(routes.router)

# --- Root endpoint (health check) ---
@app.get("/")
def read_root():
    return {
        "message": f"Welcome to {os.getenv('PROJECT_NAME', 'TradeColony API')}",
        "environment": os.getenv("ENVIRONMENT", "development")
    }
