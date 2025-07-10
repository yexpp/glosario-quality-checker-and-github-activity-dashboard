from github import Github
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("Warning: No GITHUB_TOKEN found. Requests may be rate-limited.")

g = Github(GITHUB_TOKEN)  

BASE_URL = "https://api.github.com/repos/carpentries/glosario" 

repo = g.get_repo("carpentries/glosario") 
print(repo)  

print("Repository name:", repo.name)
print("Description:", repo.description)
print("Stars:", repo.stargazers_count)
print("Forks:", repo.forks_count)
