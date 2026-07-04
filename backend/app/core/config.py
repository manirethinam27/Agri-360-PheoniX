from functools import lru_cache
import os
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Smart Satellite Crop Intelligence System"
    db_path: str = os.getenv("SMART_CROP_DB", "data/smart_crop.db")
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
