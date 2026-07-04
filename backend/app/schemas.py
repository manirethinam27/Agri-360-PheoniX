from typing import Literal

from pydantic import BaseModel, Field

CropName = Literal["Rice", "Wheat", "Cotton", "Sugarcane", "All"]


class SeasonRequest(BaseModel):
    crop: CropName = "All"
    planting_date: str = "2026-06-15"
    plots_per_crop: int = Field(8, ge=2, le=40)
    cloud_percent: float = Field(18.0, ge=0.0, le=85.0)
    noise_level: float = Field(0.025, ge=0.0, le=0.18)
    revisit_days: int = Field(5, ge=1, le=16)
    seed: int | None = None


class CompareRequest(BaseModel):
    crop: CropName = "All"
    planting_date: str = "2026-06-15"
    plots_per_crop: int = Field(8, ge=2, le=40)
    low_cloud_percent: float = Field(8.0, ge=0.0, le=85.0)
    high_cloud_percent: float = Field(55.0, ge=0.0, le=85.0)
    low_noise_level: float = Field(0.015, ge=0.0, le=0.18)
    high_noise_level: float = Field(0.09, ge=0.0, le=0.18)
    revisit_days: int = Field(5, ge=1, le=16)
    seed: int | None = None
