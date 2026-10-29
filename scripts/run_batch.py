#!/usr/bin/env python3
"""
run_batch.py - run DreamGaussian (stage 1 + stage 2) on many images x seeds and log each run.

Our own runner. The authors' scripts/runall.py is left untouched because it
  - never passes `seed` or `outdir` (all runs would land in logs/ with the default seed),
  - lacks force_cuda_rast=True (needed on WSL),
  - records nothing (no time, Gaussian count, mesh size or VRAM).

The same script is used for baseline AND improved runs, so both are measured the same way:
    --tag baseline   -> outputs in dreamgaussian/logs/baseline/, rows in results/baseline_log.csv
    --tag improved --config <improved yaml>   (later)

Run INSIDE the container:
    cd /workspace/generative-3d-gaussians
    python scripts/run_batch.py --tag smoketest --images data/anya_rgba.png     # quick check
    python scripts/run_batch.py --tag baseline --seeds 0 1 2 --video            # all 8 samples
"""
import argparse
import csv
import datetime
import glob
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]   # generative-3d-gaussians/
DG = REPO / "dreamgaussian"                   # the authors' code; stages run from here


# ---------- measuring ----------

def gpu_mem_used_mib():
    """GPU memory in use right now (MiB), as nvidia-smi reports it.
    Includes Windows' own use (~950 MiB idle), so we subtract an idle reading later."""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits", "-i", "0"],
            capture_output=True, text=True, timeout=5)
        return int(out.stdout.strip().splitlines()[0])
    except Exception:
        return None


class PeakVRAM:
    """Polls nvidia-smi every 0.5 s in a background thread while a stage runs and keeps the max.
    Can miss spikes shorter than 0.5 s - same limitation as our first manual measurement."""

    def __init__(self, interval=0.5):
        self.interval = interval
        self.peak = None
        self._stop = threading.Event()

    def _loop(self):
        while not self._stop.is_set():
            m = gpu_mem_used_mib()
            if m is not None and (self.peak is None or m > self.peak):
                self.peak = m
            time.sleep(self.interval)

    def __enter__(self):
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join()


def run_stage(cmd, log_file):
    """Run one stage as a separate process (like typing it in the terminal).
    Its printout goes to log_file so the terminal stays readable.
    Returns (wall-clock seconds, exit code, peak VRAM in MiB)."""
    with open(log_file, "w") as f, PeakVRAM() as vram:
        t0 = time.perf_counter()
        code = subprocess.run(cmd, cwd=DG, stdout=f, stderr=subprocess.STDOUT).returncode
        secs = time.perf_counter() - t0
    return secs, code, vram.peak


def ply_gaussian_count(path):
    """Number of Gaussians = the 'element vertex N' line in the .ply header (one 'vertex' per Gaussian)."""
    try:
        with open(path, "rb") as f:
            for raw in f:
                line = raw.decode("ascii", errors="ignore").strip()
                if line.startswith("element vertex"):
                    return int(line.split()[-1])
                if line == "end_header":
                    break
    except FileNotFoundError:
        pass
    return None


def obj_counts(path):
    """(vertices, faces) of a mesh = number of 'v ' and 'f ' lines in the .obj file."""
    v = f = 0
    try:
        with open(path) as fh:
            for line in fh:
                if line.startswith("v "):
                    v += 1
                elif line.startswith("f "):
                    f += 1
    except FileNotFoundError:
        return None, None
    return v, f


def git_commit():
    """Short commit hash of the code that produced the run (+dirty if tracked files have uncommitted edits).
    safe.directory=* avoids the 'dubious ownership' error inside the container."""
    try:
        g = ["git", "-c", "safe.directory=*"]
        head = subprocess.run(g + ["rev-parse", "--short", "HEAD"], cwd=REPO,
                              capture_output=True, text=True, timeout=5).stdout.strip()
        dirty = subprocess.run(g + ["status", "--porcelain", "--untracked-files=no"], cwd=REPO,
                               capture_output=True, text=True, timeout=5).stdout.strip()
        return (head + ("+dirty" if dirty else "")) or "unknown"
    except Exception:
        return "unknown"


# ---------- main loop ----------

