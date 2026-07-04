from __future__ import annotations

import secrets
from datetime import date, timedelta
from uuid import uuid4

import numpy as np
import pandas as pd

from app.simulation.advisory import advisory_from_observation
from app.simulation.crop_profiles import CROP_PROFILES, COMMON_STAGE_LABELS, CropProfile, crops_for_selection
from app.simulation.noise import apply_satellite_noise


def _smoothstep(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def _stage_for_day(day: int, duration: int, profile: CropProfile) -> tuple[str, str, int]:
    scale = duration / sum(profile.stage_lengths)
    cutoffs = np.cumsum([round(v * scale) for v in profile.stage_lengths])
    cutoffs[-1] = duration
    idx = min(int(np.searchsorted(cutoffs, day + 1, side="left")), 3)
    return COMMON_STAGE_LABELS[idx], profile.stage_names[idx], idx


def _vegetation_curve(t: np.ndarray, profile: CropProfile) -> np.ndarray:
    rise = _smoothstep(t / profile.peak_window[0])
    decline = _smoothstep((t - profile.peak_window[1]) / max(0.05, 1 - profile.peak_window[1]))
    peak = profile.ndvi_min + (profile.ndvi_peak - profile.ndvi_min) * rise
    return peak * (1 - decline) + profile.ndvi_end * decline


def _stress_event(rng: np.random.Generator, duration: int, sensitivity: float) -> tuple[int, int, float]:
    if rng.random() > 0.42:
        return duration + 1, duration + 1, 0.0
    start = int(rng.integers(max(10, duration // 5), max(11, int(duration * 0.72))))
    length = int(rng.integers(max(8, duration // 16), max(10, duration // 7)))
    severity = float(rng.uniform(0.25, 0.85) * (0.6 + sensitivity * 0.6))
    return start, min(duration - 1, start + length), min(1.0, severity)


def generate_clean_season(crop_selection: str, planting_date: str, plots_per_crop: int, seed: int | None = None) -> tuple[int, pd.DataFrame]:
    season_seed = int(seed if seed is not None else secrets.randbits(32))
    rng = np.random.default_rng(season_seed)
    start_date = date.fromisoformat(planting_date)
    rows: list[dict] = []

    for crop_name in crops_for_selection(crop_selection):
        profile = CROP_PROFILES[crop_name]
        for _ in range(plots_per_crop):
            duration = int(rng.integers(profile.duration_range[0], profile.duration_range[1] + 1))
            plot_start = start_date + timedelta(days=int(rng.integers(-12, 13)))
            weather_factor = float(np.clip(rng.normal(1.0, 0.09), 0.78, 1.22))
            water_need = float(rng.uniform(*profile.water_need_mm))
            stress_start, stress_end, stress_severity = _stress_event(rng, duration, profile.drought_sensitivity)
            plot_id = f"{crop_name[:2].upper()}-{uuid4().hex[:8]}"

            days = np.arange(duration)
            t = days / max(1, duration - 1)
            true_ndvi = _vegetation_curve(t, profile)
            true_ndvi += (weather_factor - 1.0) * 0.07 + rng.normal(0, 0.012, duration).cumsum() / 12

            stress_shape = np.zeros(duration)
            if stress_severity > 0:
                active = (days >= stress_start) & (days <= stress_end)
                phase = (days[active] - stress_start) / max(1, stress_end - stress_start)
                stress_shape[active] = np.sin(np.pi * phase) * stress_severity
                recovery = (days > stress_end) & (days <= min(duration - 1, stress_end + 18))
                if recovery.any():
                    stress_shape[recovery] = np.linspace(stress_severity * 0.45, 0, recovery.sum())

            moisture = profile.ndmi_min + (profile.ndmi_peak - profile.ndmi_min) * _smoothstep(t / max(0.15, profile.peak_window[0] * 0.9))
            senescence = _smoothstep((t - profile.peak_window[1]) / max(0.05, 1 - profile.peak_window[1]))
            true_ndmi = moisture * (1 - senescence) + (profile.ndmi_min + 0.04) * senescence
            true_ndvi = np.clip(true_ndvi - stress_shape * 0.11, -0.05, 0.92)
            true_ndmi = np.clip(true_ndmi + (weather_factor - 1.0) * 0.05 - stress_shape * 0.24 + rng.normal(0, 0.01, duration), -0.2, 0.72)

            for day in range(duration):
                stage_class, stage_name, stage_idx = _stage_for_day(day, duration, profile)
                stress_score = float(np.clip(stress_shape[day] * profile.drought_sensitivity * [0.55, 0.78, 1.0, 0.70][stage_idx], 0, 1))
                rows.append(
                    {
                        "plot_id": plot_id,
                        "crop": crop_name,
                        "date": (plot_start + timedelta(days=day)).isoformat(),
                        "planting_date": plot_start.isoformat(),
                        "day": int(day),
                        "day_norm": round(day / max(1, duration - 1), 4),
                        "duration": int(duration),
                        "growth_stage": stage_class,
                        "stage_name": stage_name,
                        "stage_index": stage_idx,
                        "true_ndvi": round(float(true_ndvi[day]), 4),
                        "true_ndmi": round(float(true_ndmi[day]), 4),
                        "water_stress": stress_score > 0.35,
                        "water_stress_label": "Stress" if stress_score > 0.55 else ("Watch" if stress_score > 0.30 else "Normal"),
                        "stress_score": round(stress_score, 4),
                        "weather_factor": round(weather_factor, 3),
                        "seasonal_water_need_mm": round(water_need, 1),
                        "synthetic": True,
                    }
                )
    return season_seed, pd.DataFrame(rows)


def generate_observed_season(config) -> tuple[int, pd.DataFrame]:
    seed, clean = generate_clean_season(config.crop, config.planting_date, config.plots_per_crop, config.seed)
    observed = apply_satellite_noise(clean, np.random.default_rng(seed + 991), config.cloud_percent, config.noise_level, config.revisit_days)
    return seed, observed


def summarize_season(df: pd.DataFrame) -> dict:
    clear = df.dropna(subset=["observed_ndvi", "observed_ndmi"])
    latest_rows = []
    for _, plot_df in df.sort_values("day").groupby("plot_id", sort=False):
        latest_clear = plot_df.dropna(subset=["observed_ndmi"]).tail(1)
        row = latest_clear.iloc[0] if len(latest_clear) else plot_df.tail(1).iloc[0]
        ndmi = None if pd.isna(row.get("observed_ndmi")) else float(row["observed_ndmi"])
        latest_rows.append({**row.to_dict(), "advisory": advisory_from_observation(ndmi, float(row["stress_score"]), row["crop"], row["stage_name"])})
    return {
        "synthetic_disclosure": "All values are generated by the included simulator; no real satellite or field datasets are used.",
        "rows": int(len(df)),
        "clear_observations": int(len(clear)),
        "missing_observations": int(len(df) - len(clear)),
        "cloud_percent_realized": round(float(df["cloud_contaminated"].mean() * 100), 2),
        "crop_counts": df[["plot_id", "crop"]].drop_duplicates()["crop"].value_counts().to_dict(),
        "stress_counts": df["water_stress_label"].value_counts().to_dict(),
        "mean_observed_ndvi": None if clear.empty else round(float(clear["observed_ndvi"].mean()), 3),
        "mean_observed_ndmi": None if clear.empty else round(float(clear["observed_ndmi"].mean()), 3),
        "latest_plot_status": latest_rows[:24],
    }
