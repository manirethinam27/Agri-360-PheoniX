# Simulation Module

The executable simulator lives in `backend/app/simulation`.

Pipeline:

1. Generate crop-specific daily clean phenology from FAO-constrained duration and stage profiles.
2. Add weather and water stress effects.
3. Keep clean `true_ndvi` and `true_ndmi` for transparency.
4. Apply satellite noise engine to create `observed_ndvi` and `observed_ndmi`.
5. Train ML only on observed features.

This folder exists to make the hackathon-required project structure explicit.
