from dotenv import load_dotenv
import os


load_dotenv()


class Settings:

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

    CHAT_ID = os.getenv("CHAT_ID")

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///smart.db"
    )

    # ==========================================
    # Google OAuth
    # ==========================================

    GOOGLE_CLIENT_ID = os.getenv(
        "GOOGLE_CLIENT_ID"
    )

    GOOGLE_CLIENT_SECRET = os.getenv(
        "GOOGLE_CLIENT_SECRET"
    )

    GOOGLE_REDIRECT_URI = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://127.0.0.1:8000/auth/callback"
    )


settings = Settings()