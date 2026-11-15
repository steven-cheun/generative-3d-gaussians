#!/usr/bin/env bash
# export.sh — gather everything for the shared Google Drive into ONE folder, ready to drag into Drive.
# WHERE: WSL, from anywhere (it cd's to the repo). Uses the dg container for the comparison videos.
# USAGE: bash scripts/export.sh                  -> Windows dialogs: pick the location, then type the
#                                                   folder name (pre-filled DG_drive_<date>)
#        bash scripts/export.sh /some/dir/name    -> no dialogs: export straight to that folder
# WHY the dialogs go through powershell.exe: WSL has no window system of its own; Windows'
#   folder picker is reached by calling PowerShell, and `wslpath` turns its C:\... answer
#   back into a /mnt/c/... path.
set -euo pipefail
cd "$(dirname "$0")/.."
DEFAULT_NAME="DG_drive_$(date +%F)"

pick_folder() {
  # 1) folder picker (starts at the Desktop)  2) name box (pre-filled)  -> prints C:\...\<name>
  # Cancel in either -> prints nothing. -STA is required for Windows dialogs; the hidden TopMost
  # form keeps them in front of the terminal.
  local ps
  ps=$(cat <<PS
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName Microsoft.VisualBasic
\$owner = New-Object System.Windows.Forms.Form -Property @{TopMost = \$true}
\$dlg = New-Object System.Windows.Forms.FolderBrowserDialog
\$dlg.Description = 'Where should the DreamGaussian export go?'
\$dlg.SelectedPath = [Environment]::GetFolderPath('Desktop')
\$dlg.ShowNewFolderButton = \$true
if (\$dlg.ShowDialog(\$owner) -ne [System.Windows.Forms.DialogResult]::OK) { exit 0 }
\$name = [Microsoft.VisualBasic.Interaction]::InputBox('Name of the export folder:', 'DreamGaussian export', '$DEFAULT_NAME')
if ([string]::IsNullOrWhiteSpace(\$name)) { exit 0 }
Write-Output (Join-Path \$dlg.SelectedPath \$name.Trim())
PS
)
  # -EncodedCommand (UTF-16LE + base64) avoids all quoting problems between bash and PowerShell
  powershell.exe -NoProfile -STA -EncodedCommand "$(printf '%s' "$ps" | iconv -f UTF-8 -t UTF-16LE | base64 -w0)" | tr -d '\r'
}

if [ $# -ge 1 ]; then
  OUT=$1
else
  command -v powershell.exe >/dev/null || { echo "powershell.exe not found: pass a folder instead, e.g. bash scripts/export.sh /mnt/c/Users/\$USER/Desktop/$DEFAULT_NAME"; exit 1; }
  echo "== choose where to save (a Windows dialog opens; check the taskbar if you don't see it)"
  WIN_OUT=$(pick_folder)
  [ -n "$WIN_OUT" ] || { echo "Cancelled - nothing exported."; exit 0; }
  OUT=$(wslpath -u "$WIN_OUT")
fi
if [ -d "$OUT" ] && [ -n "$(ls -A "$OUT" 2>/dev/null)" ]; then
  echo "Note: $OUT already has files; matching files will be overwritten."
fi
echo "== export folder: $OUT"
OBJS=$(tail -n +2 data/gso_inputs/objects.csv | cut -d, -f1)
HARD="headset_box cartridge turtle orca shark cats"   # Hector's ask: baseline seeds 1-2 of the hard cases

echo "== 1/3 side-by-side videos (in the container, ~2 min)"
docker start dg >/dev/null
docker exec -w /workspace/generative-3d-gaussians dg python scripts/compare_videos.py

echo "== 2/3 copying to $OUT"
mkdir -p "$OUT"/{videos_compare,videos_seed0,videos_baseline_hard_seeds,results,inputs}
cp dreamgaussian/logs/compare/*_compare_s0.mp4 "$OUT/videos_compare/"
for o in $OBJS; do
  for t in baseline gso_bexact gso_bpair gso_2va gso_2vb gso_side; do
    src="dreamgaussian/logs/$t/${o}_s0.mp4"
    if [ -f "$src" ]; then cp "$src" "$OUT/videos_seed0/${o}_${t#gso_}_s0.mp4"; else echo "  missing $src"; fi
  done
done
for o in $HARD; do
  for s in 1 2; do cp "dreamgaussian/logs/baseline/${o}_s${s}.mp4" "$OUT/videos_baseline_hard_seeds/"; done
done
cp results/metrics.csv results/proportions.csv results/baseline_log.csv results/gso_bpair_log.csv \
   results/gso_2va_log.csv results/gso_2vb_log.csv results/gso_side_log.csv results/gso_bexact_log.csv "$OUT/results/"
cp data/gso_inputs_2v/_check.png "$OUT/inputs/2v_inputs_check.png"

echo "== 3/3 done"
for d in "$OUT"/*/; do echo "  $(ls "$d" | wc -l) files  $(du -sh "$d" | cut -f1)  $(basename "$d")"; done
echo "Total: $(du -sh "$OUT" | cut -f1)  ->  drag $OUT into the shared Drive"
