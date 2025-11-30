import os
from dotenv import load_dotenv

# Load environment variables from the .env file in the project root
load_dotenv()

# --- API Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "qwen/qwen3-32b")

# --- File Paths ---
PROMPT_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'prompts')