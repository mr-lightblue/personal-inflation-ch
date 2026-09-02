"""Prepare the LIK data for the personal-inflation-ch page.

Source (archived locally, the URL is not versioned):
  https://dam-api.bfs.admin.ch/hub/api/dam/assets/36773867/master
  BFS, CPI (December 2025 = 100), detailed results since 1982,
  basket structure 2025, id su-e-05.02.66, published 2026-08-03.

Writes data/lik_2026-08-03.xlsx (the citable artefact) and docs/data/lik_t13.json,
the single JSON the page fetches. All paths are anchored to the repository root
derived from __file__, so the script may be run from any working directory.
"""

import datetime
import json
import os
import subprocess

import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://dam-api.bfs.admin.ch/hub/api/dam/assets/36773867/master"
XLSX = os.path.join(ROOT, "data", "lik_2026-08-03.xlsx")
OUT = os.path.join(ROOT, "docs", "data", "lik_t13.json")
FIRST, LAST = (2016, 1), (2026, 7)
SEPARATOR = "Total und"          # the summary block that repeats the hierarchy

# ------------------------------------------------------------- download -----
if os.path.exists(XLSX):
    print(f"{XLSX} already present ({os.path.getsize(XLSX)/1024/1024:.2f} MB) — reusing it")
else:
    raw = subprocess.run(["curl", "-sL", "--max-time", "300", "-A", "Mozilla/5.0", URL],
                         capture_output=True).stdout
    if raw[:2] != b"PK":
        raise SystemExit("the download is not an xlsx file")
    os.makedirs(os.path.dirname(XLSX), exist_ok=True)
    with open(XLSX, "wb") as fh:
        fh.write(raw)
    print(f"downloaded {XLSX}: {len(raw)/1024/1024:.2f} MB")

wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)


def block(sheet):
    """Header row and the main hierarchy, cut before the summary block."""
    rows = list(wb[sheet].iter_rows(values_only=True))
    header = rows[3]
    body = []
    for r in rows[4:]:
        if r[0] and str(r[0]).startswith(SEPARATOR):
            break
        if r[0] and isinstance(r[1], int):
            body.append(r)
    return header, body


hdr_i, idx_rows = block("INDEX_m")
hdr_w, w_rows = block("Weights")
print(f"main hierarchy: {len(idx_rows)} positions in INDEX_m, {len(w_rows)} in Weights")

# ----------------------------------------------------------- the checks -----
divisions = [r for r in idx_rows if r[3] == 2]
assert len(divisions) == 13, f"expected 13 COICOP divisions, found {len(divisions)}"

wcol = [j for j, c in enumerate(hdr_w) if str(c) == "2026"]
assert len(wcol) == 1, f"expected exactly one column headed 2026, found {len(wcol)}"
wcol = wcol[0]
weights = {r[0]: r[wcol] for r in w_rows}
wsum = sum(weights[r[0]] for r in divisions)
assert abs(wsum - 100.0) < 5e-4, f"division weights sum to {wsum}, expected 100.000"

months_all = [(j, c) for j, c in enumerate(hdr_i) if isinstance(c, datetime.datetime)]
window = [(j, c) for j, c in months_all
          if (c.year, c.month) >= FIRST and (c.year, c.month) <= LAST]
labels = [f"{c:%Y-%m}" for _, c in window]

total_row = [r for r in idx_rows if r[3] == 1]
assert len(total_row) == 1, f"expected one total row, found {len(total_row)}"
total = [total_row[0][j] for j, _ in window]

series, missing = {}, 0
for r in divisions:
    s = [r[j] for j, _ in window]
    missing += sum(1 for v in s if v is None)
    series[r[0]] = s
missing += sum(1 for v in total if v is None)

print(f"\nmonths in the window {labels[0]} to {labels[-1]}: {len(labels)}")
print(f"missing values across the 13 divisions and the total: {missing}")
assert len(labels) == 127, f"expected 127 months, got {len(labels)}"
assert missing == 0, f"{missing} missing values"

print(f"\n{'COICOP':<8}{'division':<44}{'weight %':>9}")
for r in divisions:
    coicop = str(r[4]).lstrip("'")
    name = (r[12] or r[11] or "").strip()
    print(f"{coicop:<8}{name[:42]:<44}{weights[r[0]]:>9.3f}")
print(f"{'':<8}{'sum':<44}{wsum:>9.3f}")

# ------------------------------ fixed-weight reconstruction over the window --
base = {code: series[code][0] for code in series}
recon = []
for t in range(len(labels)):
    v = sum(weights[code] / 100 * series[code][t] / base[code] for code in series) * 100
    recon.append(v)
pub = [v / total[0] * 100 for v in total]
gap = recon[-1] - pub[-1]
print(f"\nfixed-weight reconstruction with the official 2026 weights, {labels[0]} = 100")
print(f"  published total at {labels[-1]}      : {pub[-1]:.3f}")
print(f"  fixed-weight reconstruction        : {recon[-1]:.3f}")
print(f"  cumulative gap over {len(labels)} months : {gap:+.3f} percentage points")

# ------------------------------------------------------------------ write ---
payload = {
    "meta": {
        "source": "Federal Statistical Office (BFS), Swiss Consumer Price Index",
        "table": "su-e-05.02.66 — CPI (December 2025 = 100), detailed results since 1982, "
                 "basket structure 2025",
        "published": "2026-08-03",
        "archived_file": os.path.relpath(XLSX, ROOT),   # never an absolute path
        "index_base": "December 2025 = 100",
        "window": [labels[0], labels[-1]],
        "weight_year": 2026,
        "weight_sum": round(wsum, 3),
        "reconstruction_gap_pp": round(gap, 3),
        "licence": "opendata.swiss terms of use, attribution required",
    },
    "months": labels,
    "total": [round(v, 3) for v in total],
    "divisions": [
        {"coicop": str(r[4]).lstrip("'"),
         "name": (r[12] or r[11] or "").strip(),
         "weight": round(weights[r[0]], 3),
         "index": [round(v, 3) for v in series[r[0]]]}
        for r in divisions
    ],
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
print(f"\nwrote {os.path.relpath(OUT, ROOT)} ({os.path.getsize(OUT)/1024:.1f} KB)")
