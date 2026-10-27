import time
import shutil
import sys

src = 'doc/DataMining_Report_fixed.docx'
dst = 'doc/DataMining_Report.docx'

print('Watcher started: waiting for DataMining_Report.docx to unlock...')
for i in range(120): # check for up to 10 minutes
    try:
        with open(dst, 'a') as f:
            pass
        # If we got here, file is writable!
        time.sleep(0.5)
        shutil.copy2(src, dst)
        print('SUCCESS: DataMining_Report.docx was unlocked and updated with the fixed TOC!')
        sys.exit(0)
    except Exception:
        time.sleep(2)

print('Watcher timed out.')
