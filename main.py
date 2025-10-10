import os
import json
import time
import argparse 

# API clients
import openai
import anthropic
import cohere
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
cohere_api_key = os.getenv("COHERE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")

