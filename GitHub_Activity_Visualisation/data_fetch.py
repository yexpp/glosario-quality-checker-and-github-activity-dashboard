import json
import time
import pandas as pd
from github_client import repo

from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from utils import filter_bots, classify_file
from github import GithubException


# ==================== Constants ====================

DEFAULT_SLEEP = 0.5          # Default sleep time between API requests (seconds)
RETRY_SLEEP_BASE = 5         # Base sleep time for retry after rate limiting (seconds)
COMMENT_SLEEP = 0.5          # Sleep time between comment fetches to avoid rate limits (seconds)


# ==================== Progress Helper ====================

def show_progress(current, total, prefix="Progress"):
    sys.stdout.write(f"\r{prefix}: {current}/{total}")
    sys.stdout.flush()
    
# ==================== Helpers ====================

def safe_user_login(user):
    """Return the login username of a user object or None if user is None."""
    return user.login if user else None


def append_with_limit(data_list, item, count, max_count):
    """
    Append an item to a list if count is less than max_count.
    Return False if max_count is reached, otherwise True.
    """
    if max_count is not None and count >= max_count:
        return False
    data_list.append(item)
    return True


def extract_comments_from_iterable(iterable, comment_type=None, max_count=None):
    """
    Extract comment data from an iterable of comment objects, optionally filtering by max_count.
    Each comment dict includes user login, creation time, body, and optionally commit_id, path, position, and type.
    """
    data = []
    count = 0
    for item in iterable:
        try:
            time.sleep(COMMENT_SLEEP)  # Sleep between comment fetches to avoid hitting rate limits
            comment = {
                "login": safe_user_login(item.user),
                "created_at": item.created_at,
                "body": item.body,
            }
            # Add optional fields if present
            if hasattr(item, 'commit_id'):
                comment["commit_id"] = item.commit_id
            if hasattr(item, 'path'):
                comment["path"] = item.path
            if hasattr(item, 'position'):
                comment["position"] = item.position
            if comment_type:
                comment["type"] = comment_type
            if not append_with_limit(data, comment, count, max_count):
                break
            count += 1
        except Exception as e:
            print(f"[!] Error extracting comment: {e}")
    return data


# ==================== Core Functions ====================

def get_contributors(show_progress=True):
    """
    Fetch all contributors of the repository, return a filtered DataFrame excluding bots.
    Each contributor includes their login and number of contributions.
    """
    try:
        contributors_obj = repo.get_contributors()
        total = contributors_obj.totalCount  

        data = []

        iterator = contributors_obj
        if show_progress:
            iterator = tqdm(contributors_obj, total=total, desc="Contributors")

        for user in iterator:
            data.append({
                "login": user.login,
                "contributions": user.contributions
            })

        return filter_bots(pd.DataFrame(data))

    except Exception as e:
        print(f"[!] Error fetching contributors: {e}")
        return pd.DataFrame()


def get_pull_requests(state="all", max_count=None):
    """
    Retrieve pull requests with given state (open, closed, all).
    Returns a DataFrame filtered to exclude bots, with info about PR author, state, dates, merged status, and language labels.
    """
    try:
        pulls = repo.get_pulls(state=state, sort="created", direction="desc")
        total = pulls.totalCount

    except Exception as e:
        print(f"[!] Error fetching pull requests: {e}")
        return pd.DataFrame()

    data = []

    for i, pr in enumerate(tqdm(pulls, total=total, desc="Pull Requests", unit="pr")):
        if max_count and i >= max_count:
            break

        try:
            labels = [label.name for label in pr.labels] 

            language_codes = [
                label.split(":", 1)[1]
                for label in labels
                if label.startswith("lang:")
            ]

            data.append({
                "login": pr.user.login if pr.user else None,
                "state": pr.state,
                "created_at": pr.created_at,
                "merged_at": pr.merged_at,
                "merged": pr.merged_at is not None,
                "language_labels": language_codes
            })

        except Exception as e:
            print(f"[!] Error processing PR #{pr.number}: {e}")

    return filter_bots(pd.DataFrame(data))


def get_single_commit_data(commit):
    """
    Retrieve information about a single commit.
    Returns dict with author login, commit date, and languages of files changed.
    Handles errors by returning default values on failure..
    """
    try:
        files = commit.files 

        languages = set(
            classify_file(f.filename) for f in files
        )

        return {
            "login": safe_user_login(commit.author),
            "date": commit.commit.author.date if commit.commit.author else None,
            "languages": list(languages)
        }

    except Exception as e:
        print(f"[!] Error processing commit {commit.sha}: {e}")
        return {
            "login": None,
            "date": None,
            "languages": []
        }



