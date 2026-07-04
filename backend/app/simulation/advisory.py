def advisory_from_observation(ndmi: float | None, stress_score: float, crop: str, stage: str) -> dict:
    if ndmi is None:
        return {
            "level": "No Clear Observation",
            "reason": "The latest satellite-like observation is missing because of revisit cadence or cloud contamination.",
            "stress_score": round(stress_score, 3),
            "recommendation": "Wait for the next clear pass or inspect the field before irrigating.",
        }
    if stress_score >= 0.72 or ndmi < 0.18:
        level, recommendation = "Stress Detected", "Prioritize field inspection and irrigate immediately if soil moisture confirms deficit."
    elif stress_score >= 0.52 or ndmi < 0.25:
        level, recommendation = "Irrigate Immediately", "Schedule irrigation now, especially during canopy expansion or reproductive growth."
    elif stress_score >= 0.32 or ndmi < 0.32:
        level, recommendation = "Irrigate Soon", "Plan irrigation soon and monitor the next clear satellite pass."
    else:
        level, recommendation = "Adequate", "No water-deficit action is indicated by the synthetic satellite signal."
    return {
        "level": level,
        "reason": f"{crop} in {stage} has current NDMI {ndmi:.3f} and modeled stress score {stress_score:.2f}.",
        "current_ndmi": round(ndmi, 3),
        "stress_score": round(stress_score, 3),
        "recommendation": recommendation,
    }
