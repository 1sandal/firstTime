import json
import re
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from typing import List, Optional
from google.adk.agents import Agent 

# =====================================================================
# 1. DEFINE TARGET STRUCTURED OUTPUT SCHEMA
# =====================================================================
class PatentInsightSchema(BaseModel):
    patent_id: str = Field(description="The formal patent number (e.g., US12345678B2)")
    title: str = Field(description="The clean title of the patent.")
    publication_date: str = Field(description="The ISO date format YYYY-MM-DD.")
    classifications: List[str] = Field(description="List of international patent classifications like CPC/IPC codes.")
    technical_problem: str = Field(description="A concise summary of the specific engineering challenge or flaw in existing systems this patent solves.")
    core_mechanism: str = Field(description="The core technical solution or mechanism introduced by the patent to fix the problem, translated from legalese.")
    independent_claims_summary: List[str] = Field(description="Brief summaries or extractions of the primary independent claims (the fundamental parent claims).")


# =====================================================================
# =====================================================================
# 2. THE RETRIEVAL TOOL (Using OpenAlex Public API - Reliable & Free)
# =====================================================================
def get_raw_patent_data_by_topic(topic: str) -> str:
    """
    Searches the open-access OpenAlex database for patents matching a specific topic.
    Returns structured metadata and abstracts for the agent to synthesize.
    No API key required.
    
    Args:
        topic: The string keyword or phrase to search for.
        
    Returns:
        A rich string text dump ready for an LLM to parse into JSON.
    """
    import requests

    # fallback clean encoding
    clean_topic = topic.strip().replace(" ", "+")
    
    # We query using the structural endpoint with an updated, friendly User-Agent header
    url = f"https://api.openalex.org/works?filter=type:patent&search={clean_topic}&per_page=3"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return f"Error connecting to data provider. Status code: {response.status_code}"
        
        data = response.json()
        results = data.get("results", [])
    except Exception as e:
        return f"Failed to retrieve results due to exception: {str(e)}"

    if not results:
        # Fallback: drop the hard type:patent filter string if it returns empty, 
        # and search globally for the term with 'patent' appended to the keyword text
        fallback_url = f"https://api.openalex.org/works?search={clean_topic}+patent&per_page=3"
        try:
            response = requests.get(fallback_url, headers=headers, timeout=10)
            data = response.json()
            results = data.get("results", [])
        except Exception:
            return "No matching patents found for the given topic query."

    if not results:
        return "No matching patents found for the given topic query."

    combined_payload = []

    for item in results:
        raw_id = item.get("ids", {}).get("patent", "")
        if not raw_id:
            raw_id = item.get("id", "").split("/")[-1]
            
        title = item.get("title", "Unknown Title")
        pub_date = item.get("publication_date", "Unknown Date")
        
        classifications = []
        if item.get("primary_topic"):
            classifications.append(item["primary_topic"].get("display_name", ""))
        for concept in item.get("concepts", [])[:3]:
            classifications.append(concept.get("display_name", ""))

        abstract_text = "N/A"
        abstract_inverted_index = item.get("abstract_inverted_index")
        if abstract_inverted_index:
            try:
                words = {}
                for word, positions in abstract_inverted_index.items():
                    for pos in positions:
                        words[pos] = word
                abstract_text = " ".join([words[p] for p in sorted(words.keys())])
            except Exception:
                abstract_text = "Structure incomplete"

        patent_dump = f"""
        --- START PATENT RECORD ---
        PATENT ID: {raw_id}
        TITLE: {title}
        PUBLICATION DATE: {pub_date}
        CONCEPT CLASSIFICATIONS: {", ".join(classifications)}
        ABSTRACT/SUMMARY TEXT: 
        {abstract_text}
        --- END PATENT RECORD ---
        """
        combined_payload.append(patent_dump)

    return "\n\n".join(combined_payload)

# =====================================================================
# 3. AGENT DEFINITION
# =====================================================================
# Instantiating the agent using correct singular 'instruction' argument and response schema template
# =====================================================================
# 3. AGENT DEFINITION
# =====================================================================
# Instantiate the base agent with only the valid permitted constructor keys
root_agent = Agent(
    name="PatentInsightAgent",
    model="gemini-2.5-flash",
    description="An assistant capable of finding related patents",
    instruction=(
        "You are a helpful geometry assistant. When a user asks you about a patent"
        "use the tools to find related patents."
        "Output in format like PatentInsightSchema structure. Not conversational."
    ),
    tools=[get_raw_patent_data_by_topic],
    response_schema=List[PatentInsightSchema]
)

# Assign system properties directly or use standard framework string parameters 
# if your codebase setup leverages specific assignment tags.
# Alternatively, since adk run exposes a dynamic prompt workflow, 
# you can pass the schema directly inside the execution loop.