FIELDS = [
    "date", "tag", "config", "commit", "image", "seed",
    "stage1_s", "stage2_s", "total_s",
    "vram_stage1_mib", "vram_stage2_mib",      # peak minus idle reading
    "gaussians_final",                         # from stage-1 .ply
    "mesh1_v", "mesh1_f",                      # stage-1 mesh (from Gaussians)
    "final_v", "final_f",                      # stage-2 textured mesh
    "status", "extra",
]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", default="configs/image.yaml", help="config path, relative to dreamgaussian/")
    p.add_argument("--images", nargs="*", default=None,
                   help="image paths relative to dreamgaussian/ (default: every data/*_rgba.png)")
    p.add_argument("--seeds", nargs="+", type=int, default=[0])
    p.add_argument("--tag", default="baseline",
                   help="run label: outputs go to logs/<tag>/, rows are tagged with it")
    p.add_argument("--log", default=None, help="CSV path (default: results/<tag>_log.csv in the repo root)")
    p.add_argument("--video", action="store_true", help="also render a 360-degree video of each final mesh")
    p.add_argument("--extra", nargs="*", default=[],
                   help="extra key=value overrides passed to both stages, e.g. --extra elevation=-10")
    args = p.parse_args()

    images = args.images or sorted(
        os.path.relpath(f, DG) for f in glob.glob(str(DG / "data" / "*_rgba.png")))
    outdir = f"logs/{args.tag}"
    (DG / outdir).mkdir(parents=True, exist_ok=True)
    log_path = Path(args.log) if args.log else REPO / "results" / f"{args.tag}_log.csv"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not log_path.exists()

    idle = gpu_mem_used_mib()
    commit = git_commit()
    n_runs = len(images) * len(args.seeds)
    print(f"{n_runs} runs ({len(images)} images x seeds {args.seeds}) | tag={args.tag} | commit={commit}")
    print(f"Idle GPU memory before runs: {idle} MiB | outputs: dreamgaussian/{outdir}/ | log: {log_path}")

    with open(log_path, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()

        k = 0
        for img in images:
            name = Path(img).name.replace("_rgba.png", "")
            for seed in args.seeds:
                k += 1
                save = f"{name}_s{seed}"
                common = [f"input={img}", f"save_path={save}", f"outdir={outdir}",
                          f"seed={seed}", "force_cuda_rast=True", *args.extra]
                print(f"[{k}/{n_runs}] {name} seed {seed} ...", end=" ", flush=True)

                # Stage 1: Gaussians -> mesh. Stage 2 only if stage 1 worked (it reads stage 1's mesh).
                s1, c1, v1 = run_stage([sys.executable, "main.py", "--config", args.config, *common],
                                       DG / outdir / f"{save}_stage1.log")
                if c1 == 0:
                    s2, c2, v2 = run_stage([sys.executable, "main2.py", "--config", args.config, *common],
                                           DG / outdir / f"{save}_stage2.log")
                else:
                    s2, c2, v2 = None, None, None
                ok = (c1 == 0 and c2 == 0)

                if args.video and ok:   # not included in the timings
                    subprocess.run(["kire", f"{outdir}/{save}.obj", "--save_video", f"{outdir}/{save}.mp4",
                                    "--wogui", "--force_cuda_rast"],
                                   cwd=DG, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                m1v, m1f = obj_counts(DG / outdir / f"{save}_mesh.obj")
                fv, ff = obj_counts(DG / outdir / f"{save}.obj")
                net = lambda v: (v - idle) if (v is not None and idle is not None) else None

                row = {
                    "date": datetime.datetime.now().isoformat(timespec="seconds"),
                    "tag": args.tag, "config": args.config, "commit": commit,
                    "image": name, "seed": seed,
                    "stage1_s": round(s1, 1),
                    "stage2_s": round(s2, 1) if s2 is not None else None,
                    "total_s": round(s1 + s2, 1) if s2 is not None else None,
                    "vram_stage1_mib": net(v1), "vram_stage2_mib": net(v2),
                    "gaussians_final": ply_gaussian_count(DG / outdir / f"{save}_model.ply"),
                    "mesh1_v": m1v, "mesh1_f": m1f, "final_v": fv, "final_f": ff,
                    "status": "ok" if ok else f"failed(stage1={c1},stage2={c2}) see {save}_stage*.log",
                    "extra": " ".join(args.extra),
                }
                writer.writerow(row)
                fh.flush()   # write each row immediately, so a crash keeps earlier results
                print(f"{row['status']} | {row['total_s']} s | {row['gaussians_final']} Gaussians")

    print(f"Done. Results: {log_path}")


if __name__ == "__main__":
    main()
