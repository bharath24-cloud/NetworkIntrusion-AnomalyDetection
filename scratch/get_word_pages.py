import os
import win32com.client

def get_heading_pages():
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    
    doc_path = os.path.abspath('doc/DataMining_Report_cleaned.docx')
    print("Opening in Word COM:", doc_path)
    wdoc = word.Documents.Open(doc_path, ReadOnly=True)
    
    # Let Word calculate pagination
    wdoc.Repaginate()
    
    headings_to_find = [
        "ABSTRACT",
        "CHAPTER 1",
        "1.1 Problem Statement",
        "1.2 Motivation",
        "1.3 Objectives",
        "CHAPTER 2",
        "2.1 Dataset Source",
        "2.2 Number of Records",
        "2.3 Attributes",
        "2.4 Target Variable",
        "CHAPTER 3",
        "3.1 Missing & Infinite",
        "3.2 Data Cleaning",
        "3.3 Feature Transformation",
        "3.4 Normalization & Split",
        "CHAPTER 4",
        "4.1 Data Mining Process",
        "4.2 Exploratory Data Mining",
        "4.3 Supervised Classification",
        "4.4 Semi-Supervised Anomaly",
        "4.5 Class Imbalance",
        "CHAPTER 5",
        "5.1 Python Development",
        "5.2 Implementation Pipeline",
        "5.3 Parameters & Configurations",
        "CHAPTER 6",
        "6.1 Tables",
        "6.2 Graphs",
        "6.3 Evaluation Metrics",
        "CHAPTER 7",
        "7.1 Algorithm Comparison",
        "7.2 Advantages",
        "7.3 Limitations",
        "CHAPTER 8",
        "8.1 Conclusion",
        "8.2 Future Scope",
        "REFERENCES"
    ]
    
    wdActiveEndPageNumber = 3 # WdInformation constant
    
    pages = {}
    
    for h in headings_to_find:
        # Search using Word Find
        find_range = wdoc.Content
        find_obj = find_range.Find
        find_obj.ClearFormatting()
        find_obj.Text = h
        find_obj.Forward = True
        find_obj.Wrap = 0 # wdFindStop
        
        found = find_obj.Execute()
        if found:
            page_num = find_range.Information(wdActiveEndPageNumber)
            pages[h] = page_num
            print(f"{h:35s} -> Page {page_num}")
        else:
            print(f"{h:35s} -> NOT FOUND")
            
    wdoc.Close(False)
    word.Quit()
    return pages

if __name__ == '__main__':
    get_heading_pages()
