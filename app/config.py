import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
COMFY_URL = os.getenv("COMFY_URL", "http://localhost:8188")
IG_USER_ID = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN")
NICHE = os.getenv("NICHE", "minimalist architecture")
POST_TIME = os.getenv("POST_TIME", "09:00")
GENERATE_TIME = os.getenv("GENERATE_TIME", "08:00")

# Local paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "generated_images")
DB_PATH = os.path.join(BASE_DIR, "instabot.db")

# COMFY UI
COMFY_CHECKPOINT = os.getenv(
    "COMFY_CHECKPOINT", "realisticVisionV60B1_v51HyperVAE.safetensors")

os.makedirs(IMAGES_DIR, exist_ok=True)
