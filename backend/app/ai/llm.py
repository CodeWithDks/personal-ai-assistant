import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Professional Practice: Force-load environment profiles explicitly
load_dotenv()

# Fixed model identifier typo from 'gpt-4.1-mini' to 'gpt-4o-mini'
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2
)

"""import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Force-load environment variables from .env
load_dotenv()

# Initialize ChatGroq (requires GROQ_API_KEY set in your .env)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.2
)"""
