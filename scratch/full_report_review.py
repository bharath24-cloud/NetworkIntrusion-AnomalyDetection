import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

from replacement_texts import (
    REPLACEMENT_P151,
    REPLACEMENT_P161,
    REPLACEMENT_CLEANING_P180_183,
    REPLACEMENT_P303
)

def fix_entire_report():
    doc_path = os.path.abspath('doc/DataMining_Report.docx')
    fixed_path = os.path.abspath('doc/DataMining_Report.docx') # will save directly or to temp first

    print("Opening document:", doc_path)
    doc = docx.Document(doc_path)

    # 1. Clean up leftover retail text in body paragraphs
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        # P151 check (image density / products per image)
        if "density of the images is very high" in t or "products per image has a mean" in t:
            print(f"Replacing retail text in P{i} (P151 replacement)...")
            p.text = REPLACEMENT_P151
            p.style = doc.styles['Normal']
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(11)
                r.font.color.rgb = RGBColor(0, 0, 0)

        # P161 check (Class label / product / bounding box)
        elif "There is only one class, called" in t or "Bounding box. For a region classified" in t:
            print(f"Replacing retail text in P{i} (P161 replacement)...")
            p.text = REPLACEMENT_P161
            p.style = doc.styles['Normal']
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(11)
                r.font.color.rgb = RGBColor(0, 0, 0)

        # P303 check (mAP@50, COCO 80-class)
        elif "During the first three epochs the validation scores stayed low" in t or "mAP@50" in t:
            print(f"Replacing retail text in P{i} (P303 replacement)...")
            p.text = REPLACEMENT_P303
            p.style = doc.styles['Normal']
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(11)
                r.font.color.rgb = RGBColor(0, 0, 0)

    # Replace P180-183 (Image file format check, duplicate box, line format, cross-split image hashes)
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if "File Format Check: Only .jpg" in t:
            print(f"Replacing cleaning P180 at P{i}...")
            p.text = REPLACEMENT_CLEANING_P180_183[0]
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(11)
                r.font.color.rgb = RGBColor(0, 0, 0)
        elif "Line Format Check: Every label line must contain" in t:
            print(f"Replacing cleaning P181 at P{i}...")
            p.text = REPLACEMENT_CLEANING_P180_183[1]
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(11)
                r.font.color.rgb = RGBColor(0, 0, 0)
        elif "Duplicate Box Check:" in t:
            print(f"Replacing cleaning P182 at P{i}...")
            p.text = REPLACEMENT_CLEANING_P180_183[2]
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(11)
                r.font.color.rgb = RGBColor(0, 0, 0)
        elif "Cross-Split Leakage Check: Image hashes" in t:
            print(f"Replacing cleaning P183 at P{i}...")
            p.text = REPLACEMENT_CLEANING_P180_183[3]
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(11)
                r.font.color.rgb = RGBColor(0, 0, 0)

    # 2. Check and strip all <w:numPr> from any headings, remove empty headings
    empty_paras_to_remove = []
    for i, p in enumerate(doc.paragraphs):
        # Check if empty heading
        if p.style.name.startswith('Heading') and not p.text.strip():
            empty_paras_to_remove.append(p)
        # Strip w:numPr if present in heading
        pPr = p._p.pPr
        if pPr is not None and p.style.name.startswith('Heading'):
            numPr = pPr.find(docx.oxml.ns.qn('w:numPr'))
            if numPr is not None:
                pPr.remove(numPr)
                print(f"Stripped automatic numPr from P{i}: {p.text[:40]}")

    for ep in empty_paras_to_remove:
        print("Removing empty heading paragraph...")
        ep._p.getparent().remove(ep._p)

    # 3. Standardize Chapter & Subsection Headings in the Body
    # Ensure all chapters have page_break_before = True, CHAPTER X and TITLE are bold, centered
    # Ensure all subsections have Heading 2, left-aligned, bold, Times New Roman 12pt
    chapters_info = [
        ("CHAPTER 1", "INTRODUCTION"),
        ("CHAPTER 2", "DATASET (UNSW-NB15)"),
        ("CHAPTER 3", "DATA PREPROCESSING"),
        ("CHAPTER 4", "DATA MINING TECHNIQUES"),
        ("CHAPTER 5", "IMPLEMENTATION"),
        ("CHAPTER 6", "RESULTS"),
        ("CHAPTER 7", "COMPARISON AND DISCUSSION"),
        ("CHAPTER 8", "CONCLUSION AND FUTURE SCOPE"),
    ]

    for p in doc.paragraphs:
        txt = p.text.strip()
        for ch_num, ch_title in chapters_info:
            if txt == ch_num:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.page_break_before = True
                p.paragraph_format.space_before = Pt(18)
                p.paragraph_format.space_after = Pt(6)
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(14)
                    r.bold = True
                    r.font.color.rgb = RGBColor(0, 0, 0)
            elif txt == ch_title:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(18)
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(14)
                    r.bold = True
                    r.font.color.rgb = RGBColor(0, 0, 0)

        # Subsection headings (e.g. 1.1, 1.2, 2.1 ...)
        if any(txt.startswith(f"{c}.") for c in range(1, 9)) and len(txt) > 3 and txt[3] == ' ':
            p.style = doc.styles['Heading 2']
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(6)
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
                r.bold = True
                r.font.color.rgb = RGBColor(0, 0, 0)

    # 4. Verify Chapter 4 subsections in body
    # Specifically ensure 4.4 is "4.4 Semi-Supervised Anomaly Detection (Deep Autoencoder)"
    # and 4.5 is "4.5 Class Imbalance & Evaluation Measures"
    for p in doc.paragraphs:
        t = p.text.strip()
        if t.startswith("4.4 ") and "Semi-Supervised" not in t:
            print(f"Renaming P to proper 4.4 Autoencoder heading: {t}")
            p.text = "4.4 Semi-Supervised Anomaly Detection (Deep Autoencoder)"
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
                r.bold = True
        elif t.startswith("4.5 ") and "Class Imbalance" not in t:
            print(f"Renaming P to proper 4.5 Class Imbalance heading: {t}")
            p.text = "4.5 Class Imbalance & Evaluation Measures"
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
                r.bold = True

    # Save intermediate cleaned document
    doc.save('doc/DataMining_Report_cleaned.docx')
    print("Saved intermediate doc/DataMining_Report_cleaned.docx")

if __name__ == '__main__':
    fix_entire_report()
