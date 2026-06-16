import os
from dotenv import load_dotenv

load_dotenv()
print("LLM_PROVIDER:", os.getenv("LLM_PROVIDER"))
print("OPENROUTER_API_KEY:", os.getenv("OPENROUTER_API_KEY")[:10] + "...") # type: ignore