import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def inspect_and_build():
    doc = docx.Document('doc/DataMining_Report.docx')
    for i in range(140, 155):
        p = doc.paragraphs[i]
        print(f'{i}: {repr(p.text)} | w:br: {"w:br" in p._p.xml} | page_break_before: {p.paragraph_format.page_break_before}')

if __name__ == '__main__':
    inspect_and_build()
