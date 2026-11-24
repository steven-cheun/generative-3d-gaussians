#!/usr/bin/env bash
# run_text3d.sh — text-to-3D for our 4 prompts, in three settings, to see what MVDream changes.
#   sd     : Stable Diffusion, no negative prompt (configs/text.yaml as is)
#   sdneg  : Stable Diffusion + the negative prompt from text_mv.yaml
#   mv     : MVDream + the same negative prompt (configs/text_mv.yaml as is)
# sdneg vs mv differ only in the guide, so that pair shows MVDream's effect.
# Run inside the container from the repo root. About 2.5 min per prompt for sd and sdneg; mv is slower.
# Usage: bash scripts/run_text3d.sh sd sdneg mv     (any subset, in any order)
set -u
cd "$(dirname "$0")/../dreamgaussian"

SD=sd2-community/stable-diffusion-2-1-base
NEG=$(python -c "from omegaconf import OmegaConf; print(OmegaConf.load('configs/text_mv.yaml').negative_prompt)")
PROMPTS=("mug_white|a plain white ceramic coffee mug" "corgi|a corgi" "chair|a red wooden chair" "teapot|a teapot")

for setting in "$@"; do
  case $setting in
    sd)    ARGS=(--config configs/text.yaml hf_key=$SD) ;;
    sdneg) ARGS=(--config configs/text.yaml hf_key=$SD "negative_prompt=$NEG") ;;
    mv)    ARGS=(--config configs/text_mv.yaml) ;;
    *) echo "unknown setting: $setting (use sd, sdneg or mv)"; exit 1 ;;
  esac
  for p in "${PROMPTS[@]}"; do
    name="text_${setting}_${p%%|*}"; prompt="${p#*|}"
    echo "=== $(date +%T) $name: $prompt"
    python main.py  "${ARGS[@]}" "prompt=$prompt" save_path=$name force_cuda_rast=True
    python main2.py "${ARGS[@]}" "prompt=$prompt" save_path=$name force_cuda_rast=True
    kire logs/$name.obj --save_video logs/$name.mp4 --wogui --force_cuda_rast
  done
done
echo "=== $(date +%T) done"
