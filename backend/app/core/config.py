import os

class Settings:
    PROJECT_NAME: str = "AI Smart Soil System"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./soil_system.db")
    API_V1_STR: str = "/api/v1"

settings = Settings()
