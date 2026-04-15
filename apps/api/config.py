import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
_DEFAULT_SQLITE_URL = f"sqlite:///{(BASE_DIR / 'data' / 'homeops.db').as_posix()}"
_DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "HomeSense AI API")
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = _as_bool(os.getenv("DEBUG"), default=False)

    database_url: str = os.getenv("DATABASE_URL", _DEFAULT_SQLITE_URL)
    database_auto_create: bool = _as_bool(
        os.getenv("DATABASE_AUTO_CREATE"),
        default=os.getenv("ENVIRONMENT", "development").strip().lower() != "production",
    )
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "45"))
    refresh_token_minutes: int = int(os.getenv("REFRESH_TOKEN_MINUTES", "4320"))

    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_chat_model: str = os.getenv("GROQ_CHAT_MODEL", "llama-3.1-8b-instant")
    groq_diagnosis_model: str = os.getenv("GROQ_DIAGNOSIS_MODEL", "llama-3.1-8b-instant")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    cohere_api_key: str = os.getenv("COHERE_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    vector_provider: str = os.getenv("VECTOR_PROVIDER", "pinecone_fallback")
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_index: str = os.getenv("PINECONE_INDEX", "homesense-manuals")

    rainforest_api_key: str = os.getenv("RAINFOREST_API_KEY", "")
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_whatsapp_from: str = os.getenv("TWILIO_WHATSAPP_FROM", "")

    warranty_days: int = int(os.getenv("WARRANTY_DAYS", "365"))
    scheduler_enabled: bool = _as_bool(os.getenv("SCHEDULER_ENABLED"), default=True)
    tool_calls_enabled: bool = _as_bool(os.getenv("TOOL_CALLS_ENABLED"), default=True)
    danger_escalation_text: str = os.getenv(
        "DANGER_ESCALATION_TEXT",
        "DANGER: This repair involves high-voltage, gas lines, or sealed internal components. "
        "DO NOT attempt to fix this yourself as it poses a severe safety risk. "
        "Contact a technician immediately at 8757219362 or use the app support action to forward this diagnostic report.",
    )
    software_lock_hints: str = os.getenv(
        "SOFTWARE_LOCK_HINTS",
        "Samsung Family Hub Refrigerators,Modern Bosch 800-Series Dishwashers,"
        "LG SmartWash Combos,Apple/Nest Smart Home hubs,John Deere riding mowers/tractors",
    )

    @property
    def cors_origins(self) -> list[str]:
        origins = os.getenv("CORS_ORIGINS", _DEFAULT_CORS_ORIGINS)
        if origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in origins.split(",") if origin.strip()]

    @property
    def pinecone_required(self) -> bool:
        provider = self.vector_provider.strip().lower()
        return provider.startswith("pinecone") and "fallback" not in provider


settings = Settings()


BASE_REQUIRED_ENV_VARS = [
    "DATABASE_URL",
    "JWT_SECRET",
    "GOOGLE_API_KEY",
    "GROQ_API_KEY",
]

PINECONE_ENV_VARS = ["PINECONE_API_KEY", "PINECONE_INDEX"]


def missing_required_env_vars() -> list[str]:
    required = list(BASE_REQUIRED_ENV_VARS)
    if settings.pinecone_required:
        required.extend(PINECONE_ENV_VARS)
    return [name for name in required if not os.getenv(name)]


def validate_environment() -> list[str]:
    errors: list[str] = []

    missing = missing_required_env_vars()
    if missing:
        errors.append(f"Missing required env vars: {', '.join(missing)}")

    if settings.environment.lower() == "production":
        if "postgresql" not in settings.database_url:
            errors.append("DATABASE_URL must point to PostgreSQL in production")
        if settings.jwt_secret == "change-me-in-production":
            errors.append("JWT_SECRET must be changed in production")

    return errors
