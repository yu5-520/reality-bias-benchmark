# NMI-P8H.2 Final Status v1

Date: 2026-09-21  
Status: **PUBLIC FROZEN RAW EVIDENCE COMPLETE / PORTAL READY**

The final submission surface now matches the public evidence architecture.

## Frozen does not mean hidden

Completed raw evidence is now publicly readable and downloadable from:

https://github.com/yu5-520/reality-bias-benchmark/releases/tag/frozen-raw-evidence-v1

The release contains **24 byte-preserved historical evidence archives**.

Each published asset is bound to its historical GitHub Actions artifact identity and SHA-256 digest.

Repository access catalogs are under:

`evidence/frozen_raw/`

including:

- `release_manifest_v1.json`;
- `SHA256SUMS_v1.txt`;
- `catalog_v1/artifact_<id>.json`.

Runtime directories remain ignored only because they are mutable execution surfaces. The public frozen evidence is a separate release surface.

## Immutability gate

Workflow:

`35572865285` — **SUCCESS**

Validator output:

- `FROZEN_RAW_IMMUTABILITY=PASS`
- `FROZEN_RAW_PUBLIC_ASSET_COUNT=24`
- `RUNTIME_RAW_IGNORE=PASS`
- `VERSION_RULE=APPEND_ONLY_NEW_VERSION`

Existing frozen release assets are not overwritten. A correction must create a new evidence version.

## Final manuscript

Submission source:

`docs/submission/nmi/NMI_Manuscript_v0.17_PUBLIC_RAW.md`

Data Availability now states explicitly that the raw evidence packages are public and points to the frozen-raw release.

Code Availability now includes the raw-evidence publication and validation interfaces.

No scientific result or claim changed.

## Final submission export

Workflow:

`35573108686` — **SUCCESS**

Artifact:

`10626632446`

Artifact digest:

`sha256:c9e8818580a6ba77d236c74a8c6809f8a021ff13bc8cff215e36505b0e8ad6d6`

Inner submission ZIP SHA-256:

`dd148df99096c59077bb2b7c91ce333e400b4ecc80ea0eb094d478d34840554f`

## Visual QA

The final deliverables were re-rendered after the frozen-raw availability update.

- manuscript DOCX: **13 pages — PASS**
- manuscript PDF: **13 pages — PASS**
- Supplementary Information: **4 pages — PASS**
- cover letter: **1 page — PASS**
- Data Availability release URL: **visible and readable**
- Code Availability repository URL: **visible and readable**
- figures: **intact**
- clipping / overlap / broken glyphs: **none observed**

## Scientific boundary

This update used:

- 0 new subject runs;
- 0 provider calls;
- 0 evaluator calls;
- 0 semantic adjudications;
- 0 raw-evidence mutations;
- 0 theory expansion.

Current state:

`NMI_P8H_2_PUBLIC_FROZEN_RAW_COMPLETE_PORTAL_READY`

Next action:

`NMI_PORTAL_UPLOAD`
