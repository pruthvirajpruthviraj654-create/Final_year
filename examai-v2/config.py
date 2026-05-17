# ============================================================
# config.py — Application Configuration
# ============================================================
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY              = os.environ.get("SECRET_KEY", "examai-v2-secret-2025")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
                              f"sqlite:///{os.path.join(BASE_DIR,'instance','examai.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY          = os.environ.get("JWT_SECRET_KEY", "jwt-v2-secret-2025")
    JWT_ACCESS_TOKEN_EXPIRES= timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=30)
    JWT_TOKEN_LOCATION      = ["headers", "cookies"]
    JWT_COOKIE_SECURE       = False
    JWT_COOKIE_CSRF_PROTECT = False
    UPLOAD_FOLDER           = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH      = 16 * 1024 * 1024
    OPENROUTER_API_KEY      = os.environ.get("OPENROUTER_API_KEY", "")
    DEFAULT_AI_MODEL        = os.environ.get("DEFAULT_AI_MODEL", "openai/gpt-3.5-turbo")
    OPENROUTER_URL          = "https://openrouter.ai/api/v1/chat/completions"

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    JWT_COOKIE_SECURE = True

config_map = {"development": DevelopmentConfig, "production": ProductionConfig}
ActiveConfig = config_map.get(os.environ.get("FLASK_ENV", "development"), DevelopmentConfig)
