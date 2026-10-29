# Changelog

Every change to shared code: date, who, what, why.

## 2026-10-28 — Steven
- main.py, main2.py: seed command-line runs from config (`seed`, default "random" if missing); was GUI-only.
- main.py, main2.py: cudnn.benchmark True -> False (stable algorithm choice across runs).
- configs/image.yaml: added `seed: 0`.
- Test (anya, stage 1): same seed -> identical initial Gaussians; final meshes still differ ~2% (GPU nondeterminism in rasterizer backward). Benchmark off cost no speed (25-28 s / 500 steps).
