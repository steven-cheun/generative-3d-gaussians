"""
pair_prep.py — GSO renders -> inputs for the two-view (2V) experiment.

WHERE: scripts/, run INSIDE the container from the repo root
       (/workspace/generative-3d-gaussians). CPU only, takes seconds.
NEEDS: for every object in objects.csv, in <gso_dir>/<gso_name>/:
         render_y/<view>.png  color renders  (image_prep.py render)
         render_d/<view>.png  depth renders  (kire ... --mode depth --save render_d)

WHY a new script instead of process.py:
  1) Exact outlines. process.py guesses the background with rembg, which cuts
     white parts that touch the white background (Yoshi's eyes at 0_90 became
     holes). The depth render comes from the scan itself: background = 0,
     object > 0, so the outline is exact.
  2) One shared zoom for a pair. process.py zooms every image on its own so the
     object fills 80% of the frame. For a front/side pair that breaks the
     geometry: a head-on shark gets zoomed ~2x, its side view barely, so the two
     photos disagree about the object's size. Here both photos of a pair get the
     SAME zoom, chosen so the larger of the two outlines fills 80%.

Outputs (256x256 RGBA, same naming rules as before):
  --out_single  <short>_rgba.png               side-only control: side view, own zoom
                                                (= what process.py does, but exact outline)
  --out_exact   <short>_rgba.png               baseline-exact: front view, own zoom, exact outline
                                                (differs from the original baseline input ONLY in
                                                 the outline -> measures what rembg's mistakes cost)
  --out_pair    <short>_rgba.png               front view, shared zoom
                <short>_side.png               side view,  shared zoom
                                                (NOT *_rgba.png, so run_batch.py doesn't
                                                 treat it as a separate object)
                _check.png                     every pair on dark grey, for checking by eye

Usage:
  python scripts/pair_prep.py
  python scripts/pair_prep.py --side 0_90 --out_pair data/gso_inputs_2v --out_single data/gso_inputs_side
"""
import argparse
import csv
import os
import sys

import cv2
import numpy as np

p = argparse.ArgumentParser()
p.add_argument("--gso_dir", default="/workspace/gso_test", help="one folder per GSO object")
p.add_argument("--csv", default="data/gso_inputs/objects.csv", help="short_name + gso_name per object")
p.add_argument("--front", default="0_0", help="front view (the baseline input)")
p.add_argument("--side", default="0_90", help="second view; 0_90 = camera 90 deg to the viewer's right")
p.add_argument("--out_pair", default="data/gso_inputs_2v")
p.add_argument("--out_single", default="data/gso_inputs_side")
p.add_argument("--out_exact", default="data/gso_inputs_exact")
p.add_argument("--size", type=int, default=256, help="output size (same as process.py)")
p.add_argument("--border_ratio", type=float, default=0.2, help="same as process.py: object fills 80%%")
args = p.parse_args()


def load_rgba(obj_dir, view):
    """Color render + exact outline from the depth render -> uint8 RGBA [H, W, 4]."""
    color_path = os.path.join(obj_dir, "render_y", view + ".png")
    depth_path = os.path.join(obj_dir, "render_d", view + ".png")
    for path in (color_path, depth_path):
        if not os.path.exists(path):
            raise FileNotFoundError(path)
    color = cv2.imread(color_path, cv2.IMREAD_COLOR)        # BGR, like process.py
    depth = cv2.imread(depth_path, cv2.IMREAD_GRAYSCALE)
    if color.shape[:2] != depth.shape[:2]:
        raise ValueError(f"size mismatch: {color_path} vs {depth_path}")
    # kire's depth mode: background pixels are exactly 0, object pixels are > 0
    # (depth is divided by its max, and the nearest surface is still far from 0).
    mask = depth > 0
    if not mask.any():
        raise ValueError(f"empty outline in {depth_path}")
    rgba = np.dstack([color, (mask * 255).astype(np.uint8)])
    rgba[~mask, :3] = 0                                      # keep see-through pixels clean
    return rgba


