import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "soil_system.db").replace("\\", "/")

class Settings:
    PROJECT_NAME: str = "AI Smart Soil System"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")
    API_V1_STR: str = "/api/v1"

settings = Settings()
