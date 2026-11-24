#!/usr/bin/env bash
# run_2vc.sh — 2V-c: front + side photo; Zero123 gets one of them at random each step (iFusion's rule).
# Run inside the container from the repo root. 14 objects x 3 seeds, about 45 min on the RTX 5070.
# Same photos as 2V-a and 2V-b, so the three runs differ only in which photo Zero123 gets.
# Adds rows to the result CSVs, so run it only once.
set -u
cd "$(dirname "$0")/.."

IMG2V=$(cd dreamgaussian && ls ../data/gso_inputs_2v/*_rgba.png)

echo "=== $(date) start 2V-c"
python scripts/run_batch.py --seeds 0 1 2 --video --tag gso_2vc \
  --images $IMG2V --extra side_input=auto zero123_cond=random

python scripts/eval_clip.py --inputs data/gso_inputs_2v --logs dreamgaussian/logs/gso_2vc --tag gso_2vc

# proportions.py rewrites its whole CSV, so list every tag
python scripts/proportions.py --tags baseline gso_bexact gso_bpair gso_2va gso_2vb gso_side gso_2vc
echo "=== $(date) done"
