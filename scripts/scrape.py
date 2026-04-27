"""
Scrape priority URLs and save as clean text + metadata.
Run from project root: python scripts/scrape.py
"""

import json
import time
from pathlib import Path
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from sources import PRIORITY_SOURCES

CORPUS_DIR = Path(__file__).parent.parent / "corpus"
CORPUS_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Citebound/0.1 (research project; contact: sohil.vhora@outlook.com)"
}


import re  # add this at the top of the file with the other imports if not already there

def extract_date_modified(soup):
    """Try multiple strategies — canada.ca, ontario.ca, and quebec.ca all differ."""

    # Strategy 1: <time property="dateModified"> (canada.ca standard markup)
    tag = soup.find("time", property="dateModified")
    if tag and tag.get_text(strip=True):
        return tag.get_text(strip=True)

    # Strategy 2: canada.ca "Page details" definition list
    dl = soup.find("dl", id="wb-dtmd")
    if dl:
        m = re.search(r"\d{4}-\d{2}-\d{2}", dl.get_text())
        if m:
            return m.group(0)

    # Strategy 3: any <time> element with an ISO-style date
    for tag in soup.find_all("time"):
        text = tag.get_text(strip=True)
        if re.match(r"\d{4}-\d{2}-\d{2}", text):
            return text

    # Strategy 4: regex over full page text — catches Ontario.ca and edge cases
    body_text = soup.get_text(separator=" ", strip=True)
    patterns = [
        r"Date modified[:\s]+(\d{4}-\d{2}-\d{2})",
        r"Last modified[:\s]+(\d{4}-\d{2}-\d{2})",
        r"Updated[:\s]+(\d{4}-\d{2}-\d{2})",
        r"Page details\s+(\d{4}-\d{2}-\d{2})",
    ]
    for pattern in patterns:
        m = re.search(pattern, body_text)
        if m:
            return m.group(1)

    return None


def extract_main_content(soup):
    """Get the main article content, stripping nav/footer/scripts."""
    # Canada.ca uses <main> for the article
    main = soup.find("main")
    if not main:
        main = soup.find("article")
    if not main:
        main = soup.body

    # Remove scripts, styles, nav elements
    for tag in main.find_all(["script", "style", "nav", "aside"]):
        tag.decompose()

    # Get text with reasonable spacing
    text = main.get_text(separator="\n", strip=True)

    # Collapse excessive blank lines
    lines = [line for line in text.split("\n") if line.strip()]
    return "\n".join(lines)


def scrape_one(source):
    print(f"Fetching {source['id']}...")
    response = requests.get(source["url"], headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    title = soup.find("h1").get_text(strip=True) if soup.find("h1") else source["id"]
    date_modified = extract_date_modified(soup)
    content = extract_main_content(soup)

    record = {
        "id": source["id"],
        "url": source["url"],
        "topic": source["topic"],
        "description": source["description"],
        "title": title,
        "date_modified": date_modified,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "content": content,
        "word_count": len(content.split()),
    }

    out_path = CORPUS_DIR / f"{source['id']}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    print(f"  saved {out_path.name} | {record['word_count']} words | modified {date_modified}")
    return record


def main():
    print(f"Scraping {len(PRIORITY_SOURCES)} sources to {CORPUS_DIR}\n")
    results = []
    for source in PRIORITY_SOURCES:
        try:
            record = scrape_one(source)
            results.append(record)
        except Exception as e:
            print(f"  FAILED: {e}")
        time.sleep(1)  # Be polite to the servers

    print(f"\nDone. {len(results)}/{len(PRIORITY_SOURCES)} succeeded.")


if __name__ == "__main__":
    main()