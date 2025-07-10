import pandas as pd
from cache import cache_data
from github_api import get_contributors, get_commits, get_pull_requests, get_issues, get_issue_comments
from preprocess import (
    preprocess_commit_data,
    preprocess_pr_data,
    preprocess_issue_data,
    preprocess_comments_data
)
from analysis import (
    calculate_pr_merge_rate,
    analyze_pr_review_time,
    analyze_issue_resolution,
    expand_commit_language_df,
    get_contribution_summary,
    get_contributor_language_stats
)

def run_pipeline():

    contributors_df = cache_data("cache_contributors.pkl", get_contributors)
    commits_df = cache_data("cache_commits.pkl", get_commits)
    pr_df = cache_data("cache_prs.pkl", get_pull_requests)
    issue_df = cache_data("cache_issues.pkl", get_issues)
    comments_df = cache_data("cache_comments.pkl", get_issue_comments)

    commits_df = preprocess_commit_data(commits_df)
    pr_df = preprocess_pr_data(pr_df)
    issue_df = preprocess_issue_data(issue_df)
    comments_df = preprocess_comments_data(comments_df)

    stats_df = get_contributor_language_stats(commits_df)
    merge_rate = calculate_pr_merge_rate(pr_df)
    analyze_pr_review_time(pr_df)
    analyze_issue_resolution(issue_df)
    expand_commit_language_df(commits_df)
    contrib_summary_df = get_contribution_summary(commits_df, pr_df, issue_df, comments_df)

    return {
        "contributors_df": contributors_df,
        "commits_df": commits_df,
        "pr_df": pr_df,
        "issue_df": issue_df,
        "comments_df": comments_df,
        "stats_df": stats_df,
        "merge_rate": merge_rate,
        "contrib_summary_df": contrib_summary_df
    }
