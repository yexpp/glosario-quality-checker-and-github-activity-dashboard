import time
from itertools import islice
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from github import Github
import pandas as pd

from config import GITHUB_TOKEN, BASE_URL

def parse_repo_name(base_url):
    parts = urlparse(base_url).path.strip("/").split("/")
    if len(parts) >= 2:
        return "/".join(parts[-2:])
    raise ValueError("BASE_URL format is incorrect, unable to extract repository name.")

REPO_NAME = parse_repo_name(BASE_URL)

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def get_contributors():
    contributors = repo.get_contributors()
    data = [{"login": user.login, "contributions": user.contributions} for user in contributors]
    return pd.DataFrame(data)

def get_pull_requests(state="all", max_count=None):
    pulls = repo.get_pulls(state=state, sort="created", direction="desc")
    data = []
    for i, pr in enumerate(pulls):
        if max_count and i >= max_count:
            break
        data.append({
            "login": pr.user.login if pr.user else None,
            "state": pr.state,
            "created_at": pr.created_at,
            "merged_at": pr.merged_at,
            "merged": pr.merged_at is not None
        })
    return pd.DataFrame(data)

def classify_file(file_path):
    if file_path.endswith('.py'):
        return 'Python'
    elif file_path.endswith('.html'):
        return 'HTML'
    elif file_path.endswith('.scss'):
        return 'SCSS'
    else:
        return 'Other'

def get_single_commit_data(commit, retries=3):
    for attempt in range(retries):
        try:
            full_commit = repo.get_commit(commit.sha)
            files = full_commit.files
            languages = set(classify_file(f.filename) for f in files)
            return {
                "login": commit.author.login if commit.author else None,
                "date": commit.commit.author.date if commit.commit.author else None,
                "languages": list(languages)
            }
        except Exception as e:
            print(f"[!] Error processing commit {commit.sha}, attempt {attempt + 1}: {e}")
            time.sleep(1)  
    return {"login": None, "date": None, "message": None, "languages": []}

def get_commits(max_count=None):
    commits_iter = repo.get_commits()
    if max_count:
        commits_iter = islice(commits_iter, max_count)

    data = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(get_single_commit_data, c) for c in commits_iter]
        for future in as_completed(futures):
            data.append(future.result())

    return pd.DataFrame(data)

def get_issues(state="all", max_count=None):
    data = []
    count = 0
    issues = repo.get_issues(state=state)

    for issue in issues:
        if issue.pull_request is not None:
            continue  
        if max_count and count >= max_count:
            break
        login = issue.user.login if issue.user else None
        data.append({
            "login": login,
            "state": issue.state,
            "created_at": issue.created_at,
            "closed_at": issue.closed_at
        })
        count += 1

    return pd.DataFrame(data)

def get_single_issue_comments(issue):
    comments = []
    try:
        for comment in issue.get_comments():
            comments.append({
                "login": comment.user.login if comment.user else None,
                "created_at": comment.created_at,
                "body": comment.body
            })
    except Exception as e:
        print(f"[!] Error retrieving comments from issue {issue.number}: {e}")
    return comments

def get_issue_comments(max_count=None):
    data = []
    count = 0
    issues = list(repo.get_issues())

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_single_issue_comments, issue): issue for issue in issues}
        for future in as_completed(futures):
            comments = future.result()
            for comment in comments:
                if max_count and count >= max_count:
                    break
                data.append(comment)
                count += 1
            if max_count and count >= max_count:
                break

    return pd.DataFrame(data)
