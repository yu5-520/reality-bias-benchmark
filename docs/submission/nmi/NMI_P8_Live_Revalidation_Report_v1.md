# NMI-P8 Live Revalidation Report v1

Date: 2026-09-21  
Status: **AUTOMATED PREFLIGHT COMPLETE / HUMAN METADATA GATE OPEN**

P8 rechecked the current Nature Machine Intelligence pages rather than relying only on the P7 local snapshot.

## Live checks

| Surface | Current requirement | Repository state |
| --- | --- | --- |
| Article main text | <= 3,500 words | PASS — 2,942 |
| Abstract | <= 150 words, unreferenced | PASS — 147 |
| Main display items | <= 6 | PASS — 5 |
| Introduction | no heading | PASS |
| Results | present + topical subheadings | PASS |
| Discussion | present + no subheadings | PASS |
| Methods | present + topical subheadings | PASS |
| Initial file type | PDF / Word / TeX+PDF accepted | READY FOR EXPORT |
| Manuscript author names/affiliations | required unless double-anonymized | **WAITING REVIEW-MODE CHOICE + VERIFIED METADATA** |
| LLM use | document in Methods/alternative | PASS |
| Cover letter | required | PASS editorially; disclosure fields still human-bound |
| Related-manuscript disclosure | cover-letter requirement | WAITING HUMAN CONFIRMATION |
| Prior-editor-discussion disclosure | cover-letter requirement | WAITING HUMAN CONFIRMATION |
| Competing interests | declaration required | WAITING HUMAN CONFIRMATION |
| Data Availability | required | PASS |
| Code Availability | required for central custom code | PASS |
| Supplement | optional / relevant only | PASS after removing unmaterialized figure-plan promises |
| ORCID | requested before final acceptance | NON-BLOCKING FOR AUTOMATED INITIAL PREFLIGHT |

## Important finding

The identity-neutral manuscript cannot simply be called “final” without selecting the peer-review mode.

- If standard review is used, verified author names and affiliations must be inserted into the manuscript.
- If double-anonymized review is used, the identity-neutral manuscript is appropriate, but verified author/affiliation/contact information must be placed in the cover letter and the submission system.

P8 therefore refuses to guess identity metadata or silently choose a review model.

## Editorial cleanup

The P7 Supplementary Information included a **Supplementary Figure plan** but no corresponding submission assets. P8 removes that planning-only section in v0.3 rather than submitting promises for figures that are not materialized.

## Scientific boundary

P8 performed no:

- subject run;
- provider call;
- evaluator call;
- semantic adjudication;
- raw-evidence mutation;
- claim expansion.

Current state:

`NMI_P8_AUTOMATED_PREFLIGHT_COMPLETE_WAITING_HUMAN_METADATA`
