# Changelog

Every change to shared code: date, who, what, why.

## 2026-10-28 — Steven
- main.py, main2.py: seed command-line runs from config (`seed`, default "random" if missing); was GUI-only.
- main.py, main2.py: cudnn.benchmark True -> False (stable algorithm choice across runs).
- configs/image.yaml: added `seed: 0`.
- Test (anya, stage 1): same seed -> identical initial Gaussians; final meshes still differ ~2% (GPU nondeterminism in rasterizer backward). Benchmark off cost no speed (25-28 s / 500 steps).

## 2026-10-28 — Steven (2)
- scripts/run_batch.py (new, ours): runs stage 1 + 2 over images x seeds; logs time, peak VRAM, Gaussian count, mesh v/f to results/<tag>_log.csv. Authors' scripts/runall.py untouched.
- Smoke test (anya, seed 0): 65 s total, 24,673 final Gaussians, stage 2 keeps the mesh unchanged.
