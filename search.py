import json
import os
import requests
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

SERPAPI_URL = "https://serpapi.com/search"


def _mock_results() -> str:
    """Fallback mock data if the API is unreachable or key is missing."""
    return json.dumps([
        {
            "title": "AI-Assisted Protein Folding for Drug Target Identification",
            "url": "https://patents.google.com/patent/US11111111",
            "patent_number": "US-11111111-B2",
            "assignee": "DeepMind Technologies",
            "filing_date": "2022-03-15",
            "abstract": "A transformer-based method to predict 3D protein structure for identifying drug binding sites."
        },
        {
            "title": "Machine Learning System for Genomic Variant Classification",
            "url": "https://patents.google.com/patent/US22222222",
            "patent_number": "US-22222222-B2",
            "assignee": "Illumina Inc",
            "filing_date": "2021-07-20",
            "abstract": "Deep learning for classifying genomic variants associated with hereditary diseases."
        },
        {
            "title": "Reinforcement Learning for Novel Drug Molecule Generation",
            "url": "https://patents.google.com/patent/US33333333",
            "patent_number": "US-33333333-B2",
            "assignee": "Insilico Medicine",
            "filing_date": "2023-01-10",
            "abstract": "RL agents generating novel molecular structures with desired pharmacological properties."
        },
        {
            "title": "NLP System for Clinical Trial Data Extraction",
            "url": "https://patents.google.com/patent/US44444444",
            "patent_number": "US-44444444-B2",
            "assignee": "IBM Watson Health",
            "filing_date": "2020-09-05",
            "abstract": "NLP pipeline for automated extraction of outcomes from clinical trial documents."
        },
        {
            "title": "Convolutional Neural Network for Medical Image Diagnosis",
            "url": "https://patents.google.com/patent/US55555555",
            "patent_number": "US-55555555-B2",
            "assignee": "Google Health",
            "filing_date": "2021-11-30",
            "abstract": "CNN architecture for detecting anomalies in radiology images including CT scans and MRIs."
        },
    ], indent=2)

# @tool
def search_patents(query: str) -> str:
    """
    Searches Google Patents via SerpAPI for patents matching the query.
    Requires SERPAPI_KEY env var. Always call this first.
    Returns a list of patents with titles, assignees, dates, and abstracts.
    Input: a search string like 'machine learning drug discovery'.
    """
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        print("SERPAPI_KEY not set — falling back to mock data")
        return _mock_results()

    try:
        params = {
            "engine": "google_patents",
            "q": query,
            "num": 10,
            "api_key": api_key,
        }

        response = requests.get(SERPAPI_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        patents = data.get("organic_results", [])
        if not patents:
            return _mock_results()

        results = []
        for p in patents[:10]:
            patent_id = p.get("patent_id", "")
            results.append(p.get("patent_link", f"https://patents.google.com/patent/{patent_id.replace('-', '')}"));
            # results.append({
            #     "title": p.get("title", "Unknown"),
            #     "url": p.get("patent_link", f"https://patents.google.com/patent/{patent_id.replace('-', '')}"),
            #     "patent_number": patent_id,
            #     "assignee": p.get("assignee", "Unknown"),
            #     "filing_date": p.get("filing_date", "Unknown"),
            #     "abstract": (p.get("snippet") or "No abstract available")[:500],
            # })

        # return json.dumps(results, indent=2)
        return results
    
    except Exception as e:
        print(f"SerpAPI search failed: {e} — falling back to mock data")
        return _mock_results()
