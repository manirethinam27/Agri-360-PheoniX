from dataclasses import dataclass


@dataclass(frozen=True)
class CropProfile:
    name: str
    duration_range: tuple[int, int]
    stage_lengths: tuple[int, int, int, int]
    water_need_mm: tuple[int, int]
    drought_sensitivity: float
    ndvi_min: float
    ndvi_peak: float
    ndvi_end: float
    ndmi_min: float
    ndmi_peak: float
    peak_window: tuple[float, float]
    stage_names: tuple[str, str, str, str]
    notes: str


CROP_PROFILES: dict[str, CropProfile] = {
    "Rice": CropProfile(
        "Rice", (90, 150), (25, 35, 55, 35), (450, 700), 0.92,
        0.18, 0.84, 0.30, 0.25, 0.58, (0.50, 0.78),
        ("Establishment", "Tillering", "Panicle/Booting", "Ripening"),
        "High drought sensitivity; paddy-like moisture keeps NDMI comparatively high until ripening.",
    ),
    "Wheat": CropProfile(
        "Wheat", (120, 150), (15, 30, 65, 40), (450, 650), 0.58,
        0.16, 0.78, 0.22, 0.16, 0.42, (0.45, 0.72),
        ("Emergence", "Tillering/Stem Extension", "Heading/Grain Fill", "Maturity"),
        "Compact green-up, peak near heading/grain fill, and fast senescence.",
    ),
    "Cotton": CropProfile(
        "Cotton", (180, 195), (30, 50, 65, 50), (700, 1300), 0.38,
        0.14, 0.76, 0.34, 0.13, 0.39, (0.46, 0.74),
        ("Squaring", "Vegetative Growth", "Flowering/Boll Fill", "Boll Opening"),
        "Lower FAO drought sensitivity than rice or sugarcane, but stress still depresses NDMI during boll fill.",
    ),
    "Sugarcane": CropProfile(
        "Sugarcane", (270, 365), (45, 95, 150, 75), (1500, 2500), 0.90,
        0.20, 0.88, 0.54, 0.22, 0.56, (0.42, 0.86),
        ("Germination", "Tillering", "Grand Growth", "Ripening"),
        "Long high-biomass plateau with high seasonal water need and a gentler maturity decline.",
    ),
}

COMMON_STAGE_LABELS = ("Initial", "Development", "Mid-season", "Late-season")


def crops_for_selection(selection: str) -> list[str]:
    return list(CROP_PROFILES) if selection == "All" else [selection]
