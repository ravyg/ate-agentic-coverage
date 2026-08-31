# Release Checklist

The steps to take this dataset from **private / pre-submission** to a **public,
permanently-archived, citable release**.

> ⚠️ **Do NOT run this before you're ready.** Making the repo public and minting a
> Zenodo DOI are effectively **irreversible** (a DOI cannot be deleted). Because of
> the paper's **blind-review** considerations, keep everything private until the
> paper is submitted/accepted and de-anonymized.

---

## Phase 0 — Pre-flight (data must be final)

- [ ] Full-corpus labeling complete: `scripts/merge_validate.py` prints
      `ALL TASKS LABELED ✔` and `data/agentic_coverage.csv` has 18,796 rows.
- [ ] Human validation complete: `validation/audit_scores_200.csv` (de-identified,
      NOT committed) exists and `python3 validation/compute_validation.py`
      reproduces every number in `validation/RESULTS.md`.
- [ ] Spot-check `data/agentic_coverage.csv`: 18,796 rows, header exactly
      `task_id,occupation,task_text,coverage,rationale`, `coverage` in [0, 1],
      no stray/unparseable values.
- [ ] All docs current: `README.md`, `docs/SCHEMA.md`, `docs/METHODOLOGY.md`,
      `validation/README.md`.

## Phase 1 — Credit & metadata

- [ ] Confirm the **annotator names** in the README Acknowledgements (Saket
      Kumar, Maulik Dang, Shreeya Sharma). Confirm each person consents to
      being named (or mark anonymous on request).
- [ ] Add ORCIDs in `CITATION.cff` (Ravish, Saket, Maulik) — leave blank if none.
- [ ] Confirm the paper citation / arXiv ID is final in README + `CITATION.cff`.
- [ ] Update the version number if changed (README, `CITATION.cff` → `version:`,
      `.zenodo.json` → `version`).

## Phase 2 — Go public

- [ ] Final review that **no PII or private/unpublished framework code**
      leaks in:
  - `data/human_annotations_raw.json`, `data/human_annotations_tidy.csv`,
    `validation/audit_scores_200.csv` are gitignored — confirm none are staged.
  - `crowdsource/.clasp.json` / `.clasprc.json` are gitignored — confirm no
    OAuth credentials are staged.
  - No `results/human_ratings*.csv` / `responses*.csv` exports are staged.
- [ ] Flip the repo public:
      ```bash
      gh repo edit ravyg/ate-agentic-coverage --visibility public --accept-visibility-change-consequences
      ```
- [ ] Add repo topics for discoverability:
      ```bash
      gh repo edit ravyg/ate-agentic-coverage \
        --add-topic onet --add-topic labor-economics --add-topic automation \
        --add-topic dataset --add-topic ai-and-work --add-topic agentic-ai
      ```

## Phase 3 — Tag a versioned release

- [ ] Tag and push `v1.0.0`:
      ```bash
      git tag -a v1.0.0 -m "O*NET Agentic Coverage Dataset v1.0.0"
      git push origin v1.0.0
      ```
- [ ] Create the GitHub Release (this is what Zenodo snapshots):
      ```bash
      gh release create v1.0.0 \
        --title "O*NET Agentic Coverage Dataset v1.0.0" \
        --notes "First public release: agentic-coverage scores for all 18,796 O*NET tasks, human-validated (Spearman rho = 0.884 against a three-annotator panel; model runs 0.147 low in absolute terms). See README."
      ```

## Phase 4 — Mint the Zenodo DOI

- [ ] Log in at <https://zenodo.org> with the GitHub account (`ravyg`).
- [ ] **Settings → GitHub** → toggle **ON** for `ate-agentic-coverage`.
      (Must be done **before** the release for auto-capture; if the release
      already exists, cut a `v1.0.1` release to trigger it.)
- [ ] Zenodo auto-creates a deposit from the release and mints a DOI.
- [ ] On the Zenodo record, confirm it reads from `CITATION.cff` (authors,
      title, CC-BY-4.0) and that **"cite the paper"** intent is clear in the
      description.
- [ ] Grab the DOI (e.g. `10.5281/zenodo.XXXXXXX`).

## Phase 5 — Wire the DOI back in

- [ ] Add the Zenodo DOI badge to the top of `README.md`.
- [ ] Replace every "TBD, not yet minted" DOI placeholder in `README.md` and
      `CITATION.cff` with the real DOI.
- [ ] Uncomment/fill the `doi:` field in `CITATION.cff`.
- [ ] Put the DOI into the paper's Data Availability / supplement section.
- [ ] Commit + push the README and `CITATION.cff` updates.

## Phase 6 — Announce

- [ ] Publish the Hugging Face dataset (`ravishgupta/ate-agentic-coverage`) and
      confirm `datasets.load_dataset(...)` works.
- [ ] Cross-link: add a pointer to this dataset (+ DOI) in the `ate-framework`
      README and in the `ate-task-ability-dataset` README's Related section.
- [ ] Update `MEMORY.md` / project notes with the final DOI and public URL.
- [ ] Post `LINKEDIN_POST.md`, share the star/clone request with co-authors and
      annotators now that the repo is public and stars actually count.

---

### Rollback note
You **can** flip the repo back to private (`gh repo edit ... --visibility private`),
but you **cannot** un-mint a Zenodo DOI — only publish a new version. So treat
**Phase 4 as the point of no return** and be sure the data is final before it.
