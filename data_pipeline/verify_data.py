import sqlite3
import re
from db_manager import get_db_connection

def verify_dataset():
    print("=== Executing Database Content Validation & Verification ===")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Check Date Range Integrity
    cursor.execute("""
        SELECT 
            MIN(publish_date) as earliest, 
            MAX(publish_date) as latest, 
            count(*) as total 
        FROM articles 
        WHERE status = 'cleaned'
    """)
    stats = cursor.fetchone()
    print(f"\n1. Temporal Range Check:")
    print(f"   - Earliest Article Date: {stats['earliest']}")
    print(f"   - Latest Article Date:   {stats['latest']}")
    print(f"   - Total Cleaned Records: {stats['total']}")
    
    # Check if dates fall strictly into the Nashik 2015 and Prayagraj 2025 windows
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN publish_date BETWEEN '2014-07-14' AND '2016-09-25' THEN 1 ELSE 0 END) as count_2015,
            SUM(CASE WHEN publish_date BETWEEN '2024-01-14' AND '2026-02-26' THEN 1 ELSE 0 END) as count_2025
        FROM articles
        WHERE status = 'cleaned'
    """)
    windows = cursor.fetchone()
    print(f"   - Nashik 2015 Window articles (2014-2016): {windows['count_2015']}")
    print(f"   - Prayagraj 2025 Window articles (2024-2026): {windows['count_2025']}")
    
    # 2. Check Keyword Relevance (Semantic Scoping)
    print(f"\n2. Keyword Scoping & Relevance Check:")
    cursor.execute("SELECT headline, clean_body FROM articles WHERE status = 'cleaned'")
    rows = cursor.fetchall()
    
    kumbh_kw_count = 0
    nashik_kw_count = 0
    prayagraj_kw_count = 0
    infra_kw_count = 0
    health_kw_count = 0
    crowd_kw_count = 0
    
    for row in rows:
        text = (row['headline'] + " " + row['clean_body']).lower()
        if any(w in text for w in ["kumbh", "simhastha", "mela"]):
            kumbh_kw_count += 1
        if any(w in text for w in ["nashik", "trimbakeshwar", "godavari"]):
            nashik_kw_count += 1
        if any(w in text for w in ["prayagraj", "allahabad", "sangam", "ganga", "ganges"]):
            prayagraj_kw_count += 1
        if any(w in text for w in ["road", "bridge", "flyover", "sanitation", "toilet", "sewage", "infrastructure", "electricity", "power", "ghat"]):
            infra_kw_count += 1
        if any(w in text for w in ["health", "hospital", "camp", "disease", "epidemic", "outbreak", "medical"]):
            health_kw_count += 1
        if any(w in text for w in ["crowd", "stampede", "safety", "policing", "security", "density", "lost", "missing"]):
            crowd_kw_count += 1
            
    total = len(rows)
    print(f"   - Articles containing 'Kumbh / Simhastha / Mela': {kumbh_kw_count} ({kumbh_kw_count/total*100:.1f}%)")
    print(f"   - Articles mentioning 'Nashik / Trimbakeshwar / Godavari': {nashik_kw_count} ({nashik_kw_count/total*100:.1f}%)")
    print(f"   - Articles mentioning 'Prayagraj / Sangam / Ganga': {prayagraj_kw_count} ({prayagraj_kw_count/total*100:.1f}%)")
    print(f"   - Articles covering 'Infrastructure / Sanitation / River Works': {infra_kw_count} ({infra_kw_count/total*100:.1f}%)")
    print(f"   - Articles covering 'Health / Medical Camps / Safety': {health_kw_count} ({health_kw_count/total*100:.1f}%)")
    print(f"   - Articles covering 'Crowd Control / Stampedes / Security': {crowd_kw_count} ({crowd_kw_count/total*100:.1f}%)")
    
    # 3. Sample 5 articles for manual validation print (date, source, headline, length)
    print(f"\n3. Ingested Content Random Samples:")
    cursor.execute("""
        SELECT headline, source, publish_date, length(clean_body) as body_len 
        FROM articles 
        WHERE status = 'cleaned' 
        ORDER BY RANDOM() LIMIT 5
    """)
    samples = cursor.fetchall()
    for idx, s in enumerate(samples):
        # We clean the headline for display
        clean_headline = s['headline'].encode('ascii', errors='ignore').decode('utf-8')
        print(f"   [{idx+1}] [{s['publish_date']}] [{s['source']}]")
        print(f"       Headline: {clean_headline[:100]}")
        print(f"       Clean Body Text Length: {s['body_len']} characters")
        
    conn.close()

if __name__ == "__main__":
    verify_dataset()
