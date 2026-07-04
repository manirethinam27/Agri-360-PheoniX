from app.ml.trainer import train_all
from app.schemas import SeasonRequest
from app.simulation.simulator import generate_observed_season


def test_synthetic_season_contains_observed_and_hidden_columns():
    seed, frame = generate_observed_season(SeasonRequest(plots_per_crop=2, cloud_percent=10, noise_level=0.02, seed=123))
    assert seed == 123
    assert {"true_ndvi", "true_ndmi", "observed_ndvi", "observed_ndmi", "crop", "growth_stage"}.issubset(frame.columns)
    assert frame["crop"].nunique() == 4
    assert frame["observed_ndvi"].notna().sum() > 20


def test_models_train_on_observed_features():
    _, frame = generate_observed_season(SeasonRequest(plots_per_crop=3, cloud_percent=12, noise_level=0.02, seed=999))
    metrics = train_all(frame)
    assert metrics["crop_classifier"]["feature_count"] > 30
    assert "true_ndvi" not in metrics["crop_classifier"].get("features_used", [])
    assert metrics["growth_stage_predictor"]["accuracy"] >= 0
