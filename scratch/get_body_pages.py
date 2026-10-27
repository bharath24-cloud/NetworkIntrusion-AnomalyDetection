import os
import win32com.client

def query_exact_body_pages():
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    
    doc_path = os.path.abspath('doc/DataMining_Report_cleaned.docx')
    wdoc = word.Documents.Open(doc_path, ReadOnly=True)
    wdoc.Repaginate()
    
    # We want to find the heading in the body (after the TOC table)
    # The TOC is the first table in the document
    toc_tbl = wdoc.Tables(1)
    toc_end = toc_tbl.Range.End
    
    headings_to_query = [
        ("ABSTRACT", "ABSTRACT"),
        ("1", "CHAPTER 1"),
        ("1.1", "1.1 Problem Statement"),
        ("1.2", "1.2 Motivation"),
        ("1.3", "1.3 Objectives"),
        ("2", "CHAPTER 2"),
        ("2.1", "2.1 Dataset Source"),
        ("2.2", "2.2 Number of Records"),
        ("2.3", "2.3 Attributes"),
        ("2.4", "2.4 Target Variable"),
        ("3", "CHAPTER 3"),
        ("3.1", "3.1 Missing & Infinite"),
        ("3.2", "3.2 Data Cleaning"),
        ("3.3", "3.3 Feature Transformation"),
        ("3.4", "3.4 Normalization & Split"),
        ("4", "CHAPTER 4"),
        ("4.1", "4.1 Data Mining Process"),
        ("4.2", "4.2 Exploratory Data Mining"),
        ("4.3", "4.3 Supervised Classification"),
        ("4.4", "4.4 Semi-Supervised Anomaly"),
        ("4.5", "4.5 Class Imbalance"),
        ("5", "CHAPTER 5"),
        ("5.1", "5.1 Python Development"),
        ("5.2", "5.2 Implementation Pipeline"),
        ("5.3", "5.3 Parameters & Configurations"),
        ("6", "CHAPTER 6"),
        ("6.1", "6.1 Tables"),
        ("6.2", "6.2 Graphs"),
        ("6.3", "6.3 Evaluation Metrics"),
        ("7", "CHAPTER 7"),
        ("7.1", "7.1 Algorithm Comparison"),
        ("7.2", "7.2 Advantages"),
        ("7.3", "7.3 Limitations"),
        ("8", "CHAPTER 8"),
        ("8.1", "8.1 Conclusion"),
        ("8.2", "8.2 Future Scope"),
        ("REFERENCES", "REFERENCES"),
    ]
    
    wdActiveEndPageNumber = 3
    results = {}
    
    for tag, search_text in headings_to_query:
        # Create a range starting after the TOC table
        rng = wdoc.Range(Start=toc_end, End=wdoc.Content.End)
        find_obj = rng.Find
        find_obj.ClearFormatting()
        find_obj.Text = search_text
        find_obj.Forward = True
        find_obj.Wrap = 0 # wdFindStop
        
        found = find_obj.Execute()
        if found:
            page_num = rng.Information(wdActiveEndPageNumber)
            results[tag] = page_num
            print(f"{tag:12s} ({search_text:28s}) -> Page {page_num}")
        else:
            print(f"{tag:12s} ({search_text:28s}) -> NOT FOUND")
            
    wdoc.Close(False)
    word.Quit()
    return results

if __name__ == '__main__':
    query_exact_body_pages()
