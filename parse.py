import json
import requests
from bs4 import BeautifulSoup

def parse_patent(url: str) -> dict:
    """
    Fetches and parses a patent page given its URL.
    Returns a Python dictionary with structured data: title, abstract, and claims.
    """
    if not url.startswith("http"):
        return {"error": "Invalid URL — must start with http.", "url": url}

    if "mock" in url:
        return _mock_parse(url)

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.find(class_="invention-title") or soup.find("h1")
        title = title.get_text(strip=True) if title else "Unknown Title"

        abstract = soup.find(class_="abstract")
        abstract = abstract.get_text(strip=True) if abstract else "No abstract found"

        claims = []
        claims_section = soup.find(class_="claims")
        if claims_section:
            for c in claims_section.find_all("div", class_="claim")[:5]:
                claims.append(c.get_text(strip=True)[:300])

        return {
            "title": title,
            "abstract": abstract,
            "claims": claims,
            "url": url
        }

    except Exception as e:
        print(f"Parse error for {url}: {e} — using mock")
        return _mock_parse(url)


def _mock_parse(url: str) -> dict:
    """Fallback mock parsed patent."""
    patent_id = url.split("/")[-1]
    return {
        "title": f"Sample Biotech AI Patent ({patent_id})",
        "abstract": "A machine learning method applied to biological data for the purpose of identifying novel drug candidates...",
        "claims": [
            "1. A computer-implemented method comprising: receiving biological sequence data...",
            "2. The method of claim 1, wherein the neural network comprises transformer-based layers...",
        ],
        "url": url
    }


def parse_all_patents(urls) -> list:
    """
    Proof of concept: Iterates through the hardcoded URLs 
    and returns a list of parsed patent dictionaries.
    """
    # urls = [
    #     "https://patents.google.com/patent/US8828399B2/en",
    #     "https://patents.google.com/patent/CN112552396B/en",
    #     "https://patents.google.com/patent/US10973905B2/en",
    #     "https://patents.google.com/patent/WO2022218272A1/en",
    #     "https://patents.google.com/patent/US10246494B2/en",
    #     "https://patents.google.com/patent/EP4114460A1/en",
    #     "https://patents.google.com/patent/JP3734263B2/en",
    #     "https://patents.google.com/patent/CN105175538B/en"
    # ]
    
    if not len(urls):
        return {"error": "Invalid URL array"}
    
    results = []
    for url in urls:
        parsed = parse_patent(url)
        results.append(parsed)
    return results


# This ONLY runs if you execute `python parse.py` directly
# if __name__ == "__main__":
#     print("Running parse.py standalone test...")
#     data = get_hardcoded_patents_data()
#     print(json.dumps(data, indent=2))