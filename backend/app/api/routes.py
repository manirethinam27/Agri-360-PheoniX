from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app import db
from app.ml.trainer import train_all
from app.schemas import CompareRequest, SeasonRequest
from app.simulation.crop_profiles import CROP_PROFILES
from app.simulation.simulator import generate_observed_season, summarize_season

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "synthetic_only": True}


@router.get("/research-summary")
def research_summary() -> dict:
    return {
        "disclosure": "All generated values are synthetic. Research sources are used only to set ranges and simulator behavior.",
        "crop_profiles": {name: profile.__dict__ for name, profile in CROP_PROFILES.items()},
        "sources": [
            "FAO Irrigation Water Management: Irrigation Water Needs",
            "FAO Irrigation and Drainage Paper 56",
            "NASA Earth Observatory NDVI/EVI",
            "ESA Sentinel-2 mission facts",
            "Copernicus SentiWiki Sentinel-2 mission",
            "USGS Landsat Satellite Missions",
            "Gao 1996 NDWI/NDMI vegetation liquid water index",
            "scikit-learn RandomForestClassifier documentation",
        ],
    }


@router.post("/seasons/generate")
def generate_season(config: SeasonRequest) -> dict:
    seed, frame = generate_observed_season(config)
    season_id = uuid4().hex[:12]
    payload = {
        "season_id": season_id,
        "seed": seed,
        "config": config.model_dump(),
        "summary": summarize_season(frame),
        "metrics": train_all(frame),
        "observations": frame.to_dict(orient="records"),
    }
    db.save_season(season_id, seed, config.model_dump(), payload)
    return payload


@router.get("/seasons")
def seasons() -> list[dict]:
    return db.list_seasons()


@router.get("/seasons/{season_id}")
def season(season_id: str) -> dict:
    payload = db.get_season(season_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Season not found")
    return payload


@router.post("/compare")
def compare(config: CompareRequest) -> dict:
    low = SeasonRequest(
        crop=config.crop,
        planting_date=config.planting_date,
        plots_per_crop=config.plots_per_crop,
        cloud_percent=config.low_cloud_percent,
        noise_level=config.low_noise_level,
        revisit_days=config.revisit_days,
        seed=config.seed,
    )
    high = SeasonRequest(
        crop=config.crop,
        planting_date=config.planting_date,
        plots_per_crop=config.plots_per_crop,
        cloud_percent=config.high_cloud_percent,
        noise_level=config.high_noise_level,
        revisit_days=config.revisit_days,
        seed=config.seed,
    )
    low_seed, low_frame = generate_observed_season(low)
    _, high_frame = generate_observed_season(high)
    low_metrics, high_metrics = train_all(low_frame), train_all(high_frame)
    return {
        "seed": low_seed,
        "low_noise": {"config": low.model_dump(), "summary": summarize_season(low_frame), "metrics": low_metrics},
        "high_noise": {"config": high.model_dump(), "summary": summarize_season(high_frame), "metrics": high_metrics},
        "accuracy_delta": {
            "crop_classifier": round(low_metrics["crop_classifier"]["accuracy"] - high_metrics["crop_classifier"]["accuracy"], 4),
            "growth_stage_predictor": round(low_metrics["growth_stage_predictor"]["accuracy"] - high_metrics["growth_stage_predictor"]["accuracy"], 4),
        },
        "interpretation": "Accuracy should decline as cloud gaps and noise reduce the number and quality of clear observations.",
    }
