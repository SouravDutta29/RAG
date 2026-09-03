import json
import logging
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

URLS = [
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
]

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw"

def extract_dom_tables(html_content):
    """
    Extracts all text from tables and potentially useful DOM blocks 
    using BeautifulSoup, to avoid storing massive raw HTML files.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    tables_data = []
    for table in soup.find_all('table'):
        rows = []
        for tr in table.find_all('tr'):
            cells = [td.get_text(strip=True) for td in tr.find_all(['th', 'td'])]
            if cells:
                rows.append(cells)
        if rows:
            tables_data.append(rows)
            
    # Extract any text content from div tags that look like they contain metrics
    # For a robust scraper, we just return the cleaned up body text and the tables
    
    return {
        "tables": tables_data,
    }

def scrape_funds():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Using a standard user agent to avoid basic blocking
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        for url in URLS:
            slug = url.split('/')[-1]
            logging.info(f"Scraping {slug}...")
            
            try:
                # Add randomized sleep to prevent rate limiting (as per edge-case.md)
                time.sleep(random.uniform(2.0, 4.0))
                
                # Navigate to the page and wait for the network to be idle
                page.goto(url, wait_until="networkidle")
                
                # Explicitly wait for the NEXT_DATA script tag which contains the core financial data
                page.wait_for_selector("script#__NEXT_DATA__", state="attached", timeout=10000)
                
                # 1. Extract __NEXT_DATA__ JSON payload injected by Next.js
                next_data = page.evaluate("() => window.__NEXT_DATA__")
                
                # 2. Extract raw HTML for BeautifulSoup processing
                html_content = page.content()
                dom_elements = extract_dom_tables(html_content)
                
                # Combine into an intermediate raw payload
                # (The parser in Phase 1.2 will consume this to produce the final normalized JSON)
                result = {
                    "source_url": url,
                    "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "next_data": next_data,
                    "dom_tables": dom_elements["tables"],
                    "raw_html_snapshot": html_content  # Keeping full HTML for robust parsing in 1.2
                }
                
                # We save with '_raw.json' suffix to differentiate from Phase 1.2 output
                output_path = OUTPUT_DIR / f"{slug}_raw.json"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False)
                    
                logging.info(f"Successfully saved raw data for {slug} to {output_path}")
                
            except Exception as e:
                logging.error(f"Failed to scrape {url}: {e}")
                
        browser.close()
        logging.info("Scraping completed.")

if __name__ == "__main__":
    scrape_funds()
