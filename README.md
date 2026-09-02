# Build your own Swiss inflation basket

**→ https://mr-lightblue.github.io/personal-inflation-ch/**

The Swiss consumer price index is a weighted mean of thirteen COICOP divisions.
The official figure describes an average household that may not resemble yours:
a quarter of the basket is housing and energy, a sixth is healthcare, a tenth is
transport. This page keeps the published price series untouched and hands the
reader the one thing chosen on their behalf — the weights. Thirteen sliders
start at the official 2026 shares; moving them rebuilds the index and shows how
far a household's own inflation can drift from the national average.

Both lines on the chart are the *same* computation: the thirteen divisional
indices, re-based to January 2016 = 100, combined with one fixed set of weights.
Only the weights differ. With the sliders at their defaults the two lines
coincide exactly, and the page proves it rather than asserting it — a self-test
under the method note prints the measured `max |difference|` across the 127
months, which is `0.0e+0`.

Two things are stated on the page itself rather than buried in this file:

- The published index **re-weights and re-bases every December**, so a
  constant-weight recombination is not the same object as the official series.
  Over this window the two differ by **+0.177 percentage points**. That gap is a
  property of an annually re-weighted index, not an error of this page — and
  holding the weights still is exactly what makes the two lines comparable to
  each other.
- **Compulsory health insurance premiums are not in the index at all.** Division
  06 prices medical services, medicines and devices; premiums are treated as a
  transfer rather than as consumption. This is why healthcare reads −4.9% over
  the window while premiums rose, and it means the largest single item in many
  Swiss household budgets sits outside this calculator entirely.

## Data source

| | |
|---|---|
| Publisher | Federal Statistical Office (BFS/OFS/UST), Switzerland |
| Dataset | Swiss Consumer Price Index (LIK/IPC), December 2025 = 100, detailed results since 1982, basket structure 2025 |
| Identifier | `su-e-05.02.66` |
| As of | published **2026-08-03**, archived here as `data/lik_2026-08-03.xlsx` |
| Retrieved from | `https://dam-api.bfs.admin.ch/hub/api/dam/assets/36773867/master` |
| Extent used | 2016-01 to 2026-07 — 127 months, 13 divisions, no missing values |
| Licence | [opendata.swiss terms of use](https://opendata.swiss/en/terms-of-use), free reuse including commercial, **attribution required** |

Attribution as required: *Source: Federal Statistical Office, Swiss Consumer
Price Index.* The publisher's URL is not versioned — a later release silently
replaces the file — so the exact workbook used is committed here and the page
cites its publication date.

## Regenerating the JSON

```bash
python3 -m pip install openpyxl
python3 scripts/prep_lik.py
```

Paths are anchored to the repository root via `__file__`, so the script runs
from any working directory. It re-downloads the workbook only if
`data/lik_2026-08-03.xlsx` is missing, and writes `docs/data/lik_t13.json` —
the single file the page fetches.

It asserts on the way through: 13 divisions, weights summing to 100.000 within
5e-4, 127 complete months with no gaps. It stops rather than emitting a
silently wrong file. Note that the workbook repeats its own hierarchy in a
summary block, which the script cuts before filtering; without that cut you get
26 divisions and weights summing to 200.

## Layout

```
docs/index.html        the page — one self-contained file, plain HTML/CSS/JS
docs/data/             the JSON it fetches
scripts/prep_lik.py    workbook -> JSON
data/                  the archived source workbook
```

## Running it locally

The page fetches its JSON, so opening `docs/index.html` by double-click fails
under `file://`. Serve it:

```bash
python3 -m http.server -d docs 8000   # then open http://localhost:8000/
```

Published with GitHub Pages from the `main` branch, `/docs` folder. The only
external dependency is d3 v7 from cdnjs; there is no build step.
