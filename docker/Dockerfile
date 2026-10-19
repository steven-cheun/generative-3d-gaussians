# DreamGaussian environment for RTX 50-series (Blackwell, sm_120)
# Recreates the environment that was first set up manually on 2026-10-19.
#
# Build (from repo root, in WSL):
#   docker build -f docker/Dockerfile -t dreamgaussian:cu128 .
# Run:
#   docker run -it --gpus all --name dg2 \
#     -v ~/dg:/workspace -v ~/hf-cache:/root/.cache/huggingface \
#     dreamgaussian:cu128 bash

# PyTorch 2.11 + CUDA 12.8: newest PyTorch line with a cu128 build (2.12+ dropped it).
# "devel" variant includes nvcc, needed to compile the CUDA extensions.
FROM pytorch/pytorch:2.11.0-cuda12.8-cudnn9-devel

# Settings from the manual setup's `export` lines, baked in so every shell has them.
#   TORCH_CUDA_ARCH_LIST  -> compile extensions for the RTX 5070 (compute capability 12.0).
#                            Also lets them build here, where no GPU is visible.
#   PIP_BREAK_SYSTEM_PACKAGES -> allow pip installs into the image's Python 3.12 (PEP 668 guard).
ENV DEBIAN_FRONTEND=noninteractive \
    TORCH_CUDA_ARCH_LIST="12.0" \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
    PIP_NO_CACHE_DIR=1

# System tools: compilers for the extensions, OpenGL/EGL libs for opencv and nvdiffrast.
RUN apt-get update && apt-get install -y --no-install-recommends \
        git build-essential ninja-build libgl1 libglib2.0-0 libegl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/build

# Python packages, pinned to the exact versions that worked on 2026-10-19.
# constraints.txt = pip freeze minus locally built packages; it also locks torch.
COPY dreamgaussian/requirements.txt docker/constraints.txt ./
RUN python -m pip install -r requirements.txt -c constraints.txt

# CUDA extensions, pinned to the commits built on 2026-10-19.
# simple-knn is copied from this repo so it includes the #include <cfloat> fix.
COPY dreamgaussian/simple-knn ./simple-knn
RUN git clone --recursive https://github.com/ashawkey/diff-gaussian-rasterization \
    && git -C diff-gaussian-rasterization checkout 8829d14f814fccdaf840b7b0f3021a616583c0a1 \
    && git -C diff-gaussian-rasterization submodule update --init --recursive \
    && python -m pip install --no-build-isolation ./diff-gaussian-rasterization \
    && python -m pip install --no-build-isolation ./simple-knn \
    && python -m pip install --no-build-isolation \
        "git+https://github.com/NVlabs/nvdiffrast@253ac4fcea7de5f396371124af597e6cc957bfae" \
    && python -m pip install "git+https://github.com/ashawkey/kiuikit" \
    && rm -rf /opt/build/diff-gaussian-rasterization

# Sanity check at build time: fails the build if any extension doesn't import.
RUN python -c "import torch, diff_gaussian_rasterization, simple_knn._C, nvdiffrast.torch, kiui; print('all ok', torch.__version__)"

WORKDIR /workspace/generative-3d-gaussians/dreamgaussian
CMD ["bash"]
