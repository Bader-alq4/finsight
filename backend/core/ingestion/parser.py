# Opens one HTML filing file and extracts clean readable text organized by SEC Item sections
# parser.py uses a regex to find SEC Item headers

import re
from bs4 import BeautifulSoup

ITEM_RE = re.compile(r"^item\s+(\d+[a-z]?)\.", re.IGNORECASE)

def parse_html(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    # Remove noise
    for tag in soup.find_all(True, style=lambda x: x and "display:none" in x):
        tag.decompose()
    for tag in soup(["script", "style", "meta"]):
        tag.decompose()

    sections = []
    current_label = "Front Matter"
    current_text = []

    for element in soup.find_all(["p", "div"]):
        text = element.get_text(separator=" ", strip=True)
        if not text or len(text) < 10:
            continue

        match = ITEM_RE.match(text)
        if match and len(text) < 80:
            if current_text:
                sections.append({
                    "section_label": current_label,
                    "text": " ".join(current_text)
                })
            current_label = text
            current_text = []
        else:
            current_text.append(text)

    if current_text:
        sections.append({
            "section_label": current_label,
            "text": " ".join(current_text)
        })

    return sections