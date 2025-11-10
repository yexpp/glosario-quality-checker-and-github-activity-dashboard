from dotenv import load_dotenv
import os

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("Warning: No GITHUB_TOKEN found. Requests may be rate-limited.")

BASE_URL = "https://api.github.com/repos/carpentries/glosario"
