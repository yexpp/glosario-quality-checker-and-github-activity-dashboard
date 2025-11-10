import pandas as pd

def preprocess_commit_data(commit_df):
    if not commit_df.empty:
        commit_df["date"] = pd.to_datetime(commit_df["date"]).dt.tz_localize(None)
    return commit_df

def preprocess_pr_data(pr_df):
    if not pr_df.empty:
        pr_df["created_at"] = pd.to_datetime(pr_df["created_at"]).dt.tz_localize(None)
        pr_df["merged_at"] = pd.to_datetime(pr_df["merged_at"]).dt.tz_localize(None)
    return pr_df

def preprocess_issue_data(issue_df):
    if not issue_df.empty:
        issue_df["created_at"] = pd.to_datetime(issue_df["created_at"]).dt.tz_localize(None)
        issue_df["closed_at"] = pd.to_datetime(issue_df["closed_at"]).dt.tz_localize(None)
    return issue_df

def preprocess_comments_data(comments_df):
    if not comments_df.empty:
        if "created_at" in comments_df.columns:
            comments_df["created_at"] = pd.to_datetime(comments_df["created_at"]).dt.tz_localize(None)
    return comments_df