def bbox(rgba):
    """(row_min, row_max, col_min, col_max) of the object, same convention as process.py."""
    rows, cols = np.nonzero(rgba[..., 3])
    return rows.min(), rows.max(), cols.min(), cols.max()


def place(rgba, scale):
    """Crop to the object, resize by `scale`, paste centered on an empty size x size canvas.
    Mirrors process.py's recenter step, but the zoom is passed in instead of computed."""
    r0, r1, c0, c1 = bbox(rgba)
    h, w = r1 - r0, c1 - c0
    h2, w2 = int(h * scale), int(w * scale)
    if max(h2, w2) > args.size:
        raise ValueError(f"object does not fit: {h2}x{w2} > {args.size}")
    out = np.zeros((args.size, args.size, 4), dtype=np.uint8)
    top, left = (args.size - h2) // 2, (args.size - w2) // 2
    out[top:top + h2, left:left + w2] = cv2.resize(rgba[r0:r1, c0:c1], (w2, h2), interpolation=cv2.INTER_AREA)
    return out


def zoom_for(*images):
    """One zoom so the LARGEST outline among `images` fills (1 - border_ratio) of the frame."""
    desired = int(args.size * (1 - args.border_ratio))
    longest = max(max(r1 - r0, c1 - c0) for r0, r1, c0, c1 in (bbox(im) for im in images))
    return desired / longest


def on_grey(rgba):
    """For the check sheet: composite on dark grey so see-through holes show up
    (on white they'd be invisible - that's how the Yoshi eye holes hid)."""
    a = rgba[..., 3:] / 255.0
    return (rgba[..., :3] * a + 60 * (1 - a)).astype(np.uint8)


if not os.path.exists(args.csv):
    sys.exit(f"{args.csv} not found")
with open(args.csv, newline="") as f:
    rows = list(csv.DictReader(f))
os.makedirs(args.out_pair, exist_ok=True)
os.makedirs(args.out_single, exist_ok=True)
os.makedirs(args.out_exact, exist_ok=True)

sheet_rows, failed = [], 0
for row in rows:
    short, gso = row["short_name"].strip(), row["gso_name"].strip()
    obj_dir = os.path.join(args.gso_dir, gso)
    try:
        front = load_rgba(obj_dir, args.front)
        side = load_rgba(obj_dir, args.side)

        # side-only control: own zoom, exactly like a normal single-image input
        single = place(side, zoom_for(side))
        # baseline-exact: front, own zoom (like the original baseline), exact outline
        exact = place(front, zoom_for(front))
        # pair: one shared zoom for both photos
        s = zoom_for(front, side)
        pair_front, pair_side = place(front, s), place(side, s)
    except (FileNotFoundError, ValueError) as e:
        print(f"[FAILED] {short}: {e}")
        failed += 1
        continue

    cv2.imwrite(os.path.join(args.out_single, f"{short}_rgba.png"), single)
    cv2.imwrite(os.path.join(args.out_exact, f"{short}_rgba.png"), exact)
    cv2.imwrite(os.path.join(args.out_pair, f"{short}_rgba.png"), pair_front)
    cv2.imwrite(os.path.join(args.out_pair, f"{short}_side.png"), pair_side)

    # how much the shared zoom shrank the front vs. a normal single-image input
    front_alone = zoom_for(front)
    print(f"[ok] {short:12s} shared zoom {s:.2f} | front at {s / front_alone:4.0%} of its usual size")

    label = np.full((20, args.size * 4, 3), 255, np.uint8)
    cv2.putText(label, f"{short}: pair front | pair side | side-only | baseline-exact", (4, 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
    sheet_rows.append(np.vstack([label, np.hstack([on_grey(pair_front), on_grey(pair_side), on_grey(single), on_grey(exact)])]))

if sheet_rows:
    cv2.imwrite(os.path.join(args.out_pair, "_check.png"), np.vstack(sheet_rows))
    print(f"Check {args.out_pair}/_check.png by eye (holes show as grey), then commit.")
if failed:
    sys.exit(f"{failed} object(s) failed")
