import docx

doc = docx.Document('doc/DataMining_Report.docx')
for i, p in enumerate(doc.paragraphs[:110]):
    txt = p.text.strip()
    has_page_br = 'w:type="page"' in p._p.xml or p.paragraph_format.page_break_before
    if txt or has_page_br:
        print(f'{i:3d}: {txt[:40]:40s} | page_br: {has_page_br}')
