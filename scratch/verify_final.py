import os
import win32com.client

def verify_final():
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    
    doc_path = os.path.abspath('doc/DataMining_Report.docx')
    wdoc = word.Documents.Open(doc_path, ReadOnly=True)
    wdoc.Repaginate()
    
    print("Document Pages Count:", wdoc.ComputeStatistics(2)) # wdStatisticPages = 2
    
    # Read first table (TOC)
    tbl = wdoc.Tables(1)
    print(f"TOC Table has {tbl.Rows.Count} rows and {tbl.Columns.Count} columns.")
    
    print("\n--- SAMPLE TOC ROWS ---")
    for r in range(1, min(12, tbl.Rows.Count + 1)):
        c1 = tbl.Cell(r, 1).Range.Text.strip().replace('\r', '').replace('\x07', '')
        c2 = tbl.Cell(r, 2).Range.Text.strip().replace('\r', '').replace('\x07', '')
        c3 = tbl.Cell(r, 3).Range.Text.strip().replace('\r', '').replace('\x07', '')
        print(f"Row {r:2d}: {c1:12s} | {c2:45s} | Page {c3}")

    print("\n--- CHAPTER 4 TOC ROWS ---")
    for r in range(17, 23):
        c1 = tbl.Cell(r, 1).Range.Text.strip().replace('\r', '').replace('\x07', '')
        c2 = tbl.Cell(r, 2).Range.Text.strip().replace('\r', '').replace('\x07', '')
        c3 = tbl.Cell(r, 3).Range.Text.strip().replace('\r', '').replace('\x07', '')
        print(f"Row {r:2d}: {c1:12s} | {c2:45s} | Page {c3}")

    print("\n--- FINAL TOC ROWS ---")
    for r in range(tbl.Rows.Count - 4, tbl.Rows.Count + 1):
        c1 = tbl.Cell(r, 1).Range.Text.strip().replace('\r', '').replace('\x07', '')
        c2 = tbl.Cell(r, 2).Range.Text.strip().replace('\r', '').replace('\x07', '')
        c3 = tbl.Cell(r, 3).Range.Text.strip().replace('\r', '').replace('\x07', '')
        print(f"Row {r:2d}: {c1:12s} | {c2:45s} | Page {c3}")

    wdoc.Close(False)
    word.Quit()
    print("\nVerification completed successfully!")

if __name__ == '__main__':
    verify_final()
