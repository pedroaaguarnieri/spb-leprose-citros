# Degree-Day Model for *Brevipalpus yothersi* (citrus leprosis mite)

Open-source predictive system that applies the **Degree-Day (DD) model** to track the development of the mite that transmits citrus leprosis (*Brevipalpus yothersi*, formerly treated as *B. phoenicis*) and support management decisions in commercial orchards. The goal is to replace the fixed spray calendar with intervention timing driven by the pest's **physiological time**.

Supporting repository for an undergraduate thesis in Agronomy — UniFatecie, Paranavaí, Brazil.

**Live demo:** https://leprose.pedroguarnieri.com.br

---

## Background: the thermal parameters

The mite is a poikilothermic organism: it only develops above a lower base temperature (T_b), and its development rate is proportional to the heat accumulated above that threshold. The model's two parameters were obtained by **linear regression** (r = 1/D = a + b·T) over the laboratory data of **Chiavegato (1986)** — 35 days at 20 °C, 21 days at 25 °C and 17 days at 30 °C:

- **T_b (base temperature) = 10.12 °C** — the point where the development rate reaches zero (−a/b);
- **K (egg-to-adult thermal constant) = 331 DD** — the inverse of the slope coefficient (1/b);
- Fit: **R² = 0.978**; mean error of re-estimated durations < 5%.

These values, derived from 1986 data, **independently converge** with those determined by a life table specifically for *B. yothersi* by **Castro-Reséndiz et al. (2021)**: **T_b = 10.2 °C** and **K = 331.7 DD**. Agreement between two studies separated by more than three decades, built on distinct methodologies, is the main argument validating the model's biological basis.

The full mathematical derivation of the regression is in [`docs/modelo_graus_dia_brevipalpus.docx`](docs/modelo_graus_dia_brevipalpus.docx) (kept in Portuguese, as it is the calculation memo submitted with the original thesis).

**Daily calculation:** `DD = max(0, T_mean − T_b)`, with `T_mean = (T_max + T_min) / 2`. Starting from the first detection (biofix), DD are summed; once the accumulation reaches K, a generation is predicted to complete.

---

## Data

- **Field:** scouting spreadsheets from a commercial citrus orchard in northwestern Paraná, Brazil, covering the **2024–2026** seasons, consolidated and **anonymized** in `data/INSPECOES_CONSOLIDADAS.xlsx` (**3,624 records**; **117** with leprosis present). A text-matching step flags mentions of eggs, nymphs and adults, distinguishing leprosis from other pests noted in the same observation.
- **Weather:** daily max/min temperatures from the **Open-Meteo** API for the area's coordinates.

> **Nature of the data.** Records come from the farm's routine commercial scouting, **with no sampling protocol designed for phenological validation**. They are therefore real but noisy data, suited to a **demonstrative case study**, not a statistical validation of generations in the field.

---

## Results and scope of the validation

The model's validation rests on its **physiological basis** — the Chiavegato (1986) regression and its convergence with Castro-Reséndiz et al. (2021), described above. The case study plays a **demonstrative** role: it shows the tool turning the thermal timeline into objective management windows, using real weather data.

Some honest notes on the field data:

- **No significant instantaneous correlation** between the monthly rate of positive inspections and temperature, DD accumulation or rainfall (e.g., r ≈ 0.05; p ≈ 0.80 for temperature). This is **expected**: the population observed in one inspection reflects heat accumulated over weeks — already filtered by rain, natural enemies and, above all, sprays — not the temperature on that day. Inspection effort also varied a lot month to month. In other words, raw scouting data is exactly the lagging information that a physiological-time approach aims to overcome.
- **Overlapping generations.** In mature orchards, eggs, nymphs and adults coexist almost constantly, which makes it impossible to confirm the exact hatching date of each generation from the available notes alone.

The exploratory phase-agreement script (`validacao_modelo.py`) is kept as a demonstration, but its percentages should **not** be read as the model's statistical accuracy, for the reasons above.

---

## Repository structure

- `data/` — consolidated, anonymized inspection records.
- `src/` — processing and analysis scripts:
  - `processar_planilhas.py` — ETL/consolidation and anonymization of the raw spreadsheets;
  - `validacao_modelo.py` — DD calculation and exploratory cross-check against inspections;
  - `analise_incidencia_clima.py` — honest incidence × thermal regime/season analysis (generates a figure and correlations).
- `docs/` — regression calculation memo and thesis summary.
- `index.html` — predictive web dashboard (runs in the browser, no install needed; PT/EN/ES).

---

## Reproducing

```bash
git clone https://github.com/pedroaaguarnieri/spb-leprose-citros.git
cd spb-leprose-citros
pip install -r requirements.txt
```

Web dashboard: open `index.html` in a browser.

Command-line analyses:

```bash
cd src
python analise_incidencia_clima.py            # incidence x weather (figure + correlations)
python validacao_modelo.py --farm "FARM_01" --lat -23.079 --lon -52.465
```

---

## References

- CASTRO-RESÉNDIZ, C. A. et al. Potential areas for the establishment of citrus leprosis virus vectors, *Brevipalpus* spp., in Mexico. *Experimental and Applied Acarology*, v. 84, n. 2, p. 365-388, 2021.
- CHIAVEGATO, L. G. Biologia do ácaro *Brevipalpus phoenicis* em citros. *Pesquisa Agropecuária Brasileira*, v. 21, n. 8, p. 813-816, 1986.
- LARANJEIRA, F. F. et al. Infestation dynamics of *Brevipalpus phoenicis* (Geijskes) in citrus orchards as affected by edaphic and climatic variables. *Experimental and Applied Acarology*, v. 66, n. 4, p. 491-508, 2015.
- ROCHA, C. M. et al. Resistance to spirodiclofen in *Brevipalpus yothersi* from Brazilian citrus groves. *Pest Management Science*, v. 77, n. 7, p. 3099-3106, 2021.

---
*A tool for Integrated Pest Management (IPM). Developed by Pedro Augusto de Andrade Guarniéri.*
