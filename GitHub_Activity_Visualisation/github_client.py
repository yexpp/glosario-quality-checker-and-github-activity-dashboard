from github import Github
from urllib.parse import urlparse
from config import GITHUB_TOKEN, BASE_URL

def parse_repo_name(base_url):
    """
    Extract the repository name in "owner/repo" format from the base URL.

    Parameters:
        base_url (str): The GitHub repository API base URL.

    Returns:
        str: The repository name as "owner/repo".

    Raises:
        ValueError: If the base_url format is incorrect or cannot be parsed.
    """
    parts = urlparse(base_url).path.strip("/").split("/")
    if len(parts) >= 2:
        return "/".join(parts[-2:])
    raise ValueError("BASE_URL format is incorrect.")

REPO_NAME = parse_repo_name(BASE_URL)

# Initialize GitHub client with the access token
g = Github(GITHUB_TOKEN)

try:
    # Retrieve the repository object
    repo = g.get_repo(REPO_NAME)
except Exception as e:
    raise RuntimeError(f"Failed to retrieve repo '{REPO_NAME}': {e}")