def get_commits(max_count=None, max_workers=8):
    """
    Fetch commits from the repository, limited by max_count.
    Uses a thread pool to fetch commit details concurrently.
    Returns a filtered DataFrame excluding bots.
    """
    try:
        commits_obj = repo.get_commits()

        commits = []
        for i, c in enumerate(commits_obj):
            if max_count and i >= max_count:
                break
            commits.append(c)

        data = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(get_single_commit_data, c)
                for c in commits
            ]

            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Commits",
                unit="commit"
            ):
                data.append(future.result())

        return filter_bots(pd.DataFrame(data))

    except Exception as e:
        print(f"[!] Error fetching commits: {e}")
        return pd.DataFrame()


def get_issues(state="all", max_count=None):
    """
    Retrieve issues from the repository with specified state.
    Skips pull requests (issues with pull_request field).
    Returns filtered DataFrame with issue author, state, created/closed dates, and labels.
    """
    try:
        issues = list(repo.get_issues(state=state))
        
        total = len(issues)

    except Exception as e:
        print(f"[!] Error fetching issues: {e}")
        return pd.DataFrame()

    data = []
    processed = 0

    pbar = tqdm(total=total, desc="Issues", unit="issue")

    for issue in issues:
        pbar.update(1)

        if issue.pull_request is not None:
            continue

        if max_count and processed >= max_count:
            break

        try:
            data.append({
                "login": issue.user.login if issue.user else None,
                "state": issue.state,
                "created_at": issue.created_at,
                "closed_at": issue.closed_at,
                "labels": [label.name for label in issue.labels]
            })
            processed += 1

        except Exception as e:
            print(f"[!] Error processing issue #{issue.number}: {e}")

    pbar.close()
    return filter_bots(pd.DataFrame(data))


def get_single_issue_comments(issue):
    """
    Fetch all comments from a single issue.
    Returns a list of comment dictionaries or empty list on failure.
    """
    try:
        return extract_comments_from_iterable(issue.get_comments())
    except Exception as e:
        print(f"[!] Error getting comments from issue #{issue.number}: {e}")
        return []

def get_issue_comments(max_count=None):
    """
    Fetch comments from all issues concurrently, up to max_count.
    Returns a filtered DataFrame excluding bots.
    """
    data, count = [], 0
    try:
        issues = list(repo.get_issues())
    except Exception as e:
        print(f"[!] Error fetching issues: {e}")
        return pd.DataFrame()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_single_issue_comments, issue): issue for issue in issues}

        for future in tqdm(as_completed(futures), total=len(futures), desc="Issue comments"):  
            comments = future.result()
            for c in comments:
                if not append_with_limit(data, c, count, max_count):
                    break
                count += 1
            if max_count and count >= max_count:
                break

    return filter_bots(pd.DataFrame(data))


def get_commit_comments(max_count=None):
    """
    Fetch commit comments from the repository, limited by max_count if specified.
    Returns a filtered DataFrame excluding bot accounts.
    """
    try:
        comments = list(repo.get_comments())

        data = extract_comments_from_iterable(
            tqdm(comments, total=len(comments), desc="Commit comments"),
            comment_type="commit_comment",
            max_count=max_count
        )

        return filter_bots(pd.DataFrame(data))

    except Exception as e:
        print(f"[!] Error retrieving commit comments: {e}")
        return pd.DataFrame()


def fetch_and_append_pr_comments(pr, method_name, comment_type, data, count, max_count):
    """
    Helper to fetch PR comments of a given type (issue comments or review comments),
    append them to data list, and return updated count.
    """
    try:
        method = getattr(pr, method_name)
        comments = extract_comments_from_iterable(
            method(), comment_type=comment_type, max_count=(max_count - count) if max_count else None
        )
        data.extend(comments)
        return count + len(comments)
    except Exception as e:
        print(f" [!] Error fetching {comment_type} from PR #{pr.number}: {e}")
        return count


def process_single_pr(pr, max_count):
    """
    Process a single pull request by fetching issue and review comments.
    Returns a list of extracted comment data and the updated comment count.
    """
    data = []
    count = 0

    count = fetch_and_append_pr_comments(
        pr, "get_issue_comments", "pr_issue_comment",
        data, count, max_count
    )

    if max_count and count >= max_count:
        return data, count

    count = fetch_and_append_pr_comments(
        pr, "get_review_comments", "pr_review_comment",
        data, count, max_count
    )

    return data, count


