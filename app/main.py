import os
from fastapi import FastAPI
from dotenv import load_dotenv
from app.api import routes

load_dotenv()  # Load values from .env into environment

app = FastAPI(title=os.getenv("PROJECT_NAME"))

app.include_router(routes.router)

@app.get("/")
def read_root():
    return {
        "message": f"Welcome to {os.getenv('PROJECT_NAME')}",
        "environment": os.getenv("ENVIRONMENT")
    }