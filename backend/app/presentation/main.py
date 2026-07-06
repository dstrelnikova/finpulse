import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.settings import settings
from app.application.services.public_news_scheduler import (
    start_public_news_scheduler,
    stop_public_news_scheduler,
)
from app.infrastructure.database.base import Base, engine
from app.infrastructure.database.seed_rbac import seed_rbac
from app.infrastructure.middleware import ErrorHandlingMiddleware, LoggingMiddleware
from app.presentation.api.admin_users import router as admin_users_router
from app.presentation.api.auth import router as auth_router
from app.presentation.api.chat import router as chat_router
from app.presentation.api.me import router as me_router
from app.presentation.api.meta import router as options_router
from app.presentation.api.profile import router as profile_router
from app.presentation.api.public_moex import router as public_moex_router
from app.presentation.api.seo import router as seo_router
from app.presentation.api.summary import router as summary_router
from app.presentation.api.public_news import router as public_news

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="FinPulse API", version="1.0")

cors_origins = list(
    dict.fromkeys(
        [
            settings.FRONTEND_BASE_URL,
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://tauri.localhost",
            "tauri://localhost",
        ]
    )
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    seed_rbac(admin_email=getattr(settings, "ADMIN_EMAIL", None))
    start_public_news_scheduler()


@app.on_event("shutdown")
def shutdown():
    stop_public_news_scheduler()


app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.add_middleware(LoggingMiddleware)

app.add_middleware(ErrorHandlingMiddleware)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(summary_router)
app.include_router(profile_router)
app.include_router(options_router)
app.include_router(me_router)
app.include_router(admin_users_router)
app.include_router(public_news)
app.include_router(public_moex_router)
app.include_router(seo_router)


@app.get("/")
def root():
    return {"message": "Welcome to FinPulse API"}


@app.get("/healthz", tags=["Health"])
def healthz():
    return {"status": "ok"}


@app.get("/readyz", tags=["Health"])
def readyz():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="not_ready")
