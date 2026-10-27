import os
import shutil
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def finalize_document():
    doc_path = 'doc/DataMining_Report_cleaned.docx'
    doc = docx.Document(doc_path)
    
    # Final Table of Contents Data with exact Word COM page numbers
    final_toc_data = [
        # (Chapter No, Title, Page No, is_main_chapter)
        ("", "ABSTRACT", "7", True),
        ("1", "INTRODUCTION", "9", True),
        ("1.1", "Problem Statement", "9", False),
        ("1.2", "Motivation", "10", False),
        ("1.3", "Objectives", "10", False),
        ("2", "DATASET (UNSW-NB15)", "12", True),
        ("2.1", "Dataset Source", "12", False),
        ("2.2", "Number of Records", "12", False),
        ("2.3", "Attributes Description", "13", False),
        ("2.4", "Target Variable & Attack Categories", "14", False),
        ("3", "DATA PREPROCESSING", "16", True),
        ("3.1", "Missing & Infinite Value Handling", "16", False),
        ("3.2", "Data Cleaning & Leakage Prevention", "16", False),
        ("3.3", "Feature Transformation & Categorical Encoding", "17", False),
        ("3.4", "Normalization & Split Partitioning", "18", False),
        ("4", "DATA MINING TECHNIQUES", "20", True),
        ("4.1", "Data Mining Process (KDD Framework)", "20", False),
        ("4.2", "Exploratory Data Mining & Feature Analysis", "21", False),
        ("4.3", "Supervised Classification (Random Forest)", "21", False),
        ("4.4", "Semi-Supervised Anomaly Detection (Deep Autoencoder)", "22", False),
        ("4.5", "Class Imbalance & Evaluation Measures", "22", False),
        ("5", "IMPLEMENTATION", "24", True),
        ("5.1", "Python Development Environment & Tools", "24", False),
        ("5.2", "Implementation Pipeline & Architecture (KDD)", "25", False),
        ("5.3", "Parameters & Configurations", "26", False),
        ("6", "RESULTS", "27", True),
        ("6.1", "Performance Tables", "27", False),
        ("6.2", "Graphs", "28", False),
        ("6.3", "Evaluation Metrics Analysis", "29", False),
        ("7", "COMPARISON AND DISCUSSION", "31", True),
        ("7.1", "Algorithm Comparison (RF vs. Autoencoder)", "31", False),
        ("7.2", "Advantages", "32", False),
        ("7.3", "Limitations", "32", False),
        ("8", "CONCLUSION AND FUTURE SCOPE", "33", True),
        ("8.1", "Conclusion", "33", False),
        ("8.2", "Future Scope", "33", False),
        ("", "REFERENCES", "34", True),
    ]

    # The TOC table is table[0]
    table = doc.tables[0]
    
    # If the table has fewer rows than final_toc_data + 1, add rows
    total_needed = len(final_toc_data) + 1
    while len(table.rows) < total_needed:
        table.add_row()
    while len(table.rows) > total_needed:
        # remove last row
        row = table.rows[-1]
        row._tr.getparent().remove(row._tr)

    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    col_widths = [Inches(1.4), Inches(3.8), Inches(0.8)]

    # Borderless styling
    tblPr = table._tbl.tblPr
    # Remove existing borders if any
    for b in tblPr.findall(docx.oxml.ns.qn('w:tblBorders')):
        tblPr.remove(b)
    tblBorders = parse_xml(
        r'<w:tblBorders %s>'
        r'  <w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        r'  <w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        r'  <w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        r'  <w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        r'  <w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        r'  <w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        r'</w:tblBorders>' % nsdecls('w')
    )
    tblPr.append(tblBorders)

    # Style Header Row
    hdr_cells = table.rows[0].cells
    headers = ["CHAPTER NO.", "TITLE", "PAGE NO."]
    hdr_alignments = [WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT]

    for i, h_text in enumerate(headers):
        cell = hdr_cells[i]
        cell.width = col_widths[i]
        p = cell.paragraphs[0]
        p.text = ""
        p.alignment = hdr_alignments[i]
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(h_text)
        run.font.name = "Times New Roman"
        run.font.size = Pt(11)
        run.bold = True
        run.font.color.rgb = RGBColor(0, 0, 0)

    # Populate Data Rows
    for r_idx, (chap_no, title, page_no, is_main) in enumerate(final_toc_data):
        row_cells = table.rows[r_idx + 1].cells

        # Col 0: CHAPTER NO.
        c0 = row_cells[0]
        c0.width = col_widths[0]
        p0 = c0.paragraphs[0]
        p0.text = ""
        p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p0.paragraph_format.space_before = Pt(2.0 if is_main else 1.0)
        p0.paragraph_format.space_after = Pt(2.0 if is_main else 1.0)
        p0.paragraph_format.line_spacing = 1.15
        if chap_no:
            r0 = p0.add_run(chap_no)
            r0.font.name = "Times New Roman"
            r0.font.size = Pt(11)
            r0.bold = is_main
            r0.font.color.rgb = RGBColor(0, 0, 0)

        # Col 1: TITLE
        c1 = row_cells[1]
        c1.width = col_widths[1]
        p1 = c1.paragraphs[0]
        p1.text = ""
        p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p1.paragraph_format.space_before = Pt(2.0 if is_main else 1.0)
        p1.paragraph_format.space_after = Pt(2.0 if is_main else 1.0)
        p1.paragraph_format.line_spacing = 1.15
        r1 = p1.add_run(title)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(11)
        r1.bold = is_main
        r1.font.color.rgb = RGBColor(0, 0, 0)

        # Col 2: PAGE NO.
        c2 = row_cells[2]
        c2.width = col_widths[2]
        p2 = c2.paragraphs[0]
        p2.text = ""
        p2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p2.paragraph_format.space_before = Pt(2.0 if is_main else 1.0)
        p2.paragraph_format.space_after = Pt(2.0 if is_main else 1.0)
        p2.paragraph_format.line_spacing = 1.15
        r2 = p2.add_run(page_no)
        r2.font.name = "Times New Roman"
        r2.font.size = Pt(11)
        r2.bold = is_main
        r2.font.color.rgb = RGBColor(0, 0, 0)

    # Set explicit column width on every cell
    for row in table.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = w

    # Verify all headings in body match the exact titles
    print("Verifying body headings...")
    for p in doc.paragraphs:
        txt = p.text.strip()
        if txt == "2.3 Attributes":
            p.text = "2.3 Attributes Description"
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
                r.bold = True
        elif txt == "5.2 Implementation Pipeline & Architecture":
            p.text = "5.2 Implementation Pipeline & Architecture (KDD)"
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
                r.bold = True
        elif txt == "6.1 Tables":
            p.text = "6.1 Performance Tables"
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
                r.bold = True
        elif txt == "7.1 Algorithm Comparison":
            p.text = "7.1 Algorithm Comparison (RF vs. Autoencoder)"
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
                r.bold = True

    # Save to doc/DataMining_Report_final.docx
    final_output = 'doc/DataMining_Report_final.docx'
    doc.save(final_output)
    print(f"Saved {final_output} successfully!")

    # Copy to DataMining_Report.docx and DataMining_Report_fixed.docx
    for target in ['doc/DataMining_Report.docx', 'doc/DataMining_Report_fixed.docx', 'doc/DataMining_Report_updated.docx']:
        try:
            shutil.copy2(final_output, target)
            print(f"Updated {target} successfully!")
        except Exception as e:
            print(f"Could not overwrite {target}: {e}")

if __name__ == '__main__':
    finalize_document()
