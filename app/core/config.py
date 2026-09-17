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


settings = Settings()