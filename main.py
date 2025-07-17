import pandas as pd
from github_client import repo
from cache import cache_data
from data_fetch import (
    get_contributors, get_commits, get_pull_requests, get_issues,
    get_issue_comments, get_readme_contributors_remote_df, get_file_contributors_df,
)
from preprocess import (
    preprocess_commit_data, preprocess_pr_data, preprocess_issue_data, preprocess_comments_data
)
from analysis import (
    calculate_pr_merge_rate, analyze_pr_review_time, analyze_issue_resolution,
    expand_commit_language_df, get_contribution_summary, get_contributor_language_stats,
    count_languages_in_glossary,find_missing_contributors_from_readme_and_github
)

def run_pipeline():
    # Load data (use cache if available, otherwise fetch from API)
    contributors_df = cache_data("cache_contributors.json", get_contributors)
    commits_df = cache_data("cache_commits.json", get_commits)
    pr_df = cache_data("cache_prs.json", get_pull_requests)
    issue_df = cache_data("cache_issues.json", get_issues)
    comments_df = cache_data("cache_comments.json", get_issue_comments)
    glossary_contribs_df = cache_data("cache_glossary_contribs.json", get_file_contributors_df)
    readme_contribs_df = cache_data("cache_readme_contributors.json", get_readme_contributors_remote_df)  

    # Merge README contributors with glossary commit counts, fill missing with zero
    df_commit_counts = glossary_contribs_df.rename(columns={"contributor": "login"}).set_index("login")
    df_merged = readme_contribs_df.join(df_commit_counts, how="left").fillna(0)
    df_merged["commits"] = df_merged["commits"].astype(int)

    # Preprocess data for analysis
    commits_df = preprocess_commit_data(commits_df)
    pr_df = preprocess_pr_data(pr_df)
    issue_df = preprocess_issue_data(issue_df)
    comments_df = preprocess_comments_data(comments_df)

    # Perform stats and analyses
    stats_df = get_contributor_language_stats(commits_df)
    merge_rate = calculate_pr_merge_rate(pr_df)
    analyze_pr_review_time(pr_df)
    analyze_issue_resolution(issue_df)
    expand_commit_language_df(commits_df)
    contrib_summary_df = get_contribution_summary(commits_df, pr_df, issue_df, comments_df)
    glossary_lang_df = count_languages_in_glossary()


    # Reset the index of each DataFrame in the list to start from 1
    dfs_to_fix = [
    commits_df,
    pr_df,
    issue_df,
    comments_df,
    contributors_df,
    readme_contribs_df,     
    glossary_contribs_df,    
    glossary_lang_df
]

    for df in dfs_to_fix:
        df.index = range(1, len(df) + 1)
    

    # Return all results
    return {
        "contributors_df": contributors_df,
        "commits_df": commits_df,
        "pr_df": pr_df,
        "issue_df": issue_df,
        "comments_df": comments_df,
        "readme_contribs_df": readme_contribs_df,
        "stats_df": stats_df,
        "merge_rate": merge_rate,
        "contrib_summary_df": contrib_summary_df,
        "glossary_contribs_df": glossary_contribs_df,
        "glossary_lang_df": glossary_lang_df,
    }
