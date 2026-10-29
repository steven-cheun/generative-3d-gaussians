# TASKS

Last updated: 2026-10-21

One page for every to-do. Open tasks at the top, finished ones in the Archive at the bottom. Claude (chat or Claude Code) updates this file at the end of each session.

How it works:

- One line per task: `- [ ] ID · due · task. Done when: ...` IDs never get reused.
- H = Hector, B = both. Steven can add an S section if he wants his tasks tracked here too.
- When a task is done: check it, add the date, move it to the top of the Archive.
- If a task is stuck on someone else, list the dependency under "Waiting on".
- Pull before editing this file. It's the one most likely to conflict.

## Before Thursday (Oct 22)

- [ ] H-01 · Thu Oct 22 · Read the DreamGaussian paper: Sec. 1 to 3, Sec. 4.3, App. A.1 and A.2. Done when: short notes in my own words for each of slides 1 to 4 (intro, 3D Gaussian splatting, diffusion + Zero123, SDS), plus the eval protocol written out exactly.
- [ ] H-03 · Thu Oct 22 · GSO recon: download route, license (CC-BY 4.0, needs attribution), object count, file layout. Download 2 or 3 objects and open one in Blender. Findings go in STATUS.md.
- [ ] H-04 · Thu Oct 22 · Draft `data/test_set.csv`: about 30 objects, roughly 10 easy, 10 medium, 10 hard, one-line "why" each.
- [ ] H-05 · Thu Oct 22 · Set up the claude.ai Project (instructions + knowledge files).
- [ ] B-01 · Thu Oct 22 · First sync: walk the agenda in STATUS.md, re-plan dates, pick the shared folder.

## Next

- [ ] H-06 · Fri Oct 23 · Create the shared folder and invite Steven (if that's decided as mine on Thursday).
- [ ] H-07 · Sun Oct 25 · Diffusion basics: Lilian Weng's diffusion post, then Hugging Face's Annotated Diffusion. Done when: I can explain the forward and reverse process and noise prediction for slide 3.
- [ ] H-08 · Sun Oct 25 · Analysis env: `requirements-analysis.txt` plus a venv working on both my desktop and laptop.
- [ ] H-09 · Wed Oct 28 · `scripts/cs469/render_gso.py` (Blender, headless) using the camera agreed with Steven.
- [ ] H-10 · Thu Oct 29 · CHECKPOINT. Test set ready: 20 to 30 GSO objects rendered to `data/inputs/`, about 10 prompts if text-to-3D stays in scope.
- [ ] H-11 · Mon Nov 2 · CHECKPOINT. `notebooks/04_evaluation.ipynb` working: reads runs.csv and renders, writes scores.csv (clip_ref, clip_gt), runs on CPU.
- [ ] H-12 · after brainstorm · Novelty check for Steven's improvement idea.
- [ ] H-13 · Mon Nov 9 (proposed) · `notebooks/05_failures.ipynb`: failure-case analysis of baseline outputs, grouped by difficulty tier.
- [ ] H-14 · Fri Nov 20 (proposed) · Tables and figures from runs.csv and scores.csv: paired comparison per object, mean and spread.
- [ ] H-15 · Tue Nov 24 · CHECKPOINT. Report intro, background, and lit review drafted.
- [ ] H-16 · Tue Nov 24 · CHECKPOINT. Slides 1 to 4 drafted.
- [ ] H-17 · Sat Nov 28 (proposed) · Report formatted in the IEEE Word template.
- [ ] B-02 · Week 3 · Improvement brainstorm. Hector brings 2 or 3 papers that tackled the paper's stated limitations.
- [ ] B-03 · Tue Nov 24 · Conclusions and future work; cross-review each other's report sections.
- [ ] B-04 · Mon Nov 30 · Rehearse twice, record the Zoom talk.
- [ ] B-05 · Tue Dec 1 · Final check of all four deliverables; Steven submits.

## Waiting on

- Steven: render camera values (radius, FOV) for GSO inputs. Needed for H-09.
- Steven: first baseline outputs in the agreed folder layout. Needed to test H-11 on real data.
- Instructor: what "executable" means for the notebooks.

## Archive (done, newest first)

- [x] H-02 · 2026-10-21 · Cloned the repo, added the project docs on branch `project-docs`, opened a PR for Steven to review Thursday.
- [x] H-00 · 2026-10-21 · Set up CLAUDE.md, CLAUDE.local.md, STATUS.md, TASKS.md, and the claude.ai project instructions.
- [x] S · 2026-10-21 · Steven created the GitHub repo.
