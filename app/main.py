from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os

from app.core.database import create_tables
from app.api.bot import router as bot_router
from app.api.tasks import router as task_router
from app.routes.auth import router as auth_router


app = FastAPI(title="Smart Email Bot")


@app.on_event("startup")
def startup():
    create_tables()

    from app.core.database import engine

    print("=" * 50)
    print("DATABASE:", engine.url)
    print("=" * 50)
    print("Current Directory:", os.getcwd())


app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv(
        "SESSION_SECRET",
        "smart-email-bot-dev-session-secret"
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(bot_router)
app.include_router(task_router)
app.include_router(auth_router)


@app.get("/")
def home():
    return {"message": "Smart Email Bot Running"}