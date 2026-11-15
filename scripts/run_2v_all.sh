#!/usr/bin/env bash
# run_2v_all.sh — the whole two-view experiment, unattended (~4 h on the RTX 5070).
# WHERE: INSIDE the container, from the repo root (/workspace/generative-3d-gaussians).
# WHAT : 4 conditions x 14 objects x 3 seeds, then CLIP for all 5 conditions
#        (baseline-pair already ran on 2026-11-14 as gso_bpair).
# ORDER: most important first, so a stop halfway still leaves the main comparison.
# Each run_batch/eval_clip call skips nothing and appends: don't start this twice.
set -u
cd "$(dirname "$0")/.."

IMG2V=$(cd dreamgaussian && ls ../data/gso_inputs_2v/*_rgba.png)        # front, shared zoom (+ _side.png next to it)
IMGSIDE=$(cd dreamgaussian && ls ../data/gso_inputs_side/*_rgba.png)    # side only, own zoom
IMGEXACT=$(cd dreamgaussian && ls ../data/gso_inputs_exact/*_rgba.png)  # front, own zoom, exact outline
RUN="python scripts/run_batch.py --seeds 0 1 2 --video"

echo "=== $(date) start"
$RUN --tag gso_2va    --images $IMG2V --extra side_input=auto zero123_cond=front
$RUN --tag gso_2vb    --images $IMG2V --extra side_input=auto zero123_cond=nearest

# CLIP reference = each run's own input (the shared-zoom front for these three)
python scripts/eval_clip.py --inputs data/gso_inputs_2v --logs dreamgaussian/logs/gso_bpair --tag gso_bpair
python scripts/eval_clip.py --inputs data/gso_inputs_2v --logs dreamgaussian/logs/gso_2va   --tag gso_2va
python scripts/eval_clip.py --inputs data/gso_inputs_2v --logs dreamgaussian/logs/gso_2vb   --tag gso_2vb

$RUN --tag gso_side   --images $IMGSIDE
$RUN --tag gso_bexact --images $IMGEXACT
python scripts/eval_clip.py --inputs data/gso_inputs_side  --logs dreamgaussian/logs/gso_side   --tag gso_side
python scripts/eval_clip.py --inputs data/gso_inputs_exact --logs dreamgaussian/logs/gso_bexact --tag gso_bexact
echo "=== $(date) done"
