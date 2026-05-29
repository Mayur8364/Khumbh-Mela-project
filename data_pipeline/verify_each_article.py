import sqlite3
import re
import datetime
from db_manager import get_db_connection

def verify_each_and_every_article():
    print("=== Launching Exhaustive Article Verification System ===")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch all cleaned articles
    cursor.execute("""
        SELECT id, url, source, publish_date, headline, clean_body 
        FROM articles 
        WHERE status = 'cleaned'
        ORDER BY id ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    report_lines = []
    report_lines.append("=================================================================================")
    report_lines.append("             KUMBH MONITOR - EXHAUSTIVE ARTICLE VERIFICATION REPORT")
    report_lines.append(f"             Run Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"             Total Cleaned Articles Checked: {len(rows)}")
    report_lines.append("=================================================================================\n")
    
    passed_count = 0
    failed_count = 0
    warnings_count = 0
    
    report_lines.append(f"{'ID':<4} | {'Date':<10} | {'Source':<28} | {'Body Len':<8} | {'Verif Status':<12} | {'Notes'}")
    report_lines.append("-" * 110)
    
    for row in rows:
        art_id = row['id']
        date_str = row['publish_date']
        source = row['source']
        headline = row['headline']
        body = row['clean_body']
        url = row['url']
        
        errors = []
        warnings = []
        
        # 1. Headline Checks
        if not headline or len(headline.strip()) == 0:
            errors.append("Empty Headline")
        elif len(headline) < 10:
            warnings.append("Headline too short")
        elif headline.startswith("http"):
            errors.append("Headline is a URL")
            
        # 2. Date Checks
        is_date_valid = False
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            is_date_valid = True
        except ValueError:
            errors.append(f"Invalid Date format: {date_str}")
            
        if is_date_valid:
            # Check windows
            is_2015 = datetime.datetime.strptime('2014-07-14', "%Y-%m-%d").date() <= dt <= datetime.datetime.strptime('2016-09-25', "%Y-%m-%d").date()
            is_2025 = datetime.datetime.strptime('2024-01-14', "%Y-%m-%d").date() <= dt <= datetime.datetime.strptime('2026-02-26', "%Y-%m-%d").date()
            if not (is_2015 or is_2025):
                warnings.append(f"Date outside core windows (Nashik 2015 / Prayagraj 2025)")
                
        # 3. Source Checks
        if not source or len(source.strip()) == 0 or source == "Unknown":
            errors.append("Unknown Source")
            
        # 4. Clean Body Checks
        body_len = len(body) if body else 0
        if body_len == 0:
            errors.append("Clean body is completely empty")
        elif body_len < 150:
            warnings.append("Clean body extremely short")
            
        # 5. Semantic scoping check (check if Kumbh related)
        text_lower = (headline + " " + (body if body else "")).lower()
        has_kw = any(w in text_lower for w in ["kumbh", "simhastha", "mela", "bath", "ghat", "snan", "sadhu", "akhada", "pilgrim", "prayagraj", "nashik"])
        if not has_kw:
            warnings.append("No core Kumbh/Simhastha keywords detected in text")
            
        # 6. Status determination
        if len(errors) > 0:
            status = "FAILED"
            failed_count += 1
            notes = ", ".join(errors)
        elif len(warnings) > 0:
            status = "PASSED (WARN)"
            warnings_count += 1
            notes = ", ".join(warnings)
            passed_count += 1
        else:
            status = "PASSED"
            passed_count += 1
            notes = "Fully Verified"
            
        # Trim source for clean print
        source_short = source[:28]
        report_lines.append(f"{art_id:<4} | {date_str:<10} | {source_short:<28} | {body_len:<8} | {status:<12} | {notes}")
        
    report_lines.append("\n" + "=" * 110)
    report_lines.append(f"VERIFICATION SUMMARY:")
    report_lines.append(f"   - TOTAL CHECKED:      {len(rows)}")
    report_lines.append(f"   - PASSED (PERFECT):   {passed_count - warnings_count}")
    report_lines.append(f"   - PASSED (WITH WARN): {warnings_count}")
    report_lines.append(f"   - FAILED:             {failed_count}")
    report_lines.append("=" * 110)
    
    # Save detailed report to text file
    report_text = "\n".join(report_lines)
    report_path = "data_pipeline/detailed_verification_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
        
    print(f"Exhaustive verification finished. Detailed report written to: {report_path}")
    
    # Print the summary metrics to console
    print(f"\nExhaustive Summary:")
    print(f"   - Verified Cleaned Articles: {len(rows)}")
    print(f"   - Perfect Passed:            {passed_count - warnings_count}")
    print(f"   - Passed with Warnings:      {warnings_count}")
    print(f"   - Failed:                    {failed_count}")

if __name__ == "__main__":
    verify_each_and_every_article()
