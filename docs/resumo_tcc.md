# Thesis Summary: Degree-Day Model for *Brevipalpus yothersi* (citrus leprosis mite)
*Work summary — Pedro Augusto de Andrade Guarniéri (Agricultural Engineering, UniFatecie)*

---

## 1. Theoretical background and mathematical modeling

The biological basis comes from the laboratory experiments of **Chiavegato (1986)**, who measured the egg-to-adult cycle duration of the leprosis mite at three fixed temperatures (20 °C → 35 days; 25 °C → 21 days; 30 °C → 17 days).

A **linear regression** of the development rate (r = 1/D = a + b·T) was fitted over these three points, yielding the model's two parameters:

- **Base temperature (T_b): 10.12 °C** — below this threshold development stops;
- **Thermal constant (K): 331 degree-days** — the energy needed to complete one generation;
- Fit quality: **R² = 0.978**; mean error of re-estimated durations **< 5%**.

It is worth noting the correct species: recent taxonomic revisions reclassified most of the *B. phoenicis* complex in South American citriculture as ***Brevipalpus yothersi***. The parameters above, derived from 1986 data, **coincide** with those determined by a life table specifically for *B. yothersi* by **Castro-Reséndiz et al. (2021): T_b = 10.2 °C and K = 331.7 DD** — a convergence that reinforces the robustness of the adopted biological basis.

---

## 2. Computational tool

To make the model applicable, a predictive web dashboard (`index.html`) and a set of Python routines were developed:

- **Automatic weather:** queries the Open-Meteo API and accumulates the area's daily degree-days;
- **Biological reading:** estimates the percentage of the cycle completed since the biofix and the mite's most likely stage;
- **Decision support:** indicates the application window, positioned shortly before the predicted hatching (K = 331 DD), when the younger, more vulnerable forms predominate.

---

## 3. Case study in a commercial orchard

Using a Python script, the weather history was cross-referenced with inspection spreadsheets from **one commercial orchard** (anonymized) in northwestern Paraná, Brazil, covering the **2024–2026** seasons — **3,624 records**, of which **117** flagged leprosis. The first detection in each plot was taken as the biofix.

### Scope and limitations (an honest reading of the data)

The records come from the **farm's routine commercial scouting, with no sampling protocol designed for phenological validation**. Two consequences are important and were explicitly acknowledged in the thesis:

1. **No significant instantaneous correlation** between the monthly rate of positive inspections and temperature/DD/rainfall (e.g., r ≈ 0.05; p ≈ 0.80). This is consistent with the biology: the population seen in one inspection results from heat accumulated over weeks — already discounted by rain, natural enemies and sprays — not the temperature on that day. Inspection effort itself also varied a lot month to month. This is exactly the kind of lagging data that physiological-time management seeks to replace.
2. **Overlapping generations.** In mature orchards, eggs, nymphs and adults coexist almost continuously, which makes it impossible to confirm the exact hatching date of each generation from the available notes alone.

Therefore, **the model's validation rests on its physiological basis** (Chiavegato's regression plus the convergence with Castro-Reséndiz et al., 2021), not on a direct correlation with the field. The case study is **demonstrative**: it shows the tool turning real weather into objective, reproducible decision windows — something a fixed calendar cannot offer.

---

## Conclusion

Degree-day accumulation consistently describes *B. yothersi*'s development and can underpin an alert system for leprosis management. The limitations of routine data — no specific protocol and overlapping generations — do not allow each hatching event to be validated statistically in the field, but they reinforce the central argument: management should rest on a mechanistic reference tied to the pest's thermal biology, rather than on isolated, lagging counts. As follow-up work, monitoring designed for phenological validation (tracked cohorts, stage and application records) and the incorporation of microclimate corrections for plots under water stress are recommended.
