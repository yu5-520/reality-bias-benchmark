# NMI-P8 Status v1

Date: 2026-09-21  
Status: **AUTOMATED PREFLIGHT COMPLETE / FINAL EXPORT CORRECTLY BLOCKED ON HUMAN METADATA**

P8 has reached the first point in the submission chain that cannot be completed from frozen scientific evidence alone.

Completed:

- live revalidation of current Nature Machine Intelligence Article limits and structure;
- live revalidation of initial-submission file rules;
- live revalidation of author/affiliation routing;
- live revalidation of cover-letter disclosures;
- live revalidation of double-anonymized review routing;
- live revalidation of competing-interest requirements;
- cover letter v0.3 prepared with explicit non-guessed completion fields;
- machine-readable portal metadata template frozen;
- Supplementary Information v0.3 cleaned so no unmaterialized supplementary-figure plan is submitted;
- 5/5 main figure assets inventoried and present.

Not yet executable without the author's verified input:

- choice of standard vs double-anonymized review;
- publication-form author name;
- affiliation;
- correspondence email/name;
- competing-interest declaration;
- related-manuscript disclosure;
- prior-editor-discussion disclosure.

Therefore:

`portal_ready = false`

and

`final_export_status = BLOCKED_ON_VERIFIED_HUMAN_METADATA`.

Next gate:

`NMI_P8H_METADATA_BIND_AND_FINAL_EXPORT`.

This is not a scientific or engineering failure. It is the intended human-authorization boundary before generating the actual upload files.

No new experiment, theory expansion, semantic adjudication or evidence mutation occurred.
