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

## 2026-11-09 - Hector
- notebooks/05_failures.ipynb (new): failure analysis of the GSO baseline. Stage 1 mesh = final mesh in all 42 runs (stage 2 only changes texture). The 3 worst objects (cartridge, headset_box, turtle) hit the 100k face decimation cap in 9 of 9 runs; across 14 objects, mesh size vs CLIP Spearman rho -0.87. Tags per object from the seed 0 videos using the failure-notes categories (plus a new MISS tag), and a "usable angles out of 8" human check next to CLIP (rho 0.56). CPU only. Figures, tables and contact sheets go to figures/ (not committed; uploaded to the Drive). Write-up: failure-notes-part3.md on the Drive.

## 2026-11-14 — Steven
- scripts/pair_prep.py (new): inputs for the two-view experiment. Outline from kire depth renders (render_d/, background = 0) instead of rembg, which cut white parts touching the white background (yoshi 0_90 eyes became holes). Writes data/gso_inputs_2v (front + side, one shared zoom), data/gso_inputs_side (side-only control, own zoom), data/gso_inputs_exact (front, own zoom, exact outline).
- Shared zoom shrinks the front to 55-66% of its usual size for orca, shark, turtle (long side must fit).
- main.py, configs/image.yaml: two-view option, OFF by default (`side_input: null`). `side_input=auto` loads `<name>_side.png` as a second reference photo at `side_azimuth` (90); the known-view loss loops over `self.ref_views` (rgb + mask loss per photo, summed, so the front keeps its baseline weight). `zero123_cond=nearest` (2V-b) conditions Zero123 on the photo closest to each random view and passes the angle relative to that photo; `front` (2V-a) keeps the original conditioning. Smoke test: baseline mode on shark s0 = 40,162 Gaussians (baseline-pair range 39.2k-44.2k).
- scripts/run_2v_all.sh (new): runs 2V-a, 2V-b, side-only, baseline-exact (3 seeds) and CLIP for all five conditions in one unattended job.
- scripts/clip_sim.py: also prints a `PER_ANGLE` line (the average is still the last line, same math). scripts/eval_clip.py: adds `clip_0` ... `clip_315` and `clip_heldout` (mean without 90 and 270) to results/metrics.csv. Old rows keep these empty.
