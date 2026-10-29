# STATUS

Last updated: 2026-10-21 (Claude Code: repo cloned, project docs on branch project-docs, state caught up to Steven's Oct 19 commits)
Next meeting: Thu Oct 22, in person. Treat it as the kickoff.
Next checkpoint: Oct 22 (setup working) and Oct 26 (first object) are already met per Steven's Oct 19 commits. Next is Oct 29 (test set ready, Hector). Re-plan Thursday.

## Current state

- Plan and roles drafted Oct 16 (docs/next-steps.md). "Me" there is Steven; "Partner" is Hector. Live to-dos are in docs/TASKS.md.
- Repo: steven-cheun/generative-3d-gaussians, default branch `master`. Commit 1 (876d6fc) is the authors' code, untouched, in `dreamgaussian/`. Project docs on branch `project-docs`, PR for Thursday.
- GPU env (Steven): Docker, working. Image-to-3D reproduced on `anya` (see README). Analysis env (Hector): plain Python venv on Windows plus Blender, not built yet (H-08).

## Machines

- Steven: RTX 5070, Windows + WSL2. All final generation runs.
- Hector: desktop (RTX 2060, i7-8700K, 16 GB RAM) and laptop (Intel Core Ultra 7 258V, no NVIDIA GPU). Analysis env, Blender, notebooks 04 and 05.

## Submission requirements

1. PowerPoint presentation
2. Word document of the report
3. Jupyter notebooks and all code files (database if any). Must be executable.
4. Link to the recorded Zoom presentation

## Environment record (GPU env, Steven)

Lives in Steven's files, not duplicated here: `README.md` (reproduction and changes tables) and `docker/` (Dockerfile, pinned versions in `constraints.txt`).

## Decisions

- 2026-10-16: Roles. Steven is ML engineer and tech lead; Hector owns data, evaluation, and research communication.
- 2026-10-16: All final generation runs on Steven's RTX 5070.
- 2026-10-16: Primary metric is CLIP similarity, following the paper's protocol.
- 2026-10-16: The improvement is Steven's call; brainstorm together in Week 3.

## Proposed, confirm Thursday

- Two environments: GPU env (Steven's call, Docker optional) and a CPU-friendly analysis env (Hector, and what the grader runs for notebooks 04 and 05).
- Sharing: GitHub for code, CSVs, docs, and small input images; one synced shared folder for big files and the Word/PowerPoint deliverables.
- Handoff: `runs.csv` (Steven) and `scores.csv` (Hector) joined on `run_id`; output folder layout as in CLAUDE.md.
- 3 seeds per object, paired comparison per object.
- Add `clip_gt` (renders vs GSO ground truth) alongside the paper's `clip_ref`.

## Thursday agenda

1. Review the project docs PR. Merge, or note what to change.
2. Re-plan dates. Steven's first object already ran, so pull later dates forward?
3. Shared folder: OneDrive (if both CSUEB accounts include it) or Google Drive. Who sets it up?
4. What "finished" means for code and results. What does "executable" mean to the instructor: runs on the grader's machine, or runs with saved outputs? Ask if unclear.
5. Text-to-3D: upstream loads `stabilityai/stable-diffusion-2-1-base`, which reportedly no longer downloads from Hugging Face. Mirror, switch prior, or image-to-3D only?
6. Render camera for GSO inputs and outputs (radius, FOV, elevation).
7. Which CLIP model to lock.
8. Was the paper PDF link submitted? Sync once or twice a week? Is individual contribution graded?
9. Steven: CLAUDE.md rule 2 (`// CS469:` markers) and the "GPU env setup" section were written before the Docker setup. Edit them to match how you actually work.

## Blockers

- No shared folder yet.

## Log (newest first, keep about 10, archive older)

- 2026-10-21: Hector cloned the repo. Code is in `dreamgaussian/`, so CLAUDE.md paths were fixed to match. Project docs added on branch `project-docs`; CLAUDE.local.md gitignored. STATUS caught up to Steven's Oct 19 commits (Docker env and the `anya` reproduction were already done).
- 2026-10-21: Steven created the repo. Added docs/TASKS.md as the single task tracker; added sharing plan to CLAUDE.md.
- 2026-10-21: Roles corrected (Hector: data, evaluation, research comms). Rewrote CLAUDE.md, STATUS.md, CLAUDE.local.md, and the claude.ai project instructions around a two-environment setup.
