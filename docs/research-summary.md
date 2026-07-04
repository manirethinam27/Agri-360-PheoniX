# Research Summary

All simulator values are synthetic. The project uses research only to constrain ranges and behavior.

## Crop phenology

- Rice: FAO lists rice at 90-150 days, high drought sensitivity, and 450-700 mm crop water need. The simulator models establishment, tillering, panicle/booting, and ripening with a high NDMI profile for paddy-like conditions and harvest decline.
- Wheat: FAO groups barley/oats/wheat at 120-150 days and 450-650 mm water need. The simulator uses a compact green-up, peak around heading/grain fill, and quick senescence.
- Cotton: FAO lists cotton at 180-195 days, 700-1300 mm water need, and low drought sensitivity. The simulator still lowers NDMI under stress, especially during flowering/boll fill.
- Sugarcane: FAO lists sugarcane at 270-365 days in the general duration table, while FAO Kc tables discuss 12-month ratoon and 18-month virgin crops. The simulator uses a hackathon-friendly 270-365 day season with a long grand-growth plateau and high water need of 1500-2500 mm.

## Remote sensing behavior

NDVI is modeled from canopy density: low early, high at peak vegetation, and lower during maturity or harvest. NDMI is modeled as a canopy water-content signal using the accepted NIR-SWIR moisture-index concept. Sentinel-2-style 5-day revisit and Landsat-style longer revisit settings motivate configurable revisit intervals. Cloud contamination creates missing observations rather than clean values.

## Water stress logic

Stress episodes reduce NDMI faster than NDVI because canopy water content responds before structural greenness fully declines. Stress intensity is weighted by crop drought sensitivity and growth stage; reproductive or grand-growth periods receive higher stress impact.

## ML choice

Random Forest was selected over heavier boosting stacks because it is robust for tabular features, fast for live demos, easy to explain, and part of scikit-learn. The model receives observed NDVI, observed NDMI, time, and short-window slopes only.
