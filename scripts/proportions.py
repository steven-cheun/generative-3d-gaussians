"""
proportions.py — proportion error of every generated mesh vs the real GSO scan
                 -> results/proportions.csv   (primary metric for the two-view experiment)

WHERE: scripts/, run INSIDE the container from the repo root. CPU only, numpy only, ~1 min.
WHAT:  for each mesh NAME_sX.obj in dreamgaussian/logs/<tag>/ (objects in objects.csv),
       compares the bounding-box PROPORTIONS with the scan <gso_dir>/<gso_name>/meshes/model.obj:
         width / height  and  depth / height   (dividing by height cancels the unknown scale)
WHY:   STRETCH = wrong size of the dimension hidden from the input camera (head-on shark too
       short, face-on cartridge too thick). CLIP can't see it; face counts mix size and bumpiness.
       Proportions ignore size, so a smaller-but-correct shark and a bigger-but-correct shark
       score the same.

AXES (checked in the code, 2026-11-14):
  ours (DreamGaussian): input camera at +z, y up      -> width = x, height = y, depth = z
  GSO scan (raw .obj):  Z-up, front facing -y          -> width = x, height = z, depth = y
                        (kire --front_dir=-y maps (x, y, z) -> (x, z, -y))
  side-only runs:       DreamGaussian's "front" is the scan's 90-degree side
                        -> width and depth of the scan swap (--side_tags)

ERROR: ratio = (our proportion) / (true proportion): 1.00 = perfect, 0.5 = half as long, 2 = twice
       as thick. Error per axis = |ln(ratio)| (symmetric: 2x too thick and 2x too thin are equally
       wrong). prop_err = mean of the width and depth errors.
       Extents use the 0.5th-99.5th percentile of vertex coordinates so one stray floater can't
       stretch the box.

Usage:
  python scripts/proportions.py
  python scripts/proportions.py --tags gso_bpair gso_2va gso_2vb
"""
import argparse
import csv
import glob
import math
import os
import re
import sys

import numpy as np

p = argparse.ArgumentParser()
p.add_argument("--tags", nargs="+",
               default=["baseline", "gso_bexact", "gso_bpair", "gso_2va", "gso_2vb", "gso_side"],
               help="run tags = folders in dreamgaussian/logs/ ('baseline' = the original GSO baseline)")
p.add_argument("--side_tags", nargs="*", default=["gso_side"],
               help="tags whose input was the 90-degree side view (width/depth of the scan swap)")
p.add_argument("--logs_root", default="dreamgaussian/logs")
p.add_argument("--csv", default="data/gso_inputs/objects.csv", help="short_name -> gso_name")
p.add_argument("--gso_dir", default="/workspace/gso_test")
p.add_argument("--out", default="results/proportions.csv")
p.add_argument("--pct", type=float, default=0.5, help="trim this percent at each end of each axis")
args = p.parse_args()


def obj_vertices(path):
    """All 'v x y z' lines of an .obj as an [N, 3] array (no faces, textures or normals needed)."""
    with open(path) as f:
        v = [line.split()[1:4] for line in f if line.startswith("v ")]
    return np.asarray(v, dtype=np.float64)


def extents(v):
    """Robust size along x, y, z: distance between the low and high percentile."""
    lo = np.percentile(v, args.pct, axis=0)
    hi = np.percentile(v, 100 - args.pct, axis=0)
    return hi - lo


def true_whd(gso_name):
    """(width, height, depth) of the real scan, in DreamGaussian's naming."""
    path = os.path.join(args.gso_dir, gso_name, "meshes", "model.obj")
    ex, ey, ez = extents(obj_vertices(path))
    return ex, ez, ey          # GSO: width = x, height = z, depth = y


with open(args.csv, newline="") as f:
    objects = {r["short_name"].strip(): r["gso_name"].strip() for r in csv.DictReader(f)}

# ground truth once per object, printed first so the axis mapping can be checked by eye
truth = {}
print("Ground truth (scan): width/height, depth/height")
for name, gso in objects.items():
    try:
        w, h, d = true_whd(gso)
    except FileNotFoundError as e:
        sys.exit(f"scan not found: {e}")
    truth[name] = (w / h, d / h)
    print(f"  {name:12s} w/h {w / h:5.2f}   d/h {d / h:5.2f}")
print("  -> check: cartridge and headset_box d/h small (thin); shark, orca, turtle d/h large (long)\n")

FIELDS = ["tag", "name", "seed", "mesh", "true_w_h", "true_d_h", "our_w_h", "our_d_h",
          "ratio_w", "ratio_d", "err_w", "err_d", "prop_err"]
rows = []
for tag in args.tags:
    folder = os.path.join(args.logs_root, tag)
    n = 0
    for name in objects:
        for mesh in sorted(glob.glob(os.path.join(folder, f"{name}_s*.obj"))):
            m = re.fullmatch(rf"{re.escape(name)}_s(\d+)\.obj", os.path.basename(mesh))
            if not m:            # skip NAME_sX_mesh.obj (stage-1 mesh; same geometry anyway)
                continue
            ex, ey, ez = extents(obj_vertices(mesh))
            our_w, our_d = ex / ey, ez / ey             # ours: width = x, height = y, depth = z
            tw, td = truth[name]
            if tag in args.side_tags:                   # input was the side: scan's w and d swap
                tw, td = td, tw
            rw, rd = our_w / tw, our_d / td
            ew, ed = abs(math.log(rw)), abs(math.log(rd))
            rows.append(dict(tag=tag, name=name, seed=int(m.group(1)), mesh=mesh,
                             true_w_h=round(tw, 4), true_d_h=round(td, 4),
                             our_w_h=round(our_w, 4), our_d_h=round(our_d, 4),
                             ratio_w=round(rw, 4), ratio_d=round(rd, 4),
                             err_w=round(ew, 4), err_d=round(ed, 4), prop_err=round((ew + ed) / 2, 4)))
            n += 1
    print(f"[{tag}] {n} meshes" + ("" if n else f"  (none found in {folder})"))

os.makedirs(os.path.dirname(args.out), exist_ok=True)
with open(args.out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)
print(f"-> {args.out} ({len(rows)} rows)\n")

# quick summary: mean over seeds
def mean(v):
    return sum(v) / len(v) if v else float("nan")

tags = [t for t in args.tags if any(r["tag"] == t for r in rows)]
short = lambda t: t.replace("gso_", "")
print(f"{'prop_err (lower = better)':26s}" + "".join(f"{short(t):>9s}" for t in tags))
print(f"{'ALL':26s}" + "".join(f"{mean([r['prop_err'] for r in rows if r['tag'] == t]):9.3f}" for t in tags))
for name in objects:
    print(f"{name:26s}" + "".join(
        f"{mean([r['prop_err'] for r in rows if r['tag'] == t and r['name'] == name]):9.3f}" for t in tags))
print(f"\n{'depth ratio (1.00 = right)':26s}" + "".join(f"{short(t):>9s}" for t in tags))
for name in objects:
    print(f"{name:26s}" + "".join(
        f"{mean([r['ratio_d'] for r in rows if r['tag'] == t and r['name'] == name]):9.2f}" for t in tags))
