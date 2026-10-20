# Generative 3D Gaussians

Course project for Generative AI: a reproduction and extension of **DreamGaussian** (Tang et al., ICLR 2024), which turns a single image or a text prompt into a textured 3D object using SDS-guided 3D Gaussian Splatting.

**Status:** reproduction working (image-to-3D) · improvement in progress

| | |
|---|---|
| Team | Steven Cheun · Hector Pena |
| Original paper | [arXiv 2309.16653](https://arxiv.org/abs/2309.16653) |
| Original code | [dreamgaussian/dreamgaussian](https://github.com/dreamgaussian/dreamgaussian) (upstream commit `69a3c70`) |

---

## Repository layout

```
dreamgaussian/   Original authors' code (commit 1 = unmodified upstream; later commits = our changes)
docker/          Dockerfile + pinned package versions to rebuild the environment
```

Planned: `configs/` (baseline vs. improved), `notebooks/`, `data/`, `results/`.

---

## Environment

Tested on an **NVIDIA RTX 5070** (Blackwell, compute capability 12.0), Windows 11 + WSL2 + Docker.

- Base image: `pytorch/pytorch:2.11.0-cuda12.8-cudnn9-devel` (PyTorch 2.11, CUDA 12.8)
- All Python packages pinned in `docker/constraints.txt`
- CUDA extensions (diff-gaussian-rasterization, simple-knn, nvdiffrast) compiled for `sm_120`

### Build the image
```bash
docker build -f docker/Dockerfile -t dreamgaussian:cu128 .
```
For other GPUs, change `TORCH_CUDA_ARCH_LIST` in `docker/Dockerfile` (e.g. `"7.5;12.0"` to also support RTX 20-series) and rebuild.

### Start a container
```bash
docker run -it --gpus all --name dg \
  -v <parent-of-this-repo>:/workspace \
  -v ~/hf-cache:/root/.cache/huggingface \
  dreamgaussian:cu128 bash
```
`~/hf-cache` keeps the downloaded model weights (~2.5 GB) between containers.
The image's default folder is `/workspace/generative-3d-gaussians/dreamgaussian`, so keep the repo folder named `generative-3d-gaussians`.

---

## Quick start (image-to-3D)

Inside the container, from `dreamgaussian/`:
```bash
# Stage 1: optimize 3D Gaussians, export a coarse mesh
python main.py  --config configs/image.yaml input=data/anya_rgba.png save_path=anya force_cuda_rast=True
# Stage 2: refine mesh texture
python main2.py --config configs/image.yaml input=data/anya_rgba.png save_path=anya force_cuda_rast=True
# 360° video of the result
kire logs/anya.obj --save_video logs/anya.mp4 --wogui --force_cuda_rast
```
`force_cuda_rast=True` avoids OpenGL, which may be unavailable in WSL/containers.

### Reproduction (RTX 5070, image-to-3D, `anya`)
| Stage | Time |
|---|---|
| Gaussian stage (500 iterations) | 38.5 s |
| Mesh stage (50 iterations) | 15.8 s |
| **Total per object** | **~54 s** (paper: ~2 min) |
| Peak VRAM | ~4.1 GB |

---

## Changes to the original code

| Change | Where | Why |
|---|---|---|
| Add `#include <cfloat>` | `dreamgaussian/simple-knn/simple_knn.cu` | Newer compilers no longer include it implicitly; required to build |

See `git log` for the full history; `git diff 876d6fc -- dreamgaussian/` shows every change to the original code.

---

## Results

_To be added: baseline vs. improved comparison (CLIP similarity, timing, Gaussian count) across multiple seeds._

---

## Credits & licenses

This project builds directly on the work below. All original license files are kept in `dreamgaussian/`.

- **DreamGaussian** — Tang, Ren, Zhou, Liu, Zeng. MIT License.
- **3D Gaussian Splatting** — Kerbl, Kopanas, Leimkühler, Drettakis (Inria). `simple-knn` and the differentiable rasterizer derive from this work and are under the Inria license (**non-commercial, research and evaluation use only**; see `dreamgaussian/LICENSE_GAUSSIAN_SPLATTING.md`).
- **diff-gaussian-rasterization** (fork with depth/alpha) and **kiuikit** — Jiaxiang Tang.
- **nvdiffrast** — NVIDIA Research.
- **Zero-1-to-3** (Liu et al., ICCV 2023) — view-conditioned diffusion model used as guidance; Zero123-XL weights via Hugging Face (`ashawkey/zero123-xl-diffusers`).

Because of the Inria license, this repository is for **non-commercial research and educational use**.

```bibtex
@misc{tang2024dreamgaussiangenerativegaussiansplatting,
      title={DreamGaussian: Generative Gaussian Splatting for Efficient 3D Content Creation}, 
      author={Jiaxiang Tang and Jiawei Ren and Hang Zhou and Ziwei Liu and Gang Zeng},
      year={2024},
      eprint={2309.16653},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2309.16653}, 
}
```
