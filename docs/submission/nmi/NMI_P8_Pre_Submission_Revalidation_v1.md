# NMI-P8 Pre-Submission Revalidation v1

Date: 2026-09-21  
Status: **LIVE JOURNAL REVALIDATION COMPLETE / FINAL EXPORT WAITING FOR VERIFIED HUMAN METADATA**

P8 re-checked the current Nature Machine Intelligence initial-submission requirements against the frozen P7 package.

## Live revalidation result

| Current requirement | Frozen package |
| --- | --- |
| Article main text ≤ 3,500 words | PASS — 2,942 |
| Abstract ≤ 150 words, unreferenced | PASS — 147 |
| ≤ 6 display items | PASS — 5 main figures |
| Introduction without heading | PASS |
| Results present with topical subheadings | PASS |
| Discussion present without subheadings | PASS |
| Methods present with topical subheadings | PASS |
| Reference list | PASS — 12 references |
| Data Availability | PASS |
| Code Availability | PASS |
| LLM use disclosed in Methods | PASS |
| Cover letter explains importance / NMI relevance | PASS |
| Supplementary Information | PASS — assembled v0.3 |
| Initial Word/PDF accepted | PASS as planned |
| Author names / affiliations | WAITING VERIFIED HUMAN METADATA unless double-anonymized is selected |
| Competing-interest declaration | WAITING VERIFIED HUMAN DECLARATION |
| Related-manuscript disclosure | WAITING AUTHOR CONFIRMATION |
| Prior-editor-discussion disclosure | WAITING AUTHOR CONFIRMATION |
| Peer-review model | WAITING AUTHOR SELECTION |
| Public archive DOI/URL | OPTIONAL/PENDING — must not be invented |

## Important live-rule correction

P7 correctly kept author metadata outside the scientific freeze, but the current Nature Machine Intelligence preparing-submission page makes the routing explicit:

- standard review → names and affiliations belong in the manuscript;
- double-anonymized review → manuscript must conceal identities and author affiliation/contact information moves to the cover letter.

Because the review model has not been selected by the author, P8 must not silently choose either route.

## Cover-letter update

`NMI_Cover_Letter_v0.3.md` now contains explicit completion fields for:

- related manuscripts;
- prior NMI editor discussions;
- peer-review mode;
- competing interests;
- double-anonymized identity block if selected.

The scientific significance text is unchanged in substance.

## Export decision

Final Word/PDF upload files are **not** generated as falsely final artifacts before the author metadata route is known. This avoids producing a standard-review manuscript without required author information or a double-anonymized manuscript paired with an incomplete identity cover letter.

The export stage is therefore mechanically ready but correctly blocked on human-owned metadata.

## Zero-change scientific boundary

P8 revalidation used:

- 0 new subject runs;
- 0 provider/evaluator experiment calls;
- 0 new semantic adjudications;
- 0 evidence mutations;
- 0 theory expansion.

## Resume condition

Once the required fields in `configs/nmi_p8_portal_metadata_template_v1.json` are supplied, P8 can immediately:

1. route standard vs double-anonymized packaging;
2. inject only the verified metadata;
3. generate final DOCX/PDF files;
4. render and visually verify every page;
5. freeze a final upload manifest.


## P8 supplement cleanup

The P7 Supplementary Information contained a planning-only “Supplementary Figure plan” without corresponding submission figure assets. P8 removed that planning surface from the actual submission-facing Supplementary Information v0.3.

The resulting Supplementary Information contains only material that is actually present: evidence-accounting notes and tables. Repository-only audit visualizations are not represented as submission display items.

All five **main** figure assets are present and frozen in:

`docs/submission/nmi/NMI_P8_Figure_Asset_Inventory_v1.md`.