def get_pull_request_comments(max_count=None, max_workers=10):
    """
    Retrieve comments from all pull requests (both issue comments and review comments).
    Returns a filtered DataFrame excluding bots.
    """
    data, count = [], 0

    try:
        pulls = list(repo.get_pulls(state="all"))  
    except Exception as e:
        print(f"[!] Error fetching PRs: {e}")
        return pd.DataFrame()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_single_pr, pr, max_count) for pr in pulls]

        for future in tqdm(as_completed(futures), total=len(futures), desc="PR comments"):
            pr_data, pr_count = future.result()

            data.extend(pr_data)
            count += pr_count

            if max_count and count >= max_count:
                break

    return filter_bots(pd.DataFrame(data))


def get_all_comments(max_count=None):
    """
    Aggregate all comments from issues, pull requests, and commits, limited by max_count.
    Fetches issue comments concurrently, then PR comments, then commit comments.
    Returns a filtered DataFrame excluding bots.
    """
    data, count = [], 0
    print("Fetching issue comments...")
    try:
        issues = list(repo.get_issues())
    except Exception as e:
        print(f"[!] Error fetching issues: {e}")
        return pd.DataFrame()
    
    # Fetch issue comments concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_single_issue_comments, issue): issue for issue in issues}
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="All issue comments"):  
            comments = future.result()
            for comment in comments:
                comment["type"] = "issue_comment"
                if not append_with_limit(data, comment, count, max_count):
                    break
                count += 1
            if max_count and count >= max_count:
                break

    if max_count and count >= max_count:
        return filter_bots(pd.DataFrame(data))

    print("Fetching PR comments...")
    pr_df = get_pull_request_comments(max_count=(max_count - count) if max_count else None)
    data.extend(pr_df.to_dict(orient="records"))
    count = len(data)

    if max_count and count >= max_count:
        return filter_bots(pd.DataFrame(data))

    print("Fetching commit comments...")
    commit_df = get_commit_comments(max_count=(max_count - count) if max_count else None)
    data.extend(commit_df.to_dict(orient="records"))

    return filter_bots(pd.DataFrame(data))


def get_readme_contributors_remote():
    """
    Fetch the README file content from the remote repository as a UTF-8 string.
    Returns empty string if failed.
    """
    try:
        return repo.get_readme().decoded_content.decode("utf-8")
    except Exception as e:
        print(f" Unable to fetch README: {e}")
        return ""
    

def get_readme_contributors_remote_df(show_progress=True):
    """
    Fetch and parse the .all-contributorsrc JSON file from the repo root,
    convert contributors to a DataFrame with binary flags for contribution types.
    Returns empty DataFrame on failure.
    """
    try:
        file_content = repo.get_contents(".all-contributorsrc")
        raw = file_content.decoded_content.decode("utf-8")
        data = json.loads(raw)
    except Exception as e:
        print(f"[!] Failed to fetch .all-contributorsrc: {e}")
        return pd.DataFrame()
    
    contributors = data.get("contributors", [])
    rows = []
    
    iterator = contributors
    if show_progress:
        iterator = tqdm(contributors, desc="Readme contributors")

    for c in iterator:
        login = c.get("login")
        contribs = c.get("contributions", [])
        if not login:
            continue
        rows.append({
            "login": login.strip().lower(),
            **{t: 1 for t in contribs}
        })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows).fillna(0)
    int_cols = df.columns.drop("login")
    df[int_cols] = df[int_cols].astype(int)
    return df

 
def get_file_contributors(file_path="glossary.yml"):
    """
    Fetch commit history for a given file in the repo,
    count commits per contributor and return as a dict.
    Returns empty dict on failure.
    """
    try:
        commits = list(repo.get_commits(path=file_path))
    except Exception as e:
        print(f"[!] Error fetching commits for {file_path}: {e}")
        return {}

    counts = {}

    for commit in tqdm(commits, desc=f"Commits ({file_path})"):
        try:
            if commit.author and commit.author.login:
                login = commit.author.login.lower()
            else:
                login = (
                    commit.commit.author.email.lower()
                    if commit.commit.author
                    else "unknown"
                )

            counts[login] = counts.get(login, 0) + 1

        except Exception:
            continue

    return counts


def get_file_contributors_df(file_path="glossary.yml"):
    """
    Convert commit counts per contributor for a file into a pandas DataFrame.
    """
    contribs = get_file_contributors(file_path)
    return pd.DataFrame([{"contributor": k, "commits": v} for k, v in contribs.items()])
