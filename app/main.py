from fastapi import FastAPI
from dotenv import load_dotenv
import os
from app.api import routes, users

load_dotenv()

app = FastAPI(title=os.getenv("PROJECT_NAME"))

app.include_router(routes.router)
app.include_router(users.router)

@app.get("/")
def read_root():
    return {
        "message": f"Welcome to {os.getenv('PROJECT_NAME')}",
        "environment": os.getenv("ENVIRONMENT")
    }