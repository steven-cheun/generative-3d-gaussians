# CS 469 Final Project: DreamGaussian

Repo: https://github.com/steven-cheun/generative-3d-gaussians

Two-person project. We reproduce DreamGaussian (Tang et al., ICLR 2024, arXiv 2309.16653), design and test one improvement, and submit four things: a PowerPoint deck, a Word report (IEEE template), all code and Jupyter notebooks as executable files, and a link to the recorded Zoom presentation. Final deadline: Tue Dec 1, 11:59 pm PT.

Read STATUS.md (state, decisions, agenda) and TASKS.md (every open to-do) first every session. Both are imported below. The original Oct 16 plan is `docs/next-steps.md`; it was written from Steven's side, so "Me" there means Steven and "Partner" means Hector. Live tasks are tracked in TASKS.md, not in next-steps.md.

@docs/STATUS.md
@docs/TASKS.md

## Who owns what

- Steven: ML engineer and technical lead. GPU environment, baseline reproduction, code map, the improvement (his idea, his call), all final generation runs on his RTX 5070. Notebooks 01_setup_check, 02_baseline, 03_improved. Slides 5 to 8.
- Hector: data, evaluation, research communication. GSO test set and prompts, input image renders, evaluation notebook, failure-case analysis, novelty check, tables and figures, intro/background/lit review, IEEE formatting. Notebooks 04_evaluation, 05_failures. Slides 1 to 4.
- If a task crosses lanes or has no owner, say so and log it instead of quietly doing the other person's part. Both of us must be able to answer questions on every slide.

## Ground rules

1. Commit 1 is the authors' code, untouched. Never rewrite history at or before it.
2. Mark every edit to an upstream file with `# CS469:` (or `// CS469:`) and a one-line reason, so `git grep "CS469:"` lists every change for the report.
3. The improvement goes behind a config flag that defaults to off (for example `cs469_<name>: False` in the yaml). Baseline and improved runs come from the same commit and differ only in that flag.
4. All final generation runs and all timings come from Steven's RTX 5070. Other machines and Colab are for debugging. CLIP scoring may run on any machine, as long as the model, views, and preprocessing are identical for every method.
5. Generation facts go in `results/runs.csv` (Steven). Scores go in `results/scores.csv` (Hector). Both are keyed by `run_id`. If a number is not in one of these files, it does not go in the report or slides.
6. Fixed, logged seeds. Same object list and same seeds for baseline and improved.
7. Once the baseline is measured, do not upgrade torch, CUDA, diffusers, or model weights. Pinned versions live in `docker/constraints.txt`.
8. Never commit meshes, renders, videos, `.ply` checkpoints, Hugging Face caches, or raw GSO data. Those go in the shared folder.
9. Ask before deleting files, force-pushing, or changing anything under `dreamgaussian/diff-gaussian-rasterization/`.

## Sharing: GitHub vs the shared folder

- GitHub holds code, notebooks, configs, CSVs, docs, and the small input images (`data/inputs/`, about 30 PNGs). Anything the grader needs to run the notebooks should live here if it's small.
- The shared folder (synced to both computers by its desktop app) holds everything big or binary: raw GSO data, generated outputs, figures for slides, `report.docx`, `talk.pptx`.
- Git rhythm: `git pull` before starting, small commits, push when a piece works. We mostly touch different files. STATUS.md and TASKS.md are the exceptions, so pull right before editing them.
- Generate outputs on local disk, then copy finished runs into the shared folder. Sync apps handle thousands of files changing mid-run badly.

Shared folder layout:

```
CS469-DreamGaussian/
  gso_raw/                                  GSO downloads
  outputs/<method>/<object_id>/seed<k>/     mesh + texture, 8 renders, 360 video
  gt_renders/<object_id>/                   GSO ground-truth renders at the 8 eval views
  figures/
  report.docx
  talk.pptx
```

## Two environments

DreamGaussian needs CUDA and compiled extensions. Data prep and evaluation do not. Keep them separate so neither person blocks the other and the grader can run the evaluation notebooks without a GPU.

| | GPU env | Analysis env |
|---|---|---|
| Who | Steven | Hector, and the grader |
| Machine | RTX 5070, Windows + WSL2 | Any machine, including a laptop with no NVIDIA GPU |
| Used for | notebooks 01 to 03, generation, rendering outputs | test set, GSO renders, notebooks 04 and 05, figures |
| Setup | "GPU env setup" below | `requirements-analysis.txt` in a plain Python venv; Blender installed separately |

