import sqlite3
from googlenewsdecoder import gnewsdecoder
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from db_manager import get_db_connection

def resolve_url_task(article_id, google_url):
    try:
        print(f"Resolving redirect for article [{article_id}]...")
        decoded = gnewsdecoder(google_url)
        if decoded.get("status"):
            real_url = decoded["decoded_url"]
            # Estimate clean source from decoded url netloc
            domain = urllib.parse.urlparse(real_url).netloc
            source = domain.replace("www.", "")
            return article_id, real_url, source
    except Exception as e:
        print(f"Error resolving [{article_id}]: {e}")
    return article_id, None, None

def run_url_resolution_pipeline():
    print("=== Starting Google News Link Resolution Engine ===")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch all articles where url contains news.google.com
    cursor.execute("""
        SELECT id, url 
        FROM articles 
        WHERE url LIKE '%news.google.com%'
    """)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("No unresolved Google News links found in the database.")
        return
        
    print(f"Found {len(rows)} Google News links to resolve.")
    
    resolved_data = []
    
    # Resolve in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(resolve_url_task, row['id'], row['url']): row for row in rows}
        
        for future in as_completed(futures):
            art_id, real_url, source = future.result()
            if real_url:
                resolved_data.append((real_url, source, art_id))
                
    print(f"Successfully resolved {len(resolved_data)} articles to their original domains.")
    
    # Ingest updates back to DB
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Reset raw_body and clean_body so they can be re-fetched and re-cleaned!
        cursor.executemany("""
            UPDATE articles 
            SET url = ?, source = ?, raw_body = NULL, clean_body = NULL, status = 'raw' 
            WHERE id = ?
        """, resolved_data)
        conn.commit()
        print("Database successfully updated with original destination URLs and status reset to 'raw'.")
    except Exception as e:
        conn.rollback()
        print(f"Database update failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_url_resolution_pipeline()
