import json
import time
import pandas as pd
from github_client import repo

from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import islice

from utils import filter_bots, classify_file

def get_contributors():
    """
    Retrieve contributors from the repository with their contribution counts.
    Filters out bot accounts.
    """
    contributors = repo.get_contributors()
    data = [{"login": user.login, "contributions": user.contributions} for user in contributors]
    df = pd.DataFrame(data)
    return filter_bots(df)

def get_pull_requests(state="all", max_count=None):
    pulls = repo.get_pulls(state=state, sort="created", direction="desc")
    data = []
    for i, pr in enumerate(pulls):
        if max_count and i >= max_count:
            break

        labels = [label.name for label in pr.get_labels()]
        
        language_codes = [label.split(":", 1)[1] for label in labels if label.startswith("lang:")]


        data.append({
            "login": pr.user.login if pr.user else None,
            "state": pr.state,
            "created_at": pr.created_at,
            "merged_at": pr.merged_at,
            "merged": pr.merged_at is not None,
            "language_labels": language_codes  
        })
    df = pd.DataFrame(data)
    return df

    
def get_single_commit_data(commit, retries=3):
    """
    Extract commit details including author login, commit date, and languages involved.
    Retries on failure up to a specified count.
    """
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

    # Return empty data if all retries fail
    return {"login": None, "date": None, "languages": []}


def get_commits(max_count=None):
    """
    Retrieve commits from the repository with concurrency.
    Extract commit author, date, and file languages.
    Limits results if max_count specified.
    Filters out bot accounts.
    """
    commits_iter = repo.get_commits()
    if max_count:
        commits_iter = islice(commits_iter, max_count)

    data = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(get_single_commit_data, c) for c in commits_iter]
        for future in as_completed(futures):
            data.append(future.result())

    df = pd.DataFrame(data)
    return filter_bots(df)


def get_issues(state="all", max_count=None):
    """
    Retrieve issues from the repository, excluding pull requests.
    Extract issue author, state, dates, and labels.
    Limits results if max_count specified.
    Filters out bot accounts.
    """
    data = []
    count = 0
    issues = repo.get_issues(state=state)

    for issue in issues:
        if issue.pull_request is not None:
            continue
        if max_count and count >= max_count:
            break

        login = issue.user.login if issue.user else None
        labels = [label.name for label in issue.labels]

        data.append({
            "login": login,
            "state": issue.state,
            "created_at": issue.created_at,
            "closed_at": issue.closed_at,
            "labels": labels
        })
        count += 1

    df = pd.DataFrame(data)
    return filter_bots(df)


def get_single_issue_comments(issue):
    """
    Retrieve all comments on a single issue.
    Returns a list of dicts with comment author, creation time, and content.
    """
    comments = []
    try:
        for comment in issue.get_comments():
            comments.append({
                "login": comment.user.login if comment.user else None,
                "created_at": comment.created_at,
                "body": comment.body
            })
    except Exception as e:
        print(f" Error retrieving comments from issue {issue.number}: {e}")
    return comments


def get_issue_comments(max_count=None):
    """
    Retrieve comments from all issues concurrently.
    Limits total comments retrieved if max_count specified.
    Filters out comments by bot accounts.
    """
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

    df = pd.DataFrame(data)
    return filter_bots(df)


def get_readme_contributors_remote():
    """
    Retrieve the README file content from the repository.
    Intended for extracting contributor info if needed.
    """
    try:
        readme_content = repo.get_readme().decoded_content.decode("utf-8")
        return readme_content
    except Exception as e:
        print(f" Unable to fetch README content from GitHub: {e}")
        return ""


def get_readme_contributors_remote_df():
    """
    Retrieve contributors info from the .all-contributorsrc JSON config file.
    Converts it into a DataFrame with contribution types as columns.
    """
    try:
        file_content = repo.get_contents(".all-contributorsrc")
        raw = file_content.decoded_content.decode("utf-8")
        data = json.loads(raw)
    except Exception as e:
        print(f"[!] Unable to fetch .all-contributorsrc content from GitHub: {e}")
        return pd.DataFrame()

    contributors = data.get("contributors", [])
    rows = []
    for c in contributors:
        login = c.get("login")
        contribs = c.get("contributions", [])
        if not login:
            print(f" Contributor missing login field: {c}")
            continue
        rows.append({"login": login.strip().lower(), **{c_type: 1 for c_type in contribs}})

    if not rows:
        print(" No valid contributors extracted!")
        return pd.DataFrame()

    df = pd.DataFrame(rows).fillna(0)
    int_cols = df.columns.drop("login")
    df[int_cols] = df[int_cols].astype(int)
    return df

def get_file_contributors(file_path="glossary.yml"):
    """
    Retrieve commit counts per contributor for a specified file.
    Returns a dictionary mapping contributor login to number of commits.
    """
    try:
        commits = repo.get_commits(path=file_path)
    except Exception as e:
        print(f" Error fetching contributors for file {file_path}: {e}")
        return {}

    contrib_count = {}
    for commit in commits:
        try:
            author = commit.author
            if author:
                name = author.login.lower()
                contrib_count[name] = contrib_count.get(name, 0) + 1
        except Exception:
            continue

    return contrib_count


def get_file_contributors_df(file_path="glossary.yml"):
    """
    Convert file contributor commit counts into a DataFrame.
    """
    contribs = get_file_contributors(file_path)
    data = [{"contributor": k, "commits": v} for k, v in contribs.items()]
    return pd.DataFrame(data)