Analysis env rules:

- Code must run on CPU. Use CUDA only if `torch.cuda.is_available()`.
- Notebooks run top to bottom from a fresh clone, list their input paths in the first cell, and save their outputs. Restart and run all before every commit.
- Iterate with a small CLIP model on CPU. Final scores use the locked model (see "Results files"), run once on a GPU (Colab or Steven's machine) if CPU is too slow.
- GSO renders: `blender --background --python scripts/cs469/render_gso.py -- <args>`.

## GPU env setup (Steven's machine)

- RTX 5070 is Blackwell (compute capability 12.0 / sm_120). It needs PyTorch 2.7 or newer built against CUDA 12.8 or newer. Older CUDA toolkits cannot compile for sm_120.
- Docker is optional. A plain venv inside WSL2 plus the CUDA 12.8 toolkit (for nvcc) works too. Record the choice in STATUS.md.
- Clone into the WSL filesystem (`~/generative-3d-gaussians`), not under `/mnt/c`. Builds are much faster.
- Upstream was only tested on torch 1.12 / CUDA 11.6 and torch 2.1 / CUDA 12.1. Expect dependency drift. `dreamgaussian/requirements.lock.txt` shows the authors' versions.

```bash
# torch first: any release >= 2.7 from the cu128 (or newer) wheel index, or a pytorch/pytorch:*-cuda12.8-cudnn9-devel image
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.get_arch_list())"   # must list sm_120
pip install -r dreamgaussian/requirements.txt
python -c "import torch; print(torch.cuda.get_arch_list())"   # check again: pip must not have swapped torch
export TORCH_CUDA_ARCH_LIST="12.0"
git clone --recursive https://github.com/ashawkey/diff-gaussian-rasterization dreamgaussian/diff-gaussian-rasterization
pip install --no-build-isolation ./dreamgaussian/diff-gaussian-rasterization
pip install --no-build-isolation ./dreamgaussian/simple-knn
pip install --no-build-isolation git+https://github.com/NVlabs/nvdiffrast/
pip install git+https://github.com/ashawkey/kiuikit
```

Known issues. Apply a fix only if you hit the error, then log it in STATUS.md:

- diff-gaussian-rasterization, `uint32_t` / `uintptr_t` not declared: add `#include <cstdint>` to `cuda_rasterizer/rasterizer_impl.h`.
- simple-knn, `FLT_MAX` undefined: add `#include <cfloat>` to `simple_knn.cu`.
- OpenGL / EGL errors (`eglInitialize() failed`): pass `force_cuda_rast=True`. In WSL, always pass it.
- `rembg[gpu]` / onnxruntime-gpu errors: use `rembg[cli]` (CPU).
- `cached_download` import errors or zero123 pipeline errors from newer diffusers: pin `diffusers==0.24.0 huggingface_hub==0.19.4 transformers==4.36.2 accelerate==0.24.1`.
- numpy ABI errors from older compiled packages: `pip install "numpy<2"`.
- Headless only. Never `gui=True`. `dreamgaussian/diff-gaussian-rasterization/` is gitignored; save fixes to it as patches in `patches/`.

## Commands (upstream, run from `dreamgaussian/`)

```bash
python process.py data/name.jpg   # background removal + recenter -> data/name_rgba.png
python main.py  --config configs/image.yaml input=data/name_rgba.png save_path=name force_cuda_rast=True   # stage 1, 500 iters
python main2.py --config configs/image.yaml input=data/name_rgba.png save_path=name force_cuda_rast=True   # stage 2, 50 iters
kire logs/name.obj --save_video videos/name.mp4 --wogui --force_cuda_rast   # 360 degree video
kire logs/name.obj --save images/name/ --wogui --force_cuda_rast            # 8 views
python -m kiui.cli.clip_sim data/name_rgba.png logs/name.obj               # CLIP similarity
# text-to-3D: configs/text.yaml with prompt="..."; default prior is stabilityai/stable-diffusion-2-1-base (see STATUS.md)
```

## Handoff between Steven and Hector

- Test set (Hector): `data/test_set.csv` with `object_id, source, category, difficulty, why, front_azimuth, prompt, notes`, and input RGBA images in `data/inputs/`.
- Outputs (Steven): shared folder `outputs/<method>/<object_id>/seed<k>/` with the mesh, 8 renders (azimuth 0 to 315 in 45 degree steps, elevation 0), and a 360 video.
- Camera: GSO input renders, ground-truth renders, and output renders must use the same radius, FOV, and elevation convention. Record the agreed values here once set.
- Changes to either CSV schema need both of us.

## Results files

`results/runs.csv` (Steven, one row per generation run):
`run_id, date, git_sha, method, task, object_id, seed, config, stage1_sec, stage2_sec, total_sec, peak_vram_gb, vram_method, notes`

- `method` is `baseline` or `improved`. `task` is `image` or `text`.
- Wall-clock time per stage. Peak VRAM from `torch.cuda.max_memory_allocated()` or nvidia-smi sampling; record which in `vram_method`.

`results/scores.csv` (Hector, one row per scored run):
`run_id, clip_ref, clip_gt, clip_model, n_views, scored_on, notes`

- `clip_ref`: paper protocol, mean CLIP similarity of the 8 renders against the input image.
- `clip_gt`: our addition, renders against GSO ground-truth renders at the same views. It covers the back view, which `clip_ref` barely measures.
- The paper used `laion/CLIP-ViT-bigG-14-laion2B-39B-b160k`. Check what `kiui.cli.clip_sim` loads. Lock one model for the whole project.

## Repo layout

```
README.md                   project overview, changes table, credits (Steven)
CLAUDE.md                   this file (shared)
CLAUDE.local.md             personal notes, gitignored
docs/STATUS.md              state, decisions, agenda, environment record, log
docs/TASKS.md               every open to-do, plus the archive of finished ones
docs/next-steps.md          Steven's original Oct 16 plan (reference only)
docker/                     Dockerfile and pinned versions for the GPU env (Steven)
dreamgaussian/              authors' code: main.py, main2.py, configs/, sample data/, simple-knn/
                            diff-gaussian-rasterization/ is cloned in here and gitignored
patches/                    fixes to gitignored extensions
requirements-analysis.txt   analysis env
scripts/cs469/              batch runs, timing, render_gso.py
notebooks/                  01 to 03 (Steven), 04_evaluation and 05_failures (Hector)
data/test_set.csv, data/inputs/
results/runs.csv, results/scores.csv
configs/                    our baseline and improved configs (upstream ones stay in dreamgaussian/configs/)
```

## How to work in this repo

- Start of session: read STATUS.md and TASKS.md and say which task ID the work serves.
- Before anything that takes more than about 10 minutes of GPU time, say what it is and roughly how long it should take.
- When the paper and the code disagree, the code wins for reproduction. Note the gap in STATUS.md, since it is report material.
- Don't invent numbers. Paper numbers come from the PDF with a table or section reference. Ours come from the results files.
- End of session: update TASKS.md (check off, add, move done items to the Archive with the date) and STATUS.md (Current state, Decisions, Blockers, Log, Last updated). Keep STATUS.md under about 80 lines; move older log entries to `docs/archive/status-log.md`.
- If something is learned that every future session needs (a build fix, a command, a gotcha), add it to this file, not only to STATUS.md.

## Paper facts for sanity checks

- Stage 1: 500 iters of SDS on 3D Gaussians. Image-to-3D: 5000 initial points, densify every 100 iters, Zero-1-to-3 XL prior. Text-to-3D: 1000 points, densify every 50, Stable Diffusion 2.1 base prior.
- Mesh extraction: 16^3 blocks with an 8^3 local grid each (128^3 density grid), marching cubes threshold 1, then remesh and decimate.
- Stage 2: 50 iters of UV-space texture refinement with an MSE loss against SDEdit-style refined renders, not SDS (Fig. 3 shows why).
- Eval: CLIP similarity between the reference image and 8 renders (azimuth 0 to 315 in 45 degree steps, elevation 0), 30 test images. Table 1: 0.738 full pipeline, 0.678 stage 1 only, about 2 minutes on a V100, under 8 GB VRAM.
- Stated limitations (Sec. 5 and A.3): multi-face Janus problem, oversaturated texture, baked lighting, blurry back view (longer stage 2 helps).
- Our numbers will not match Table 1: different test set (GSO), GPU, and software versions. Compare baseline against improved within our own runs.
