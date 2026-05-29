import sqlite3
import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from db_manager import get_db_connection

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def fetch_single_article(article_id, url, wayback_url=None):
    """Downloads the HTML body of a single article URL, preferring Wayback snapshots if provided."""
    target_url = wayback_url if wayback_url else url
    print(f"Downloading [{article_id}]: {target_url}")
    
    try:
        r = requests.get(target_url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return article_id, r.text, 'raw'
        else:
            # If wayback failed but original exists, try original as fallback
            if wayback_url and url:
                print(f"Wayback failed (status {r.status_code}) for [{article_id}], attempting direct fallback: {url}")
                r_direct = requests.get(url, headers=HEADERS, timeout=15)
                if r_direct.status_code == 200:
                    return article_id, r_direct.text, 'raw'
            return article_id, None, 'failed'
    except Exception as e:
        # If direct Wayback request timed out, try direct original link if available
        if wayback_url and url:
            try:
                print(f"Wayback error ({e}) for [{article_id}], attempting direct fallback: {url}")
                r_direct = requests.get(url, headers=HEADERS, timeout=15)
                if r_direct.status_code == 200:
                    return article_id, r_direct.text, 'raw'
            except Exception:
                pass
        print(f"Download failed for [{article_id}] {target_url}: {e}")
        return article_id, None, 'failed'

def run_batch_downloader():
    """Fetches all raw articles with missing bodies and downloads their contents in parallel."""
    print("=== Starting Phase 3: Article Content Downloader ===")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Fetch target records
    # We select url, and we can check if there's any wayback snapshot stored
    # Note: We didn't explicitly create a wayback_url column in schema.sql, but we can query wayback URL dynamically 
    # or just use the primary URL. Let's write standard queries.
    cursor.execute("""
        SELECT id, url 
        FROM articles 
        WHERE status = 'raw' AND raw_body IS NULL
    """)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("No pending downloads found in database.")
        return
        
    print(f"Found {len(rows)} articles queue for downloading.")
    
    # 2. Run ThreadPool for concurrent downloading
    downloaded_bodies = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit tasks
        futures = {executor.submit(fetch_single_article, row['id'], row['url']): row for row in rows}
        
        for future in as_completed(futures):
            art_id, html_content, status = future.result()
            if html_content:
                downloaded_bodies.append((html_content, status, art_id))
            else:
                # Mark as failed in DB
                conn_inner = get_db_connection()
                conn_inner.execute("UPDATE articles SET status = 'failed' WHERE id = ?", (art_id,))
                conn_inner.commit()
                conn_inner.close()
                
    # 3. Batch commit downloaded HTML bodies to database
    print(f"Batch saving {len(downloaded_bodies)} successfully downloaded bodies...")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany("""
            UPDATE articles 
            SET raw_body = ?, status = ? 
            WHERE id = ?
        """, downloaded_bodies)
        conn.commit()
        print("Raw bodies successfully saved.")
    except Exception as e:
        conn.rollback()
        print(f"Error saving raw bodies: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_batch_downloader()
