from github import Github
from urllib.parse import urlparse
from config import GITHUB_TOKEN, BASE_URL

def parse_repo_name(base_url):
    parts = urlparse(base_url).path.strip("/").split("/")
    if len(parts) >= 2:
        return "/".join(parts[-2:])
    raise ValueError("BASE_URL format is incorrect.")

REPO_NAME = parse_repo_name(BASE_URL)

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)
