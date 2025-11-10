import pandas as pd
import yaml
from collections import Counter

from github_client import repo
from data_fetch import get_contributors, get_readme_contributors_remote_df


def calculate_pr_merge_rate(pr_df):
    """
    Calculate the merge rate of pull requests in the given DataFrame.
    Returns the merge rate as a percentage and a descriptive message.
    """
    if pr_df.empty:
        msg = "No PR data available."
        return 0, msg
    
    total_pr = len(pr_df)
    merged_pr = pr_df["merged_at"].notnull().sum()
    merge_rate = merged_pr / total_pr * 100 if total_pr > 0 else 0
    
    msg = f"Total Pull Requests: {total_pr}, Merged: {merged_pr}, Merge Rate: {merge_rate:.2f}%"
    return merge_rate, msg


def analyze_pr_review_time(pr_df):
    """
    Analyse the average time taken to merge pull requests.
    Returns a summary string or a message if data is insufficient.
    """
    if pr_df.empty:
        return "No PR data for review time analysis."

    merged_prs = pr_df.loc[pr_df["merged_at"].notnull()].copy()
    if merged_prs.empty:
        return "No merged PRs for review time analysis."

    # Calculate duration in days between PR creation and merge
    merged_prs.loc[:, "duration"] = (merged_prs["merged_at"] - merged_prs["created_at"]).dt.days
    avg_duration = merged_prs["duration"].mean()
    return f"Average PR merge time (days): {avg_duration:.2f}"


def analyze_issue_resolution(issue_df):
    """
    Analyse the median time taken to resolve (close) issues.
    Returns a summary string or a message if data is insufficient.
    """
    if issue_df.empty:
        return "No Issue data for resolution analysis."

    closed_issues = issue_df.loc[issue_df["closed_at"].notnull()].copy()
    if closed_issues.empty:
        return "No closed issues for resolution analysis."

    # Calculate resolution time in days between issue creation and closure
    closed_issues.loc[:, "resolution_time"] = (closed_issues["closed_at"] - closed_issues["created_at"]).dt.days
    median_resolution = closed_issues['resolution_time'].median()
    return f"Median issue resolution time: {median_resolution} days"


def get_contribution_summary(commits_df, prs_df, issues_df, comments_df):
    """
    Summarise contributions per user across commits, pull requests,
    issues, and comments. Returns a DataFrame indexed by contributor login.
    """
    # Standardise contributor column name to 'login' if needed
    for df in [commits_df, prs_df, issues_df, comments_df]:
        if 'author' in df.columns and 'login' not in df.columns:
            df.rename(columns={'author': 'login'}, inplace=True)

    commit_count = commits_df['login'].value_counts().rename('commits') if 'login' in commits_df.columns else pd.Series(dtype=int, name='commits')
    pr_count = prs_df['login'].value_counts().rename('prs') if 'login' in prs_df.columns else pd.Series(dtype=int, name='prs')
    
    issue_count = issues_df['login'].value_counts().rename('issue') if 'login' in issues_df.columns and not issues_df.empty else pd.Series(dtype=int, name='issue')
    comment_count = comments_df['login'].value_counts().rename('comments') if 'login' in comments_df.columns and not comments_df.empty else pd.Series(dtype=int, name='comments')

    summary_df = pd.concat([commit_count, pr_count, issue_count, comment_count], axis=1).fillna(0).astype(int)

    return summary_df


def expand_commit_language_df(commits_df):
    """
    Expand commit language data into a long-format DataFrame with each row
    representing a contributor-language pair.
    """
    rows = []
    for _, row in commits_df.iterrows():
        login = row["login"]
        for lang in row["languages"]:
            rows.append({"login": login, "language": lang})
    return pd.DataFrame(rows)


def get_contributor_language_stats(commits_df):
    """
    Calculate contribution counts per programming language for each contributor.
    Returns a DataFrame with contributors as index and languages as columns,
    plus a total contribution count per contributor under 'all'.
    """
    lang_df = expand_commit_language_df(commits_df)
    stats = lang_df.groupby(["login", "language"]).size().unstack(fill_value=0)
    stats["all"] = stats.sum(axis=1)
    return stats


def find_missing_contributors_from_readme_and_github():
    """
    Compare contributors obtained via GitHub API with those listed in the
    README configuration. Prints contributors present on GitHub but absent
    from the README.
    """
    github_df = get_contributors()
    github_contributors = set(github_df['login'].str.lower())

    readme_df = get_readme_contributors_remote_df()
    readme_contribs = set(readme_df['login'].str.lower())

    missing = github_contributors - readme_contribs
    print(f"Contributors on GitHub but missing in README (username): {len(missing)}")
    for user in missing:
        print(user)


def count_languages_in_glossary(file_path="glossary.yml"):
    """
    Count occurrences of language codes within the glossary YAML file.
    Returns a DataFrame of language codes and their respective entry counts.
    """
    try:
        content_file = repo.get_contents(file_path)
        raw = content_file.decoded_content.decode("utf-8")
        glossary = yaml.safe_load(raw)
    except Exception as e:
        print(f"Unable to read or parse {file_path}：{e}")
        return pd.DataFrame()

    lang_counter = Counter()

    if isinstance(glossary, dict):
 
        for slug, translations in glossary.items():
            if isinstance(translations, dict):
                for lang_code in translations.keys():
                    lang_counter[lang_code] += 1
    elif isinstance(glossary, list):
 
        for entry in glossary:
            if isinstance(entry, dict):
               
                for key in entry.keys():
                    if key not in ("slug", "id", "title"):  
                        lang_counter[key] += 1
    else:
        print("The glossary data structure is neither a dict nor a list.")
        return pd.DataFrame()

    df = pd.DataFrame(lang_counter.items(), columns=["language", "entry_count"])
    return df.sort_values("entry_count", ascending=False).reset_index(drop=True)
