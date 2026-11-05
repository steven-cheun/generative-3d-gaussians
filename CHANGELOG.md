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

## 2026-11-03 — Steven (3): 
- added `scripts/image_prep.py` (render / sheet / process for GSO inputs) 
- added `scripts/eval_clip.py` (CLIP similarity → `results/metrics.csv`).

## 2026-11-03 - Hector
- data/gso_inputs/: 14 test-set inputs (`<short_name>_rgba.png`, 256x256 RGBA) from Steven's `0_0` renders via `scripts/image_prep.py process`. All 14 checked: background removed, centered (longest side 200-202 px), nothing touching the edges, colors match the renders.
- data/gso_inputs/objects.csv: `cartridge` gso_name `Pokémon_...` -> `Pokemon_...`, render folder renamed to match. Why: on Windows, OpenCV can't open paths with `é`, and image_prep.py reads the CSV in the system encoding (cp1252), so this row failed. Only `process` reads gso_name; rerunning `process` on another copy needs the same folder rename.
- Environment for the inputs: Windows laptop, CPU only, Python 3.13.5, torch 2.15.0+cpu, torchvision 0.29.2+cpu, rembg 2.0.86 (u2net), opencv-python 5.0.0, numpy 2.5.4, pillow 13.0.0. `process.py` also needs torchvision; kiui is not needed for `process`.
- Note: shark and orca are small in the head-on render, so their inputs are upscaled about 2x and a bit soft.
- 2026-11-04 — Steven: scripts/clip_sim.py = copy of the authors' kiui/cli/clip_sim.py, fixed for transformers 5 (features computed as vision model -> projection; same math). eval_clip.py now uses it, passes --force_cuda_rast, retries failed rows, requires --tag.
- 2026-11-04 — Steven: scripts/clip_sim.py = copy of the authors' kiui/cli/clip_sim.py, fixed for transformers 5 (features computed as vision model -> projection; same math). eval_clip.py now uses it, passes --force_cuda_rast, retries failed rows, requires --tag.

## 2026-11-05 - Hector
- notebooks/04_evaluation.ipynb (new): baseline analysis of the GSO test set. Joins results/metrics.csv with results/baseline_log.csv, per-object CLIP mean and seed std, per-group table (standard, head-on, flat/printed, two figurines), overall mean vs the paper's 0.738, two figures. Section 8 pairs baseline vs improved runs automatically once improved rows exist. CPU only. Figures and table CSVs are written to figures/ (not committed; uploaded to the Drive).
- Tag mismatch found: metrics.csv tags the GSO runs `gso_baseline`, but baseline_log.csv tags them `baseline`, the same tag as the 24 mini-baseline runs. The notebook works around it by keeping only test-set objects from the log and joining on (name, seed). For the improved runs, please use matching tags in both files.
- data/gso_inputs/objects.csv: removed a comma from the `cartridge` notes (my 11/3 edit). It split the row into 5 fields, so pandas could not read the file. image_prep.py was not affected.
