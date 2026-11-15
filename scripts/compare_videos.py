"""
compare_videos.py — one side-by-side 360-degree video per object (seed 0):
    original baseline | control (bpair) | 2V-a | 2V-b
-> dreamgaussian/logs/compare/<name>_compare_s0.mp4

WHERE: INSIDE the container, from the repo root (needs imageio + imageio-ffmpeg, as kire does).
WHY:   for slides (before/after) and Hector's visual MISS check. All four panels start at the
       same angle (the front photo) and turn the same way, so frame k shows the same view in
       every panel. Side-only is left out: its video starts at the side photo (90 degrees off).
Labels show the condition and that run's proportion error (results/proportions.csv, lower = better).
"""
import argparse
import csv
import os

import cv2
import imageio.v2 as imageio
import numpy as np

p = argparse.ArgumentParser()
p.add_argument("--seed", type=int, default=0)
p.add_argument("--logs_root", default="dreamgaussian/logs")
p.add_argument("--out", default="dreamgaussian/logs/compare")
p.add_argument("--csv", default="data/gso_inputs/objects.csv")
p.add_argument("--props", default="results/proportions.csv")
p.add_argument("--size", type=int, default=384, help="panel size in pixels")
args = p.parse_args()

PANELS = [("baseline", "original baseline"), ("gso_bpair", "control (bpair)"),
          ("gso_2va", "2V-a"), ("gso_2vb", "2V-b (nearest photo)")]

with open(args.csv, newline="") as f:
    objects = [r["short_name"].strip() for r in csv.DictReader(f)]
prop = {}
if os.path.exists(args.props):
    with open(args.props, newline="") as f:
        for r in csv.DictReader(f):
            if int(r["seed"]) == args.seed:
                prop[(r["tag"], r["name"])] = float(r["prop_err"])
os.makedirs(args.out, exist_ok=True)


def label(frame, text, sub):
    """Square panel with a white title bar on top."""
    img = cv2.resize(frame[..., :3], (args.size, args.size), interpolation=cv2.INTER_AREA)
    bar = np.full((44, args.size, 3), 255, np.uint8)
    cv2.putText(bar, text, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(bar, sub, (6, 37), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (90, 90, 90), 1, cv2.LINE_AA)
    return np.vstack([bar, img])


for name in objects:
    paths = [os.path.join(args.logs_root, tag, f"{name}_s{args.seed}.mp4") for tag, _ in PANELS]
    missing = [pth for pth in paths if not os.path.exists(pth)]
    if missing:
        print(f"[skip] {name}: missing {missing}")
        continue
    videos = [imageio.mimread(pth, memtest=False) for pth in paths]
    n = min(len(v) for v in videos)
    out_path = os.path.join(args.out, f"{name}_compare_s{args.seed}.mp4")
    frames = []
    for i in range(n):
        row = []
        for (tag, title), v in zip(PANELS, videos):
            e = prop.get((tag, name))
            sub = f"{name} s{args.seed} | prop. error {e:.3f}" if e is not None else f"{name} s{args.seed}"
            row.append(label(np.asarray(v[i]), title, sub))
        frames.append(np.hstack(row))
    imageio.mimwrite(out_path, frames, fps=30, quality=8, macro_block_size=1)
    print(f"[ok] {out_path} ({n} frames)")
