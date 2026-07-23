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
