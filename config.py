import os
from dotenv import load_dotenv

# Load environment variables from the .env file in the project root
load_dotenv()

# --- API Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama3-70b-8192") # Default model

# You could add other configurations here if needed, e.g., for different APIs
# ZAI_API_KEY = os.getenv("ZAI_API_KEY")
# ZAI_MODEL_NAME = os.getenv("ZAI_MODEL_NAME", "llama3-8b-8192")

# --- File Paths (Can be configured here or passed as arguments) ---
PROMPT_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'prompts')