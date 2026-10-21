# Next Steps & Roles

_Created: 2026-10-16 22:07 PT (Session 2) · Final deadline: Tue Dec 1, 11:59 pm PT_

---

## Roles

### Me — ML engineer (technical lead)
Builds and runs everything on the GPU.
- Environment: Docker/WSL2, CUDA extensions rebuilt for cu128
- Baseline reproduction + code map
- Designs and implements the improvement (my own idea; final call is mine)
- Runs all final experiments on my RTX 5070 (one machine = fair comparison)
- Report: original model, improvement, results
- Slides 5–8: method, reproduction, improvement, results (~15 min)

### Partner — data, evaluation & research communication (DS-style role)
Prepares inputs, measures outputs, explains the background.
- Test set: GSO objects + text prompts, input images prepared
- Evaluation notebook (CLIP similarity → results table)
- Failure-case analysis of baseline outputs
- Novelty check for the improvement idea
- Tables and graphs from my logged results
- Report: introduction, background, lit review; formatting into the IEEE template
- Slides 1–4: intro, 3DGS, diffusion + Zero123, SDS (~13 min)

### Both
- Weekly sync: I demo the code, partner explains the background
- Improvement brainstorm (Week 3)
- Conclusions + future work; cross-review each other's report sections
- Rehearse twice, record Zoom, final check of deliverables
- Rule: each of us must be able to answer questions on the other's slides

**Estimated effort split:** ~65% me / ~35% partner (closer to 55/45 if partner owns failure analysis, as planned above).

---

## Next actions

### Me — Saturday Oct 17 (setup day)
1. [ ] Confirm the GPU is visible inside WSL2 (`nvidia-smi`)
2. [ ] Confirm Docker can see the GPU
3. [ ] Pick a PyTorch base image built for CUDA 12.8+ (verify current version before installing)
4. [ ] Clone DreamGaussian; build the modified diff-gaussian-rasterization, simple-knn, nvdiffrast, kiuikit
   - Make sure the build targets Blackwell (compute capability 12.0 / sm_120; verify)
5. [ ] Run the Colab demo once to see what correct output looks like
6. [ ] Generate one object from a sample image in the repo's `data/` folder
7. [ ] Record: total time, Gaussian stage time, mesh stage time, peak VRAM, any errors and fixes
8. [ ] Create the private GitHub repo; **first commit = authors' code untouched**
9. [ ] Create the shared cloud folder (outputs, figures, report.docx, talk.pptx); invite partner

### Partner — this week (Oct 17–22)
1. [ ] Get access to the GitHub repo + shared folder
2. [ ] Read the DreamGaussian paper in full
3. [ ] Learn diffusion basics (Lilian Weng's post; Hugging Face "Annotated Diffusion")
4. [ ] Look into Google Scanned Objects: how to download, license terms, how many objects
5. [ ] Draft a shortlist of ~30 candidate GSO objects (mix of shapes, textures, difficulty)

### Both — this week
- [ ] Hold the first sync (~30 min): walk through these roles and the timeline
- [ ] Partner confirms they're comfortable owning the background slides + lit review

---

## Upcoming checkpoints

| Date | Checkpoint | Owner |
|---|---|---|
| Oct 22 | Setup working locally (if not → switch baseline to Colab while debugging) | Me |
| **Oct 26** | **First object generated on my GPU** → re-plan timeline | Me |
| Oct 29 | Test set ready (~20–30 GSO objects, ~10 prompts) | Partner |
| Nov 2 | Baseline on full test set; evaluation notebook working | Me / Partner |
| Nov 16 | Improvement measured on full test set | Me |
| Nov 24 | Report + slides drafted | Both |
| Nov 30 | Zoom recorded | Both |
| Dec 1 | Submitted | Me |

---

## Project layout

- **Private GitHub repo:** code, configs, notebooks, small data, CSV results
- **Shared cloud folder:** meshes, 360° videos, figures, `report.docx`, `talk.pptx` (not in git)
- Notebooks: `01_setup_check`, `02_baseline`, `03_improved` (me) · `04_evaluation`, `05_failures` (partner)

---

## Still to confirm
- [ ] Was the paper PDF link submitted to the instructor?
- [ ] Meeting frequency: once or twice a week?
- [ ] Partner's GPU model (only matters for their own testing)
- [ ] Does the class grade individual contribution? If so, state the role split openly in the report.
