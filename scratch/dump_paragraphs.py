import docx

doc = docx.Document('doc/DataMining_Report.docx')
with open('scratch/all_paragraphs.txt', 'w', encoding='utf-8') as f:
    for i, p in enumerate(doc.paragraphs):
        f.write(f'--- P{i} [{p.style.name}] (bold={any(r.bold for r in p.runs)}) ---\n')
        f.write(p.text + '\n\n')

print('Wrote all paragraphs to scratch/all_paragraphs.txt')
