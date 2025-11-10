import os
from dotenv import load_dotenv, find_dotenv

# Attempt to locate the .env file
env_path = find_dotenv()

if env_path:
    # Load environment variables from .env file if found
    load_dotenv(env_path)
else:
    # Notify if .env file is missing, will use system environment variables instead
    print("Warning: .env file not found. Falling back to system environment variables.")

# Retrieve the GitHub access token from environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Retrieve the default GitHub repository, fallback to 'carpentries/glosario' if unset
DEFAULT_REPO = os.getenv("GITHUB_REPO", "carpentries/glosario")

# Construct the base URL for GitHub API requests
BASE_URL = f"https://api.github.com/repos/{DEFAULT_REPO}"

# Warn if no GitHub token is set, as requests may be rate limited
if not GITHUB_TOKEN:
    print("Warning: No GITHUB_TOKEN found. Requests may be rate-limited.")
