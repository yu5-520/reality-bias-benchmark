#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "nmi_p8h"
TMP = OUT / "_tmp"
OUT.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)

MANUSCRIPT = ROOT / "docs/submission/nmi/NMI_Manuscript_v0.15_STANDARD.md"
SUPPLEMENT = ROOT / "docs/submission/nmi/NMI_Supplementary_Information_v0.3.md"
COVER = ROOT / "docs/submission/nmi/NMI_Cover_Letter_v0.4_FINAL.md"
FIGDIR = ROOT / "docs/submission/nmi/figures/p5"

FIGS = [
    ("Figure 1", FIGDIR / "Fig1_Process_Reality.svg"),
    ("Figure 2", FIGDIR / "Fig2_Dynamic_CPR.svg"),
    ("Figure 3", FIGDIR / "Fig3_Functional_Semantic_Lineage.svg"),
    ("Figure 4", FIGDIR / "Fig4_Local_Perturbation_Inertia.svg"),
    ("Figure 5", FIGDIR / "Fig5_Lineage_Level_Repair.svg"),
]

def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

# Convert SVG figures to high-resolution PNG for Word/PDF review portability.
import cairosvg
pngs = []
for label, svg in FIGS:
    png = TMP / (svg.stem + ".png")
    # P5 SVGs are human-readable vector assets. Sanitize any bare ampersand
    # before strict XML parsing without mutating the frozen repository source.
    raw = svg.read_text(encoding="utf-8")
    raw = re.sub(r"&(?!#?[A-Za-z0-9]+;)", "&amp;", raw)
    sanitized = TMP / (svg.stem + ".sanitized.svg")
    sanitized.write_text(raw, encoding="utf-8")
    cairosvg.svg2png(url=str(sanitized), write_to=str(png), output_width=2200)
    pngs.append((label, png))

# Insert each materialized main figure immediately after its legend.
m = MANUSCRIPT.read_text(encoding="utf-8")
for idx, (label, png) in enumerate(pngs, start=1):
    pat = re.compile(rf"(\*\*Figure {idx} \|[^\n]*\*\*[^\n]*\n)")
    rel = png.relative_to(ROOT).as_posix()
    replacement = rf"\1\n![{label}]({rel}){{ width=6.3in }}\n"
    m, n = pat.subn(replacement, m, count=1)
    if n != 1:
        raise SystemExit(f"figure legend insertion failed for Figure {idx}")
manuscript_md = TMP / "manuscript_final.md"
manuscript_md.write_text(m, encoding="utf-8")

outputs = {
    "manuscript_docx": OUT / "NMI_Manuscript_Yeyu_Zheng_STANDARD.docx",
    "supplement_docx": OUT / "NMI_Supplementary_Information.docx",
    "cover_docx": OUT / "NMI_Cover_Letter_Yeyu_Zheng.docx",
}

for src, dst in [
    (manuscript_md, outputs["manuscript_docx"]),
    (SUPPLEMENT, outputs["supplement_docx"]),
    (COVER, outputs["cover_docx"]),
]:
    run(
        "pandoc", str(src),
        "--from=markdown+pipe_tables+raw_attribute",
        "--to=docx",
        "--standalone",
        "--output", str(dst),
    )

# Conservative document styling and page numbers.
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.shared import Inches, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def add_page_field(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    run._r.addnext(fld)

def polish(path: Path) -> None:
    doc = Document(str(path))
    for sec in doc.sections:
        sec.top_margin = Inches(0.8)
        sec.bottom_margin = Inches(0.8)
        sec.left_margin = Inches(0.85)
        sec.right_margin = Inches(0.85)
        if not sec.footer.paragraphs:
            p = sec.footer.add_paragraph()
        else:
            p = sec.footer.paragraphs[0]
        add_page_field(p)
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10.5)
    for sname, size in [("Title", 17), ("Heading 1", 13), ("Heading 2", 11.5), ("Heading 3", 10.5)]:
        if sname in styles:
            styles[sname].font.name = "Arial"
            styles[sname].font.size = Pt(size)
    for p in doc.paragraphs:
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.05
    # Keep embedded figures within text width.
    for shape in doc.inline_shapes:
        maxw = Inches(6.3)
        if shape.width > maxw:
            ratio = maxw / shape.width
            shape.width = int(shape.width * ratio)
            shape.height = int(shape.height * ratio)
    doc.core_properties.author = "Yeyu Zheng"
    doc.core_properties.title = "Process reality in multi-agent AI systems"
    doc.save(str(path))

for p in outputs.values():
    polish(p)

# Convert DOCX files to PDF.
for key, docx_path in list(outputs.items()):
    run("libreoffice", "--headless", "--convert-to", "pdf", "--outdir", str(OUT), str(docx_path))

# Normalize expected PDF names.
pdfs = [
    OUT / "NMI_Manuscript_Yeyu_Zheng_STANDARD.pdf",
    OUT / "NMI_Supplementary_Information.pdf",
    OUT / "NMI_Cover_Letter_Yeyu_Zheng.pdf",
]
for p in pdfs:
    if not p.exists():
        raise SystemExit(f"missing converted PDF: {p}")

# Copy original vector figure assets for optional separate upload/reuse.
figout = OUT / "figures"
figout.mkdir(exist_ok=True)
for _, svg in FIGS:
    shutil.copy2(svg, figout / svg.name)

files = [
    outputs["manuscript_docx"], pdfs[0],
    outputs["supplement_docx"], pdfs[1],
    outputs["cover_docx"], pdfs[2],
] + sorted(figout.glob("*.svg"))

manifest = {
    "schema": "RB-NMI-P8H-FINAL-EXPORT-MANIFEST-v1",
    "date": "2026-09-21",
    "peer_review_mode": "STANDARD_SINGLE_ANONYMIZED",
    "author": "Yeyu Zheng",
    "affiliation": "Independent Researcher, Jiangxi, China",
    "corresponding_email": "zhengyeyu520@gmail.com",
    "files": [
        {"name": p.name, "bytes": p.stat().st_size, "sha256": sha256(p)}
        for p in files
    ],
}
manifest_path = OUT / "submission_manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

# Zip only final deliverables, not temp material and never the ZIP itself.
import zipfile
zip_path = OUT / "NMI_P8H_Submission_Package_Yeyu_Zheng.zip"
if zip_path.exists():
    zip_path.unlink()
zip_members = files + [manifest_path]
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for member in zip_members:
        arcname = member.relative_to(OUT).as_posix()
        zf.write(member, arcname=arcname)
print("NMI_P8H_EXPORT=PASS")
print(manifest_path)
print(zip_path)
