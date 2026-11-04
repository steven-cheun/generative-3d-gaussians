"""
image_prep.py — GSO objects -> DreamGaussian inputs, all objects at once.

WHERE: put in scripts/ and run INSIDE the container, from the repo root
       (/workspace/generative-3d-gaussians). Rendering needs nvdiffrast (kire).

Three phases (the view choice in between is done by eye — that's the rule,
not code):

  1) render  : every object folder -> render_y/0_0, 0_90, 0_180, 0_270 .png
  2) sheet   : one overview image per 5 objects (4 views side by side, labeled)
               -> pick the view with the rule, type it into objects.csv
  3) process : for every row in objects.csv with a view filled in:
               process.py (remove bg, recenter, 256x256) -> data/gso_inputs/SHORT_rgba.png

Usage:
  python scripts/image_prep.py render
  python scripts/image_prep.py sheet
  python scripts/image_prep.py process --out_dir data/gso_inputs

Defaults assume: raw GSO folders in /workspace/gso_test/NAME/ (= ~/dg/gso_test in WSL),
objects.csv at data/gso_inputs/objects.csv.
Each phase skips work that's already done, so re-running is safe.
"""
import argparse
import csv
import os
import shutil
import subprocess
import sys

VIEWS = ["0_0", "0_90", "0_180", "0_270"]

p = argparse.ArgumentParser()
p.add_argument("phase", choices=["render", "sheet", "process"])
p.add_argument("--gso_dir", default="/workspace/gso_test", help="one folder per GSO object")
p.add_argument("--csv", default="data/gso_inputs/objects.csv")
p.add_argument("--out_dir", help="REQUIRED for 'process': where SHORT_rgba.png goes (e.g. data/gso_inputs)")
p.add_argument("--sheet_dir", default="/workspace/gso_test/_sheets")
p.add_argument("--per_sheet", type=int, default=5, help="objects per overview image")
p.add_argument("--force", action="store_true", help="redo even if output exists")
args = p.parse_args()

# No default on purpose: an explicit output folder prevents pilot inputs and
# final test-set inputs from silently landing in the same place.
if args.phase == "process" and not args.out_dir:
    p.error("the 'process' phase needs --out_dir (e.g. --out_dir data/gso_inputs)")


def object_folders():
    """All GSO object folders (anything with meshes/model.obj)."""
    names = sorted(d for d in os.listdir(args.gso_dir)
                   if os.path.isfile(os.path.join(args.gso_dir, d, "meshes", "model.obj")))
    if not names:
        sys.exit(f"No GSO folders (NAME/meshes/model.obj) found in {args.gso_dir}")
    return names


# ---------------------------------------------------------------- 1) render
def render():
    for name in object_folders():
        d = os.path.join(args.gso_dir, name)
        out = os.path.join(d, "render_y")
        if not args.force and all(os.path.exists(os.path.join(out, v + ".png")) for v in VIEWS):
            print(f"[skip] {name}: already rendered")
            continue

        # model.mtl expects texture.png NEXT TO the mesh; GSO stores it elsewhere
        # -> without this copy the render is plain grey.
        tex = os.path.join(d, "materials", "textures", "texture.png")
        if os.path.exists(tex):
            shutil.copy(tex, os.path.join(d, "meshes", "texture.png"))
        else:
            print(f"[warn] {name}: no texture.png -> render will be grey; consider another object")

        # Locked camera setup: 4 azimuths 90° apart, elevation 0°, 512x512.
        # --front_dir=-y because GSO is Z-up and kire assumes Y-up (keep the '=').
        cmd = ["kire", "meshes/model.obj", "--save", "render_y", "--num_azimuth", "4",
               "--W", "512", "--H", "512", "--wogui", "--force_cuda_rast", "--front_dir=-y"]
        r = subprocess.run(cmd, cwd=d, capture_output=True, text=True)
        status = "ok" if r.returncode == 0 else "FAILED"
        print(f"[{status}] {name}")
        if r.returncode != 0:
            print(r.stderr[-800:])


# ----------------------------------------------------------------- 2) sheet
def sheet():
    from PIL import Image, ImageDraw  # Pillow is in the container

    T = 256          # thumbnail size
    LABEL_H = 28     # space for text above each row
    names = [n for n in object_folders()
             if all(os.path.exists(os.path.join(args.gso_dir, n, "render_y", v + ".png")) for v in VIEWS)]
    if not names:
        sys.exit("Nothing rendered yet -> run the 'render' phase first")
    os.makedirs(args.sheet_dir, exist_ok=True)

    for start in range(0, len(names), args.per_sheet):
        chunk = names[start:start + args.per_sheet]
        sheet_img = Image.new("RGB", (4 * T, len(chunk) * (T + LABEL_H)), "white")
        draw = ImageDraw.Draw(sheet_img)
        for row, name in enumerate(chunk):
            y = row * (T + LABEL_H)
            draw.text((6, y + 8), name, fill="black")
            for col, v in enumerate(VIEWS):
                im = Image.open(os.path.join(args.gso_dir, name, "render_y", v + ".png")).convert("RGBA")
                im = im.resize((T, T))
                bg = Image.new("RGBA", (T, T), (235, 235, 235, 255))  # light grey shows transparent edges
                bg.alpha_composite(im)
                sheet_img.paste(bg.convert("RGB"), (col * T, y + LABEL_H))
                draw.text((col * T + 6, y + LABEL_H + 6), v, fill="red")
        path = os.path.join(args.sheet_dir, f"sheet_{start // args.per_sheet + 1:02d}.png")
        sheet_img.save(path)
        print(f"wrote {path}  ({', '.join(chunk)})")
    print("Now: apply the view rule, fill the 'view' column in objects.csv, then run 'process'.")


# --------------------------------------------------------------- 3) process
def process():
    if not os.path.exists(args.csv):
        sys.exit(f"{args.csv} not found")
    with open(args.csv, newline="") as f:
        rows = list(csv.DictReader(f))
    os.makedirs(args.out_dir, exist_ok=True)
    dg_dir = os.path.abspath("dreamgaussian")  # process.py lives here

    for row in rows:
        short, gso, view = row["short_name"].strip(), row["gso_name"].strip(), row["view"].strip()
        if not view:
            print(f"[skip] {short}: no view chosen yet")
            continue
        if view not in VIEWS:
            print(f"[skip] {short}: view '{view}' is not one of {VIEWS}")
            continue
        final = os.path.join(args.out_dir, f"{short}_rgba.png")
        if os.path.exists(final) and not args.force:
            print(f"[skip] {short}: {final} exists")
            continue

        src = os.path.join(args.gso_dir, gso, "render_y", view + ".png")
        if not os.path.exists(src):
            print(f"[skip] {short}: {src} missing (folder name typo, or not rendered?)")
            continue

        # process.py writes <input>_rgba.png next to the input (bg removed, centered, 256x256).
        # The 'libcublasLt.so.13 ... CPU' warning is harmless (CPU fallback, ~1-2 s).
        r = subprocess.run([sys.executable, "process.py", os.path.abspath(src)],
                           cwd=dg_dir, capture_output=True, text=True)
        made = src[:-len(".png")] + "_rgba.png"
        if r.returncode != 0 or not os.path.exists(made):
            print(f"[FAILED] {short}\n{r.stderr[-800:]}")
            continue
        # name MUST end in _rgba.png: run_batch.py uses the part before it as the run name
        shutil.copy(made, final)
        print(f"[ok] {short} <- {gso}/{view}")

    print(f"Check every image in {args.out_dir} (bg gone, centered, nothing cut off), then commit.")


{"render": render, "sheet": sheet, "process": process}[args.phase]()
