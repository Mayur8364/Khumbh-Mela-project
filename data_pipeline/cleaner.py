import sqlite3
import re
import hashlib
from bs4 import BeautifulSoup
from db_manager import get_db_connection

# Common HTML tags to strip completely
STRIP_TAGS = ['script', 'style', 'header', 'footer', 'nav', 'aside', 'noscript', 'iframe', 'svg', 'form']

def clean_html_content(raw_html):
    """Parses raw HTML and extracts clean body text, removing boilerplates and ads."""
    if not raw_html:
        return ""
        
    try:
        soup = BeautifulSoup(raw_html, 'html.parser')
        
        # 1. Remove unnecessary interactive/design elements
        for tag in soup(STRIP_TAGS):
            tag.decompose()
            
        # 2. Decompose known advertisement and widget elements by class/id keywords safely
        to_decompose = []
        for elem in soup.find_all(True):
            if not hasattr(elem, 'get') or elem.attrs is None:
                continue
                
            classes = elem.get('class', [])
            if classes is None:
                classes = []
            elif isinstance(classes, str):
                classes = [classes]
                
            element_id = elem.get('id', '')
            if element_id is None:
                element_id = ''
                
            attrs_str = " ".join(classes) + " " + str(element_id)
            if re.search(r'\b(ads|ad-container|advertisement|popup|social-share|related-links|footer-links|navigation|sidebar|widget|menu)\b', attrs_str, re.I):
                # Avoid decomposing the entire page body or major sections accidentally if they match
                if elem.name not in ['body', 'html', 'main', 'article']:
                    to_decompose.append(elem)
                    
        for elem in to_decompose:
            try:
                elem.decompose()
            except Exception:
                pass
                
        # 3. Extract text from remain paragraphs
        paragraphs = []
        for p in soup.find_all(['p', 'div']):
            # If it's a div, only take direct text if it has no nested div/p to avoid repeating text
            if p.name == 'div' and (p.find('p') or p.find('div')):
                continue
                
            text = p.text.strip()
            # Filter out short boilerplates or empty strings
            if len(text) > 30 and not text.startswith("Advertisement") and not text.startswith("ALSO READ"):
                # Clean multiple spaces/newlines inside paragraphs
                clean_p = re.sub(r'\s+', ' ', text)
                paragraphs.append(clean_p)
                
        cleaned_text = "\n\n".join(paragraphs)
        return cleaned_text.strip()
    except Exception as e:
        print(f"Failed to clean HTML body: {e}")
        return ""

def calculate_similarity_jaccard(str1, str2):
    """Calculates Jaccard similarity index between token sets of two strings."""
    words1 = set(re.findall(r'\w+', str1.lower()))
    words2 = set(re.findall(r'\w+', str2.lower()))
    if not words1 or not words2:
        return 0.0
    return len(words1.intersection(words2)) / len(words1.union(words2))

def deduplicate_articles():
    """Identifies and marks duplicate articles (especially wire reports) in the database."""
    print("Starting deduplication engine...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Select all active articles (not already flagged as duplicates)
    cursor.execute("""
        SELECT id, headline, publish_date, source, url 
        FROM articles 
        WHERE status != 'duplicate' 
        ORDER BY publish_date DESC
    """)
    rows = cursor.fetchall()
    
    duplicates_count = 0
    checked_ids = set()
    
    for i in range(len(rows)):
        row_i = rows[i]
        id_i = row_i['id']
        if id_i in checked_ids:
            continue
            
        headline_i = row_i['headline']
        date_i = row_i['publish_date']
        
        # Compare with subsequent articles in a narrow temporal window (e.g. same day)
        for j in range(i + 1, len(rows)):
            row_j = rows[j]
            id_j = row_j['id']
            if id_j in checked_ids:
                continue
                
            # If publication dates differ by more than 1 day, we can stop comparing (since rows are sorted)
            try:
                date_object_i = re.findall(r'\d+', date_i)
                date_object_j = re.findall(r'\d+', row_j['publish_date'])
                # Simple check: if dates are completely different years/months, no need to compare
                if date_object_i[0] != date_object_j[0] or date_object_i[1] != date_object_j[1]:
                    break
            except Exception:
                pass
                
            # Compute Jaccard similarity on headlines
            sim = calculate_similarity_jaccard(headline_i, row_j['headline'])
            
            # If similarity is very high (> 75%), mark the second one as duplicate
            if sim >= 0.75:
                # Mark as duplicate in database
                cursor.execute("UPDATE articles SET status = 'duplicate' WHERE id = ?", (id_j,))
                checked_ids.add(id_j)
                duplicates_count += 1
                print(f"Flagged duplicate article: '{row_j['headline']}' (Source: {row_j['source']}) -> Matches: '{headline_i}'")
                
        checked_ids.add(id_i)
        
    conn.commit()
    conn.close()
    print(f"Deduplication complete. Flagged {duplicates_count} duplicate articles.")

def clean_database_pipeline():
    """Fetches all uncleaned raw bodies, cleans the HTML, and runs deduplication safely."""
    print("=== Starting Phase 4: Cleaning & Deduplication ===")
    
    # 1. Fetch raw articles that have HTML body text loaded
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, raw_body, headline FROM articles WHERE status = 'raw' AND raw_body IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()
    
    print(f"Found {len(rows)} raw article bodies to clean.")
    cleaned_count = 0
    
    for row in rows:
        clean_text = clean_html_content(row['raw_body'])
        
        # Write clean results to DB in a small individual transaction to avoid locks
        conn_inner = get_db_connection()
        cursor_inner = conn_inner.cursor()
        
        if clean_text:
            # Generate stable hash signature based on cleaned text to prevent duplicate entries
            hash_sig = hashlib.sha256(clean_text.encode('utf-8')).hexdigest()
            try:
                cursor_inner.execute("""
                    UPDATE articles 
                    SET clean_body = ?, hash_signature = ?, status = 'cleaned' 
                    WHERE id = ?
                """, (clean_text, hash_sig, row['id']))
                conn_inner.commit()
                cleaned_count += 1
            except sqlite3.IntegrityError:
                # Integrity error means hash_signature already exists -> this is an exact duplicate!
                cursor_inner.execute("UPDATE articles SET status = 'duplicate' WHERE id = ?", (row['id'],))
                conn_inner.commit()
                print(f"Flagged exact duplicate hash for: {row['headline']}")
            except Exception as e:
                print(f"Error saving clean article [{row['id']}]: {e}")
        else:
            try:
                cursor_inner.execute("UPDATE articles SET status = 'failed' WHERE id = ?", (row['id'],))
                conn_inner.commit()
            except Exception as e:
                print(f"Error marking failed article [{row['id']}]: {e}")
                
        conn_inner.close()
        
    print(f"HTML Cleaning complete. Successfully cleaned {cleaned_count} articles.")
    
    # 2. Run Headline-similarity Deduplication
    deduplicate_articles()

if __name__ == "__main__":
    clean_database_pipeline()
