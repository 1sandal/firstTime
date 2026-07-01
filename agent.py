import json
import re
import os
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from typing import List, Optional
from google.adk.agents import Agent
from google import genai
from google.genai import types
from . import parse
from . import search

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

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
# 2. THE RETRIEVAL TOOL
# =====================================================================
def get_raw_patent_data_by_topic(urls: List[str]) -> str:
    # Import your parse module

    """
    Retrieves patent details for a given topic. 
    # Currently uses a hardcoded list of URLs as a proof of concept.
    """
    # print("HELLLOOO")
    # 1. Fetch the structured list of dictionaries from parse.py
    patents_list = parse.parse_all_patents(urls)
    
    # print("HELLLOOO")

    # 2. Return it as a JSON string so your Agent framework can read it as context
    return json.dumps(patents_list, indent=2)

# =====================================================================
# 3. THE SEARCH TOOL
# =====================================================================
def search_patents(topic: str) -> str:
    # Import your search module

    """
    Retrieves patent details for a given topic. 
    Currently uses a hardcoded list of URLs as a proof of concept.
    """
    # print("HELLLOOO")
    # 1. Fetch the structured list of dictionaries from parse.py
    search_results = search.search_patents(topic)
    

    # 2. Return it as a JSON string so your Agent framework can read it as context
    return json.dumps(search_results, indent=2)


# =====================================================================
# 4 c. Joke TOOL
# =====================================================================
def provide_joke(topic: str) -> str:
    # Import your parse module

    """
    Retrieves a joke
    """
    joke = ["Why don't skeletons fight each other? They don't have the guts."]
    # 1. Fetch the structured list of dictionaries from parse.py    

    # 2. Return it as a JSON string so your Agent framework can read it as context
    return joke

# =====================================================================
# 4 c. Summarize and find whitespace
# =====================================================================
def analyze_all_patents(patents_json):
    client = genai.Client(vertexai=True, project=os.environ["GOOGLE_CLOUD_PROJECT"], location="us-central1")

    print(f"--- Finding whitespace ---")
    
    # Load the hand-drawn sketch
    patent_data = patents_json

    # Prompt Gemini to read the sketch and output clean JSON
    detection_prompt = """You are a patent intelligence analyst specializing in biotech AI. Analyze the provided patent json and identify white spaces — specific areas of innovation that are NOT yet claimed. Be concrete and specific. Ground every insight in the actual patents provided.
    """

    # Model: Gemini 2.5 Flash (Optimized for JSON extraction)
    detection_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[detection_prompt, json.dumps(patents_json)],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1
        )
    )

    # Parse the JSON data
    #design_data = json.loads(detection_response.text)
    #print("Detected Data:", json.dumps(design_data, indent=2))
    #return design_data
    return detection_response.text


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
        "You are a helpful assistant. When a user asks you about a patent"
        "run the tools given. If they need a joke, provide a joke from tool instead of patents." \
        "Once you have all patents, also provide a summary of whitespace domain."
    ),
    tools=[search_patents, get_raw_patent_data_by_topic, provide_joke, analyze_all_patents],
    # tools=[get_raw_patent_data_by_topic, provide_joke, analyze_all_patents],
    # response_schema=List[PatentInsightSchema]
)

# Assign system properties directly or use standard framework string parameters 
# if your codebase setup leverages specific assignment tags.
# Alternatively, since adk run exposes a dynamic prompt workflow, 
# you can pass the schema directly inside the execution loop.