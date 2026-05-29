import subprocess
import os
import sqlite3
import csv
from db_manager import get_db_connection

def run_script(script_name):
    print(f"\n==================================================")
    print(f"Executing: {script_name}")
    print(f"==================================================")
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    try:
        # We execute the script using the same python interpreter
        result = subprocess.run(["python", script_path], check=True, text=True, capture_output=True)
        print(result.stdout)
        if result.stderr:
            print("Errors/Warnings:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Execution failed for {script_name} with exit code {e.returncode}:")
        print(e.stdout)
        print(e.stderr)
        raise e

def export_data():
    print("\n==================================================")
    print("Exporting Cleaned Dataset to CSV...")
    print("==================================================")
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Select all active cleaned articles (omitting failed and duplicates)
        cursor.execute("""
            SELECT id, url, source, publish_date, headline, clean_body 
            FROM articles 
            WHERE status = 'cleaned'
            ORDER BY publish_date DESC
        """)
        rows = cursor.fetchall()
        
        csv_path = os.path.join(os.path.dirname(__file__), "articles_export.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(['id', 'url', 'source', 'publish_date', 'headline', 'clean_body'])
            # Write data rows
            for row in rows:
                writer.writerow([row['id'], row['url'], row['source'], row['publish_date'], row['headline'], row['clean_body']])
                
        print(f"Successfully exported {len(rows)} cleaned articles to: {csv_path}")
        
        # Verify stats in DB
        cursor.execute("SELECT status, count(*) FROM articles GROUP BY status")
        stats = cursor.fetchall()
        print("\nDatabase Statistics by Status:")
        for stat in stats:
            print(f"- {stat[0]}: {stat[1]} articles")
            
    except Exception as e:
        print(f"Error exporting data: {e}")
    finally:
        conn.close()

def main():
    print("Kumbh Monitor Data Pipeline Orchestrator")
    print("Running end-to-end data harvesting and cleaning pipeline...")
    
    # Run pipeline phases sequentially
    # Phase 2: Metadata Harvesting
    run_script("collector.py")
    
    # Phase 3: Content Fetching (Downloading raw HTML)
    run_script("fetcher.py")
    
    # Phase 4: Cleaning & Deduplication
    run_script("cleaner.py")
    
    # Phase 5: Export clean CSV
    export_data()
    
    print("\nPipeline run complete. sqlite db and CSV files are fully prepared.")

if __name__ == "__main__":
    main()
