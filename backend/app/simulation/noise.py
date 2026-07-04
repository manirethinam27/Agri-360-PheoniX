import numpy as np
import pandas as pd


def apply_satellite_noise(
    df: pd.DataFrame,
    rng: np.random.Generator,
    cloud_percent: float,
    noise_level: float,
    revisit_days: int,
) -> pd.DataFrame:
    out = df.copy()
    out["is_revisit_day"] = False
    out["cloud_contaminated"] = False
    out["observed_ndvi"] = np.nan
    out["observed_ndmi"] = np.nan

    for _, plot_df in out.groupby("plot_id", sort=False):
        idx = plot_df.index.to_numpy()
        offset = int(rng.integers(0, max(1, revisit_days)))
        revisit_idx = idx[((plot_df["day"].to_numpy() + offset) % revisit_days) == 0]
        out.loc[revisit_idx, "is_revisit_day"] = True
        if len(revisit_idx) == 0:
            continue

        cloud_probability = cloud_percent / 100.0
        cloud_mask = rng.random(len(revisit_idx)) < cloud_probability
        for _ in range(int(rng.poisson(max(0.2, cloud_probability * 2.2)))):
            if len(revisit_idx) < 3:
                break
            start = int(rng.integers(0, len(revisit_idx)))
            length = int(rng.integers(2, min(8, len(revisit_idx) - start) + 1))
            cloud_mask[start : start + length] = True

        clear_idx = revisit_idx[~cloud_mask]
        cloudy_idx = revisit_idx[cloud_mask]
        out.loc[cloudy_idx, "cloud_contaminated"] = True
        ndvi_noise = rng.normal(0, noise_level, len(clear_idx)) + rng.uniform(-noise_level / 2, noise_level / 2, len(clear_idx))
        ndmi_noise = rng.normal(0, noise_level * 0.85, len(clear_idx)) + rng.uniform(-noise_level / 3, noise_level / 3, len(clear_idx))
        out.loc[clear_idx, "observed_ndvi"] = np.clip(out.loc[clear_idx, "true_ndvi"].to_numpy() + ndvi_noise, -0.1, 0.95)
        out.loc[clear_idx, "observed_ndmi"] = np.clip(out.loc[clear_idx, "true_ndmi"].to_numpy() + ndmi_noise, -0.25, 0.75)

    out["missing_reason"] = np.where(
        ~out["is_revisit_day"], "not_revisited", np.where(out["cloud_contaminated"], "cloud", "observed")
    )
    return out
