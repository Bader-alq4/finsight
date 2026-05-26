# This file talks to the SEC EDGAR API and downloads the HTML filing files onto my disk

import requests
import os
import time
from backend.config import DATABASE_URL

HEADERS = {"User-Agent": "baderalq774@gmail.com"}

COMPANIES = {
    "AAPL": {"cik": "0000320193", "name": "Apple Inc."},
    "MSFT": {"cik": "0000789019", "name": "Microsoft Corporation"},
    "NVDA": {"cik": "0001045810", "name": "NVIDIA Corporation"},
    "GOOGL": {"cik": "0001652044", "name": "Alphabet Inc."},
    "AMZN": {"cik": "0001018724", "name": "Amazon.com Inc."},
    "META":  {"cik": "0001326801", "name": "Meta Platforms Inc."},
    "TSLA": {"cik": "0001318605", "name": "Tesla Inc."},
    "JPM":  {"cik": "0000019617", "name": "JPMorgan Chase & Co."},
    "BRK":  {"cik": "0001067983", "name": "Berkshire Hathaway Inc."},
    "JNJ":  {"cik": "0000200406", "name": "Johnson & Johnson"},
}

# returns the 3 most recent 10-K filings of each company with accession numbers and dates
def get_recent_filings(cik, filing_type="10-K", count=3):
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    response = requests.get(url, headers=HEADERS, timeout=30)
    data = response.json()

    filings = data["filings"]["recent"]
    results = []

    for i, form in enumerate(filings["form"]):
        if form == filing_type and len(results) < count:
            results.append({
                "accession": filings["accessionNumber"][i],
                "filing_date": filings["filingDate"][i],
                "filing_type": form
            })

    return results


# goes to the filing's index page on EDGAR, lists all files in that filing, and finds the largest HTM file (the real filing)
def get_filing_html_url(cik, accession):
    acc_clean = accession.replace("-", "")
    index_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_clean}/"

    response = requests.get(index_url, headers=HEADERS, timeout=30)

    # Find the largest htm file because that's the real filing
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, "lxml")

    best_url = None
    best_size = 0

    for link in soup.find_all("a"):
        href = link.get("href", "")
        if href.endswith(".htm") or href.endswith(".html"):
            # Skip XBRL fragment files
            filename = href.split("/")[-1]
            if filename.startswith("R") and filename[1:3].isdigit():
                continue
            if "index" in filename.lower():
                continue

            # Get file size by making a HEAD request
            full_url = f"https://www.sec.gov{href}"
            try:
                head = requests.head(full_url, headers=HEADERS, timeout=10)
                size = int(head.headers.get("content-length", 0))
                if size > best_size:
                    best_size = size
                    best_url = full_url
            except:
                continue

    return best_url, best_size

# downloads that HTML file and saves it to data/raw/
def download_filing(url, save_path):
    response = requests.get(url, headers=HEADERS, timeout=60)
    if response.status_code == 200:
        with open(save_path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(response.text)
        return True
    return False

# loops through all companies and calls the above functions for each one
def download_all(filing_type="10-K", count_per_company=3):
    os.makedirs("data/raw", exist_ok=True)

    for ticker, info in COMPANIES.items():
        cik = info["cik"]
        print(f"\nProcessing {ticker}...")

        filings = get_recent_filings(cik, filing_type, count_per_company)
        print(f"  Found {len(filings)} {filing_type} filings")

        for filing in filings:
            year = filing["filing_date"][:4]
            save_path = f"data/raw/{ticker}_{filing_type}_{year}.htm"

            if os.path.exists(save_path):
                print(f"  Already exists: {save_path}")
                continue

            print(f"  Finding HTML URL for {filing['accession']}...")
            url, size = get_filing_html_url(cik, filing["accession"])

            if not url or size < 100_000:
                print(f"  No valid HTML found (size: {size}) — skipping")
                continue

            print(f"  Downloading {size/1024/1024:.1f}MB...")
            success = download_filing(url, save_path)

            if success:
                print(f"  Saved: {save_path}")
            else:
                print(f"  Failed to download")

            time.sleep(0.5)

if __name__ == "__main__":
    download_all(filing_type="10-K", count_per_company=3)
