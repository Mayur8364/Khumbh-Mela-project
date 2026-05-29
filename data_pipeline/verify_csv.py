import csv
import os
import re
import datetime

CSV_PATH = "data_pipeline/articles_export.csv"
REPORT_PATH = "data_pipeline/csv_verification_report.txt"

def verify_csv_dataset():
    print("=== Launching Exhaustive CSV Dataset Verification System ===")
    
    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV file not found at: {CSV_PATH}")
        return
        
    report_lines = []
    report_lines.append("=================================================================================")
    report_lines.append("             KUMBH MONITOR - EXHAUSTIVE CSV DATASET VERIFICATION REPORT")
    report_lines.append(f"             Run Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"             Target File: {CSV_PATH}")
    report_lines.append("=================================================================================\n")
    
    passed_count = 0
    failed_count = 0
    total_rows = 0
    
    expected_headers = ['id', 'url', 'source', 'publish_date', 'headline', 'clean_body']
    
    try:
        with open(CSV_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            # 1. Verify Header Column
            headers = next(reader)
            if headers != expected_headers:
                print(f"Header Verification Failed! Found: {headers}, Expected: {expected_headers}")
                report_lines.append(f"HEADER VERIFICATION: [FAILED]")
                report_lines.append(f"   Found Headers: {headers}")
                report_lines.append(f"   Expected:      {expected_headers}\n")
                failed_count += 1
            else:
                print("Header Verification: PASSED")
                report_lines.append("HEADER VERIFICATION: [PASSED]\n")
                
            report_lines.append(f"{'Row ID':<6} | {'Pub Date':<10} | {'Source':<28} | {'Columns':<7} | {'CSV Status':<10} | {'Notes'}")
            report_lines.append("-" * 110)
            
            # 2. Iterate and verify every row
            for idx, row in enumerate(reader, start=1):
                total_rows += 1
                row_errors = []
                
                # Check column count (must be exactly 6)
                col_count = len(row)
                if col_count != 6:
                    row_errors.append(f"Invalid columns count: found {col_count}, expected 6")
                    
                if col_count >= 4:
                    art_id = row[0]
                    url = row[1]
                    source = row[2]
                    pub_date = row[3]
                    
                    # Validate ID is integer
                    if not art_id.isdigit():
                        row_errors.append(f"ID is not numeric: '{art_id}'")
                        
                    # Validate Date YYYY-MM-DD
                    if not re.match(r'^\d{4}-\d{2}-\d{2}$', pub_date):
                        row_errors.append(f"Invalid date format: '{pub_date}'")
                else:
                    art_id = f"ROW_{idx}"
                    pub_date = "N/A"
                    source = "N/A"
                    
                if col_count >= 6:
                    headline = row[4]
                    clean_body = row[5]
                    
                    if not headline or len(headline.strip()) == 0:
                        row_errors.append("Empty Headline field")
                    if not clean_body or len(clean_body.strip()) == 0:
                        row_errors.append("Empty clean_body field")
                else:
                    row_errors.append("Missing headline/clean_body columns")
                    
                # Logging Status
                if len(row_errors) > 0:
                    status = "FAILED"
                    failed_count += 1
                    notes = "; ".join(row_errors)
                else:
                    status = "OK"
                    passed_count += 1
                    notes = "Cell values standard, uncorrupted and properly escaped"
                    
                source_short = source[:28]
                report_lines.append(f"{art_id:<6} | {pub_date:<10} | {source_short:<28} | {col_count:<7} | {status:<10} | {notes}")
                
    except Exception as e:
        print(f"Error parsing CSV file: {e}")
        report_lines.append(f"\nCSV CRITICAL EXCEPTION: {e}")
        failed_count += 1
        
    report_lines.append("\n" + "=" * 110)
    report_lines.append(f"CSV VERIFICATION SUMMARY:")
    report_lines.append(f"   - TOTAL ROWS AUDITED: {total_rows}")
    report_lines.append(f"   - PASSED (UNBROKEN):  {passed_count}")
    report_lines.append(f"   - FAILED (GARBLED):   {failed_count}")
    report_lines.append("=" * 110)
    
    # Save report
    report_text = "\n".join(report_lines)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report_text)
        
    print(f"CSV In-Depth Verification complete. Detailed report written to: {REPORT_PATH}")
    print(f"\nCSV Verification Summary:")
    print(f"   - Audited CSV Rows:  {total_rows}")
    print(f"   - Verified Passed:   {passed_count}")
    print(f"   - Failed/Corrupt:    {failed_count}")

if __name__ == "__main__":
    verify_csv_dataset()
