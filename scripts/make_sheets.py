"""
make_sheets.py - contact sheets for the visual check (two-view experiment + baseline seeds)

WHERE: scripts/, run from the repo root on CPU (OpenCV + numpy only, about 30 s).
WHAT:  grabs the 8 CLIP-eval angles (0 to 315 in 45 degree steps; frame = angle / 3, since
       every turntable video is 120 frames = 3 degrees per frame) and lays them out in a grid:
         seeds_<name>.png    original baseline seeds 0 / 1 / 2 of the 6 hard cases
         compare_<name>.png  seed 0, baseline / bpair / 2V-a / 2V-b (rows), from the
                             4-panel comparison videos made by scripts/compare_videos.py
WHY:   the visual check (failure tags, MISS, usable angles) needs every condition at the same
       angles side by side. Same method as the failure-notes Part 3 sheets.

INPUTS (videos are big: never commit them; keep them in excluded folders):
  --seed0_dir    <name>_s0.mp4 of the original baseline   (default data/renders/gso_videos)
  --seeds_dir    <name>_s1.mp4, <name>_s2.mp4             (Drive videos_baseline_hard_seeds/)
  --compare_dir  <name>_compare_s0.mp4                    (Drive videos_compare/)
OUTPUT: --out (default data/renders/sheets, excluded from git)

Usage:
  python scripts/make_sheets.py --seeds_dir docs/videos_baseline_hard_seeds --compare_dir docs/videos_compare
"""
import argparse
from pathlib import Path

import cv2
import numpy as np

p = argparse.ArgumentParser()
p.add_argument("--seed0_dir", default="data/renders/gso_videos")
p.add_argument("--seeds_dir", default="data/renders/videos_baseline_hard_seeds")
p.add_argument("--compare_dir", default="data/renders/videos_compare")
p.add_argument("--out", default="data/renders/sheets")
args = p.parse_args()

ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]
HARD_CASES = ["headset_box", "cartridge", "turtle", "orca", "shark", "cats"]
CONDITIONS = ["baseline", "bpair", "2V-a", "2V-b"]   # panel order in the comparison videos
FONT = cv2.FONT_HERSHEY_SIMPLEX
OUT = Path(args.out)
OUT.mkdir(parents=True, exist_ok=True)


def frames(path):
    """The 8 eval-angle frames of a 120-frame turntable video."""
    cap = cv2.VideoCapture(str(path))
    out = []
    for a in ANGLES:
        cap.set(cv2.CAP_PROP_POS_FRAMES, a // 3)
        ok, f = cap.read()
        assert ok, f"could not read frame {a // 3} of {path}"
        out.append(f)
    return out


def with_title(img, text, h=28):
    """Add a white strip with a text label above an image."""
    bar = np.full((h, img.shape[1], 3), 255, np.uint8)
    cv2.putText(bar, text, (6, h - 9), FONT, 0.55, (40, 40, 40), 1, cv2.LINE_AA)
    return np.vstack([bar, img])


def grid(rows, row_names, title):
    """rows: one list of 8 equal-size images per row. Adds angle headers and row names."""
    w = rows[0][0].shape[1]
    header = [with_title(np.full((0, w, 3), 255, np.uint8), f"{a} deg") for a in ANGLES]
    lines = [np.hstack([np.full((header[0].shape[0], 150, 3), 255, np.uint8)] + header)]
    for name, imgs in zip(row_names, rows):
        tag = np.full((imgs[0].shape[0], 150, 3), 255, np.uint8)
        cv2.putText(tag, name, (6, imgs[0].shape[0] // 2), FONT, 0.6, (40, 40, 40), 1, cv2.LINE_AA)
        lines.append(np.hstack([tag] + imgs))
    return with_title(np.vstack(lines), title, 34)


# 1) Baseline seeds 0 / 1 / 2 of the 6 hard cases
for name in HARD_CASES:
    vids = [Path(args.seed0_dir) / f"{name}_s0.mp4"] + \
           [Path(args.seeds_dir) / f"{name}_s{s}.mp4" for s in (1, 2)]
    rows = [[cv2.resize(f, (240, 240), interpolation=cv2.INTER_AREA) for f in frames(v)] for v in vids]
    cv2.imwrite(str(OUT / f"seeds_{name}.png"),
                grid(rows, ["seed 0", "seed 1", "seed 2"], f"{name}: baseline, 3 seeds"))

# 2) Comparison videos: each frame holds 4 panels side by side -> one row per condition
for v in sorted(Path(args.compare_dir).glob("*_compare_s0.mp4")):
    name = v.name.replace("_compare_s0.mp4", "")
    fs = frames(v)
    w = fs[0].shape[1] // len(CONDITIONS)
    rows = [[cv2.resize(f[:, i * w:(i + 1) * w], (210, 234), interpolation=cv2.INTER_AREA) for f in fs]
            for i in range(len(CONDITIONS))]
    cv2.imwrite(str(OUT / f"compare_{name}.png"),
                grid(rows, CONDITIONS, f"{name}: seed 0 (labels in each panel = prop. error)"))

print(f"{len(list(OUT.glob('*.png')))} sheets in {OUT}")
