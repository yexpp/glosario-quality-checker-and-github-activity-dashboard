import pandas as pd

def calculate_pr_merge_rate(pr_df):
    if pr_df.empty:
        print("No PR data available.")
        return 0
    total_pr = len(pr_df)
    merged_pr = pr_df["merged_at"].notnull().sum()
    merge_rate = merged_pr / total_pr * 100 if total_pr > 0 else 0
    print(f"Total PRs: {total_pr}, Merged PRs: {merged_pr}, Merge Rate: {merge_rate:.2f}%")
    return merge_rate

def analyze_pr_review_time(pr_df):
    if pr_df.empty:
        print("No PR data for review time analysis.")
        return

    merged_prs = pr_df.loc[pr_df["merged_at"].notnull()].copy()
    if merged_prs.empty:
        print("No merged PRs for review time analysis.")
        return

    merged_prs.loc[:, "duration"] = (merged_prs["merged_at"] - merged_prs["created_at"]).dt.days
    avg_duration = merged_prs["duration"].mean()
    print(f"Average PR merge time (days): {avg_duration:.2f}")

def analyze_issue_resolution(issue_df):
    if issue_df.empty:
        print("No Issue data for resolution analysis.")
        return

    closed_issues = issue_df.loc[issue_df["closed_at"].notnull()].copy()
    if closed_issues.empty:
        print("No closed issues for resolution analysis.")
        return

    closed_issues.loc[:, "resolution_time"] = (closed_issues["closed_at"] - closed_issues["created_at"]).dt.days
    median_resolution = closed_issues['resolution_time'].median()
    print(f"Median issue resolution time: {median_resolution} days")

def get_contribution_summary(commits_df, prs_df, issues_df, comments_df):
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

    rows = []
    for _, row in commits_df.iterrows():
        login = row["login"]
        for lang in row["languages"]:
            rows.append({"login": login, "language": lang})
    return pd.DataFrame(rows)

def get_contributor_language_stats(commits_df):

    lang_df = expand_commit_language_df(commits_df)
    stats = lang_df.groupby(["login", "language"]).size().unstack(fill_value=0)
    stats["all"] = stats.sum(axis=1)
    return stats

