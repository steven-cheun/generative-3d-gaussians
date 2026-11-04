"""
eval_clip.py — CLIP similarity for every generated mesh -> results/metrics.csv

WHERE: put in scripts/ and run INSIDE the container (needs nvdiffrast + kiui,
       which only the DreamGaussian container has).
WHAT:  for each input image NAME_rgba.png, finds its meshes in the logs folder
       and calls the authors' evaluator once per mesh:
           python -m kiui.cli.clip_sim <NAME_rgba.png> <mesh.obj>
       (this is the command from the DreamGaussian README; it renders the mesh
       and compares it with the input using CLIP ViT-bigG-14, like Table 1).
WHY a wrapper: the authors' command scores ONE mesh. We need ~60 (20 objects x
       3 seeds), one CSV row each, so baseline and improved runs can be compared.

Example (from the repo root, in the container):
    python scripts/eval_clip.py --inputs data/gso_inputs \
        --logs dreamgaussian/logs/baseline --tag baseline
Stage-1-only score (paper: 0.678) -> add  --stage 1

Resumable: rows already in the CSV are skipped, so you can stop and restart.
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
p.add_argument("--tag", default="baseline", help="label written to the CSV (baseline / improved)")
p.add_argument("--stage", type=int, choices=[1, 2], default=2,
               help="2 = final mesh NAME*.obj, 1 = coarse mesh NAME*_mesh.obj")
p.add_argument("--out", default="results/metrics.csv")
args = p.parse_args()

FIELDS = ["tag", "stage", "name", "seed", "mesh", "clip_sim", "seconds", "status"]

# --- resume: remember which meshes are already scored ---------------------
done = set()
if os.path.exists(args.out):
    with open(args.out, newline="") as f:
        for row in csv.DictReader(f):
            done.add((row["tag"], row["stage"], row["mesh"]))

new_file = not os.path.exists(args.out)
os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
out = open(args.out, "a", newline="")
writer = csv.DictWriter(out, fieldnames=FIELDS)
if new_file:
    writer.writeheader()

inputs = sorted(glob.glob(os.path.join(args.inputs, "*_rgba.png")))
if not inputs:
    sys.exit(f"No *_rgba.png found in {args.inputs}")

for img in inputs:
    name = os.path.basename(img)[: -len("_rgba.png")]

    # Stage 2 writes NAME....obj, stage 1 writes NAME..._mesh.obj.
    # CHECK the real file names in your logs folder once (ls) — if the seed is
    # written differently, adjust the seed regex below.
    candidates = sorted(glob.glob(os.path.join(args.logs, f"{name}*.obj")))
    if args.stage == 2:
        meshes = [m for m in candidates if not m.endswith("_mesh.obj")]
    else:
        meshes = [m for m in candidates if m.endswith("_mesh.obj")]
    # avoid "shark" also matching "shark2": the char after NAME must not be a letter/digit
    meshes = [m for m in meshes
              if not re.match(r"[A-Za-z0-9]", os.path.basename(m)[len(name):len(name) + 1] or "_")]

    if not meshes:
        print(f"[skip] {name}: no stage-{args.stage} mesh in {args.logs}")
        continue

    for mesh in meshes:
        key = (args.tag, str(args.stage), mesh)
        if key in done:
            continue
        seed_match = re.search(r"(?:seed|_s)(\d+)", os.path.basename(mesh))
        seed = seed_match.group(1) if seed_match else ""

        t0 = time.time()
        res = subprocess.run(
            [sys.executable, "-m", "kiui.cli.clip_sim", img, mesh],
            capture_output=True, text=True,
        )
        secs = round(time.time() - t0, 1)

        # The evaluator prints the similarity; take the last number it printed.
        numbers = re.findall(r"\d+\.\d+", res.stdout)
        if res.returncode == 0 and numbers:
            score, status = float(numbers[-1]), "ok"
        else:
            score, status = "", "error"
            print(res.stdout[-500:], res.stderr[-1500:])  # show why (e.g. CUDA out of memory)

        writer.writerow(dict(tag=args.tag, stage=args.stage, name=name, seed=seed,
                             mesh=mesh, clip_sim=score, seconds=secs, status=status))
        out.flush()  # row saved even if the run crashes later
        print(f"{name} seed={seed or '?'}  clip_sim={score}  ({secs}s, {status})")

out.close()
print(f"Done -> {args.out}")
