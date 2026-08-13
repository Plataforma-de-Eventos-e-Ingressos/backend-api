from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, events, tickets
from app.core.dependencies import RoleChecker
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(
    title="Event and Ticketing Platform API",
    description="This is the API for the Event and Ticketing Platform, which allows users to create and manage events, sell tickets, and handle payments.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(events.router)
app.include_router(tickets.router)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "The API is running smoothly."}