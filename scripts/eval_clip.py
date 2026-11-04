"""
eval_clip.py — CLIP similarity for every generated mesh -> results/metrics.csv

WHERE: scripts/, run INSIDE the container from the repo root (needs nvdiffrast).
WHAT:  for each input image NAME_rgba.png, finds its meshes in the logs folder
       and scores each one with scripts/clip_sim.py (our copy of the authors'
       kiui clip_sim, fixed for transformers 5): renders 8 views at elevation 0,
       compares each with the input using CLIP ViT-bigG-14, averages (Table 1).
WHY a wrapper: the scorer handles ONE mesh; we need one CSV row per mesh so
       baseline and improved runs can be compared.

Example:
    python scripts/eval_clip.py --inputs data/gso_inputs \
        --logs dreamgaussian/logs/baseline --tag gso_baseline
Stage-1-only score (paper: 0.678) -> add  --stage 1

Resumable: rows with status 'ok' are kept and skipped; failed rows are dropped
and retried on the next run.
"""
import argparse
import csv
import glob
import os
import re
import subprocess
import sys
import time

p = argparse.ArgumentParser()
p.add_argument("--inputs", default="data/gso_inputs", help="folder with NAME_rgba.png")
p.add_argument("--logs", default="dreamgaussian/logs/baseline", help="folder with the meshes")
p.add_argument("--tag", required=True, help="label written to the CSV (e.g. gso_baseline / gso_improved)")
p.add_argument("--stage", type=int, choices=[1, 2], default=2,
               help="2 = final mesh NAME_sX.obj, 1 = coarse mesh NAME_sX_mesh.obj")
p.add_argument("--out", default="results/metrics.csv")
args = p.parse_args()

FIELDS = ["tag", "stage", "name", "seed", "mesh", "clip_sim", "seconds", "status"]
SCORER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clip_sim.py")

# --- resume: keep only successful rows, so failures get retried -------------
kept = []
if os.path.exists(args.out):
    with open(args.out, newline="") as f:
        kept = [r for r in csv.DictReader(f) if r.get("status") == "ok"]
done = {(r["tag"], r["stage"], r["mesh"]) for r in kept}

os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
out = open(args.out, "w", newline="")          # rewrite: ok rows first, new rows appended
writer = csv.DictWriter(out, fieldnames=FIELDS)
writer.writeheader()
writer.writerows(kept)
out.flush()

inputs = sorted(glob.glob(os.path.join(args.inputs, "*_rgba.png")))
if not inputs:
    sys.exit(f"No *_rgba.png found in {args.inputs}")

n_ok = n_err = 0
for img in inputs:
    name = os.path.basename(img)[: -len("_rgba.png")]

    # run_batch.py names: NAME_s0.obj (final), NAME_s0_mesh.obj (stage 1)
    candidates = sorted(glob.glob(os.path.join(args.logs, f"{name}_s*.obj")))
    if args.stage == 2:
        meshes = [m for m in candidates if re.fullmatch(rf"{re.escape(name)}_s\d+\.obj", os.path.basename(m))]
    else:
        meshes = [m for m in candidates if re.fullmatch(rf"{re.escape(name)}_s\d+_mesh\.obj", os.path.basename(m))]

    if not meshes:
        print(f"[skip] {name}: no stage-{args.stage} mesh in {args.logs}")
        continue

    for mesh in meshes:
        if (args.tag, str(args.stage), mesh) in done:
            continue
        seed = re.search(r"_s(\d+)", os.path.basename(mesh)).group(1)

        t0 = time.time()
        # --force_cuda_rast: no OpenGL in WSL (same as all our other renders)
        res = subprocess.run(
            [sys.executable, SCORER, img, mesh, "--force_cuda_rast"],
            capture_output=True, text=True,
        )
        secs = round(time.time() - t0, 1)

        # the scorer prints the average similarity as its last line
        lines = [l.strip() for l in res.stdout.strip().splitlines() if l.strip()]
        try:
            score, status = round(float(lines[-1]), 4), "ok"
            n_ok += 1
        except (IndexError, ValueError):
            score, status = "", "error"
            n_err += 1
            print(res.stderr[-1500:])  # show why (e.g. CUDA out of memory)

        writer.writerow(dict(tag=args.tag, stage=args.stage, name=name, seed=seed,
                             mesh=mesh, clip_sim=score, seconds=secs, status=status))
        out.flush()  # row saved even if the run crashes later
        print(f"{name} seed={seed}  clip_sim={score}  ({secs}s, {status})")

        if n_err >= 3 and n_ok == 0:
            out.close()
            sys.exit("Stopping: first 3 meshes all failed — fix the error above before running the rest.")

out.close()
print(f"Done -> {args.out}  ({n_ok} ok, {n_err} errors this run)")
