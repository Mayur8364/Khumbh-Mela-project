import requests
import xml.etree.ElementTree as ET
import urllib.parse
from bs4 import BeautifulSoup
import sqlite3
import os
import time
import re
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from googlenewsdecoder import gnewsdecoder
from config import DB_PATH, KEYWORDS, NEWS_DOMAINS, NASHIK_2015_START, NASHIK_2015_END, PRAYAGRAJ_2025_START, PRAYAGRAJ_2025_END
from db_manager import get_db_connection

# User agent for requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def resolve_google_redirect(google_url):
    """Resolves a Google News redirect URL to its original destination URL using googlenewsdecoder."""
    try:
        decoded = gnewsdecoder(google_url)
        if decoded.get("status"):
            return decoded["decoded_url"]
    except Exception as e:
        print(f"Offline decoder failed for {google_url}: {e}")
        
    # Fallback to standard request redirect follow
    try:
        r = requests.head(google_url, headers=HEADERS, allow_redirects=True, timeout=5)
        return r.url
    except Exception:
        try:
            r = requests.get(google_url, headers=HEADERS, allow_redirects=True, timeout=5)
            return r.url
        except Exception:
            return google_url

def check_wayback_machine(url):
    """Queries Wayback Machine API to find archived snapshots, specifically useful for 2015 content."""
    try:
        api_url = f"https://archive.org/wayback/available?url={urllib.parse.quote(url)}"
        r = requests.get(api_url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            data = r.json()
            snapshots = data.get("archived_snapshots", {})
            closest = snapshots.get("closest", {})
            if closest.get("available"):
                return closest.get("url")
    except Exception as e:
        print(f"Wayback check failed for {url}: {e}")
    return None

def fetch_google_news_rss(query_str):
    """Fetches articles using Google News RSS search for a query string."""
    print(f"Querying Google News RSS for: '{query_str}'")
    articles = []
    try:
        encoded_query = urllib.parse.quote(query_str)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
        
        r = requests.get(rss_url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return articles
            
        root = ET.fromstring(r.content)
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date_str = item.find('pubDate').text if item.find('pubDate') is not None else ""
            source = item.find('source').text if item.find('source') is not None else "Unknown"
            
            # Format title (remove source suffix e.g., " - Times of India")
            headline = title
            if " - " in title:
                headline = " - ".join(title.split(" - ")[:-1])
            
            # Parse Date
            try:
                # e.g., "Thu, 15 Jan 2025 08:00:00 GMT"
                dt = datetime.datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")
                publish_date = dt.strftime("%Y-%m-%d")
            except Exception:
                publish_date = datetime.date.today().strftime("%Y-%m-%d")
                
            articles.append({
                'headline': headline,
                'google_link': link,
                'source': source,
                'publish_date': publish_date
            })
    except Exception as e:
        print(f"Google News RSS query failed: {e}")
    return articles

def fetch_duckduckgo_results(query_str):
    """Scrapes DuckDuckGo HTML/lite search interface for a query string to collect direct links."""
    print(f"Querying DuckDuckGo HTML for: '{query_str}'")
    articles = []
    try:
        encoded_query = urllib.parse.quote(query_str)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return articles
            
        soup = BeautifulSoup(r.content, 'html.parser')
        results = soup.find_all('div', class_='result')
        
        for result in results:
            title_tag = result.find('a', class_='result__url')
            snippet_tag = result.find('a', class_='result__snippet')
            
            if title_tag:
                headline = title_tag.text.strip()
                raw_link = title_tag['href']
                
                # DuckDuckGo wraps links in redirect urls: /l/?kh=-1&uddg=https%3A%2F%2F...
                parsed_url = urllib.parse.urlparse(raw_link)
                qs = urllib.parse.parse_qs(parsed_url.query)
                real_link = qs.get('uddg', [None])[0]
                
                if not real_link:
                    # Fallback if no uddg parameter
                    if raw_link.startswith('http'):
                        real_link = raw_link
                    else:
                        continue
                
                # Estimate source from hostname
                domain = urllib.parse.urlparse(real_link).netloc
                source = domain.replace("www.", "")
                
                # Estimate date from text snippet if possible (default to historical estimate)
                publish_date = datetime.date.today().strftime("%Y-%m-%d")
                snippet = snippet_tag.text if snippet_tag else ""
                # Look for dates like Jan 14, 2025 or 14-Jul-2015
                date_match = re.search(r'\b\d{1,2}[-\/\s](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|[0-9]{1,2})[-\/\s]\d{4}\b', snippet, re.IGNORECASE)
                if date_match:
                    try:
                        # Attempt to parse date string
                        ds = date_match.group(0)
                        # clean up dates
                        for fmt in ("%d %b %Y", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
                            try:
                                dt = datetime.datetime.strptime(ds, fmt)
                                publish_date = dt.strftime("%Y-%m-%d")
                                break
                            except ValueError:
                                continue
                    except Exception:
                        pass
                
                articles.append({
                    'headline': headline,
                    'google_link': real_link,  # Holds original link directly
                    'source': source,
                    'publish_date': publish_date
                })
        # Sleep to avoid rate limiting
        time.sleep(1)
    except Exception as e:
        print(f"DuckDuckGo query failed: {e}")
    return articles

def date_in_window(date_str, edition):
    """Checks if a publish date falls within the coverage window for an edition."""
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        if edition == "2015":
            start = datetime.datetime.strptime(NASHIK_2015_START, "%Y-%m-%d").date()
            end = datetime.datetime.strptime(NASHIK_2015_END, "%Y-%m-%d").date()
            return start <= dt <= end
        elif edition == "2025":
            start = datetime.datetime.strptime(PRAYAGRAJ_2025_START, "%Y-%m-%d").date()
            end = datetime.datetime.strptime(PRAYAGRAJ_2025_END, "%Y-%m-%d").date()
            return start <= dt <= end
    except Exception:
        # If date parsing fails, include it anyway as a precaution
        return True
    return False

def ingest_raw_article(conn, article):
    """Inserts a single raw article metadata record into the database."""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO articles (url, source, publish_date, headline, status)
            VALUES (?, ?, ?, ?, 'raw')
            ON CONFLICT(url) DO UPDATE SET
                headline = excluded.headline,
                publish_date = excluded.publish_date
        """, (article['url'], article['source'], article['publish_date'], article['headline']))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Ingestion failed for {article['url']}: {e}")
        return False

def run_collection_pipeline():
    """Main pipeline execution for news metadata harvesting."""
    print("=== Starting Phase 2: Metadata Harvesting ===")
    
    # 1. Compile query queries
    queries = []
    
    # Simple general keyword search
    for kw in KEYWORDS["general"]:
        queries.append((kw, "general"))
        
    # Domain specific queries for high-quality coverage
    for category, terms in KEYWORDS.items():
        if category == "general":
            continue
        for term in terms:
            # Combine domain site: filters with terms
            for domain in NEWS_DOMAINS[:4]: # Limit to top national/regional news domains for speed
                queries.append((f"site:{domain} {term}", "targeted"))
                
    print(f"Generated {len(queries)} search queries for harvesting.")
    
    collected_articles = []
    
    # 2. Run harvesting (limited scope first for speed)
    # We will query Google News RSS first as it is super fast and structured
    for query, qtype in queries[:15]:  # Scope to top queries for initial harvest
        # Fetch RSS
        rss_articles = fetch_google_news_rss(query)
        collected_articles.extend(rss_articles)
        
        # Fetch DDG as a secondary layer
        ddg_articles = fetch_duckduckgo_results(query)
        collected_articles.extend(ddg_articles)
        
    print(f"Harvested {len(collected_articles)} raw entries from searches.")
    
    # 3. Resolve redirects in parallel
    print("Resolving Google News redirect links in parallel...")
    resolved_articles = []
    
    def process_link(art):
        original_url = art['google_link']
        # If it's a google news redirect link, resolve it
        if "news.google.com" in original_url:
            real_url = resolve_google_redirect(original_url)
        else:
            real_url = original_url
            
        art['url'] = real_url
        
        # Check if the article fits either 2015 or 2025 window
        is_2015 = date_in_window(art['publish_date'], "2015")
        is_2025 = date_in_window(art['publish_date'], "2025")
        
        if is_2015 or is_2025:
            # Check wayback archive for 2015 articles (as fallback prep)
            if is_2015 and "2015" in art['publish_date']:
                wayback_url = check_wayback_machine(real_url)
                if wayback_url:
                    art['wayback_url'] = wayback_url
            return art
        return None

    # Run threadpool to resolve redirects quickly
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_link, art): art for art in collected_articles if art['google_link']}
        for future in as_completed(futures):
            res = future.result()
            if res:
                resolved_articles.append(res)
                
    print(f"Resolved {len(resolved_articles)} articles fitting timeline windows.")
    
    # 4. Ingest into local Database
    conn = get_db_connection()
    inserted_count = 0
    for art in resolved_articles:
        if ingest_raw_article(conn, art):
            inserted_count += 1
            
    conn.close()
    print(f"Ingestion complete. Successfully inserted {inserted_count} unique raw articles into SQLite.")

if __name__ == "__main__":
    run_collection_pipeline()
