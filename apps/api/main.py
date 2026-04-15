import logging

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from api.auth import router as auth_router
from api.alerts import router as alerts_router
from api.inventory import router as inventory_router
from api.diagnose import router as diagnose_router
from api.manuals import router as manuals_router
from api.onboard import router as onboard_router
from api.reminders import router as reminders_router
from api.tools import router as tools_router
from apis.llm_api import chat as llm_chat
from apis.vision_api import scan_appliance
from config import missing_required_env_vars, settings, validate_environment
from database.db import SessionLocal, engine, init_db
from scheduler.jobs import start_scheduler, stop_scheduler
from telemetry.middleware import TelemetryMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("homesense")

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TelemetryMiddleware)


def _database_ready() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1"))
        return True
    except SQLAlchemyError:
        return False

@app.on_event("startup")
def startup_event():
    errors = validate_environment()
    if errors:
        for error in errors:
            logger.error("config_error=%s", error)
        raise RuntimeError("Environment validation failed")

    init_db()
    if not _database_ready():
        raise RuntimeError("Database connection failed at startup")

    if settings.scheduler_enabled:
        start_scheduler(SessionLocal)


@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()

class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=1200)

@app.get("/")
def read_root():
    return {
        "status": "HomeSense API is alive and ready!",
        "environment": settings.environment,
    }


@app.get("/health")
def health():
    missing = missing_required_env_vars()
    db_ok = _database_ready()
    return {
        "ok": len(missing) == 0 and db_ok,
        "checks": {
            "env_ok": len(missing) == 0,
            "missing_env": missing,
            "database_ok": db_ok,
            "providers": {
                "groq": bool(settings.groq_api_key),
                "google": bool(settings.google_api_key),
                "pinecone": bool(settings.pinecone_api_key),
            },
        },
    }


app.include_router(auth_router)
app.include_router(alerts_router)
app.include_router(inventory_router)
app.include_router(onboard_router)
app.include_router(manuals_router)
app.include_router(diagnose_router)
app.include_router(tools_router)
app.include_router(reminders_router)

@app.post("/api/chat")
def chat(payload: ChatRequest):
    chat_response = llm_chat(payload.message)
    return {
        "answer": chat_response.get("answer", ""),
        "video_url": chat_response.get("video_url", ""),
        "source": "llm",
    }

@app.post("/api/scan")
async def scan(file: UploadFile = File(...)):
    if not file.content_type:
        raise HTTPException(status_code=400, detail="Missing file content type")
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Scan upload must be an image file")

    data = await file.read()
    return scan_appliance(data, mime_type=file.content_type)