from fastapi import FastAPI, Depends
import auth
import events 
from models import User, RoleEnum
from dependencies import get_current_user, RoleChecker
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(
    title="Event and Ticketing Platform API",
    description="This is the API for the Event and Ticketing Platform, which allows users to create and manage events, sell tickets, and handle payments.",
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(events.router)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "The API is running smoothly."}