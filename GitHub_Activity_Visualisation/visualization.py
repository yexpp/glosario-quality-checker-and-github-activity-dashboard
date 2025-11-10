import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def plot_contributor_activity_interactive(stats_df, top_n=10, language_cols=None):
    stats_df = stats_df.copy()

    if 'all' not in stats_df.columns:
        raise ValueError("DataFrame must contain 'all' column for sorting.")

    if stats_df.index.name is None:
        stats_df = stats_df.reset_index().rename(columns={stats_df.columns[0]: 'login'})
    elif 'login' not in stats_df.columns:
        stats_df = stats_df.reset_index()

    if language_cols is None:
        language_cols = [col for col in stats_df.columns if col not in ['login', 'all']]

    fig = go.Figure()
    all_traces = []         
    visibility_matrix = []   

    sort_fields = ['all'] + language_cols

    for sort_index, sort_field in enumerate(sort_fields):
        sorted_df = stats_df.sort_values(sort_field, ascending=False).head(top_n)
        x = sorted_df['login']

        if sort_field == 'all':
            y_vals = sorted_df['all']
            trace_name = 'All'
        else:
            y_vals = sorted_df[sort_field]
            trace_name = sort_field.capitalize()

        trace = go.Bar(
            x=x,
            y=y_vals,
            name=trace_name,
            visible=(sort_index == 0)
        )
        all_traces.append(trace)

        visibility = [False] * len(sort_fields)
        visibility[sort_index] = True
        visibility_matrix.append(visibility)

    for trace in all_traces:
        fig.add_trace(trace)

    buttons = []
    for i, sort_field in enumerate(sort_fields):
        buttons.append(dict(
            label=sort_field.capitalize(),
            method='update',
            args=[
                {'visible': visibility_matrix[i]},
                {'title': f"Top {top_n} Contributors (Sorted by {sort_field.capitalize()})"}
            ]
        ))

    fig.update_layout(
        updatemenus=[dict(
            type='buttons',
            direction='right',
            buttons=buttons,
            showactive=True,
            x=0.5,
            y=1.15,
            xanchor='center',
            yanchor='top'
        )],
        barmode='group',
        title={
            'text': f"Top {top_n} Contributors (Sorted by All)",
            'pad': {'b': 50}  
        },

        xaxis_title="Contributors",
        yaxis_title="Commits",
        legend_title="Category",
        height=500,
        width=900
    )

    fig.show()


def plot_retention_curve(commits_df):
    if commits_df.empty:
        print("No commit data available.")
        return

    df = commits_df.copy()
    df['month'] = df['date'].dt.to_period('M')

    first_month = df.groupby('login')['month'].min().rename('first_month')

    df = df.merge(first_month, on='login')

    df['month_offset'] = (df['month'] - df['first_month']).apply(lambda x: x.n)

    retention_counts = df.groupby(['first_month', 'month_offset'])['login'].nunique().unstack(fill_value=0)

    cohort_sizes = retention_counts[0]

    retention = retention_counts.divide(cohort_sizes, axis=0)

    plt.figure(figsize=(14, 8))
    sns.heatmap(
        retention.iloc[:, :12],  
        annot=True,
        fmt='.2%',             
        cmap='Blues',
        cbar_kws={'label': 'Retention Rate'},
        annot_kws={"size": 8}   
    )
    plt.title('Contributor Retention Curve (First 12 Months)')
    plt.xlabel('Months Since First Contribution')
    plt.ylabel('First Contribution Month (Cohort)')
    plt.xticks(rotation=45) 
    plt.yticks(rotation=0)  
    plt.tight_layout()       
    plt.show()

def plot_commit_count_barchart(contributors_df):
    if contributors_df.empty:
        print("No contributor data available.")
        return

    df = contributors_df.dropna(subset=['contributions'])


    bins = [0, 1, 5, 10, 20, float('inf')]
    labels = ['1 time', '2–5 times', '6–10 times', '11–20 times', '20+ times']

    df = df[df['contributions'] >= 1]  
    df['commit_range'] = pd.cut(df['contributions'], bins=bins, labels=labels, right=True)

    count_by_range = df['commit_range'].value_counts().reindex(labels, fill_value=0)

    plt.figure(figsize=(8, 5))
    count_by_range.plot(kind='bar', color='skyblue', edgecolor='black')
    plt.title('Distribution of Contributor Commit Counts')
    plt.xlabel('Commit Count Range')
    plt.ylabel('Number of Contributors')
    plt.xticks(rotation=0)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

def plot_contributor_activity_multi(contrib_summary_df):
    contrib_summary_df = contrib_summary_df.copy()

    if contrib_summary_df.index.name is None and 'login' not in contrib_summary_df.columns:
        raise ValueError("DataFrame must have 'login' column or login as index.")
    elif contrib_summary_df.index.name is not None:
        contrib_summary_df = contrib_summary_df.reset_index().rename(columns={contrib_summary_df.index.name: 'login'})

    categories = ['commits', 'prs', 'issue', 'comments']

    sorted_data = {}
    for cat in categories:
        sorted_df = contrib_summary_df.sort_values(cat, ascending=False).head(10)
        sorted_data[cat] = {
            'x': sorted_df['login'].tolist(),
            'y': sorted_df[cat].tolist()
        }

    contrib_summary_df['total'] = contrib_summary_df[categories].sum(axis=1)
    total_sorted = contrib_summary_df.sort_values('total', ascending=False).head(10)
    sorted_data['total'] = {
        'x': total_sorted['login'].tolist(),
        'y': total_sorted['total'].tolist()
    }

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=sorted_data['total']['x'],
        y=sorted_data['total']['y'],
        name='Total',
        visible=True
    ))

    for cat in categories:
        fig.add_trace(go.Bar(
            x=sorted_data[cat]['x'],
            y=sorted_data[cat]['y'],
            name=cat.capitalize(),
            visible=False
        ))

    buttons = []

    buttons.append(dict(
        label='All',
        method='update',
        args=[{
            'visible': [True] + [False]*len(categories),
            'x': [sorted_data['total']['x']] + [None]*len(categories),
            'y': [sorted_data['total']['y']] + [None]*len(categories)
        },
        {'title': "Top 10 Contributors - Total Contribution",
         'barmode': 'group'}]
    ))

    for i, cat in enumerate(categories):
        visible = [False] * (1 + len(categories))
        visible[i+1] = True

        buttons.append(dict(
            label=cat.capitalize(),
            method='update',
            args=[{
                'visible': visible,
                'x': [None] * (1 + len(categories)),
                'y': [None] * (1 + len(categories))
            },
            {'title': f"Top 10 Contributors - {cat.capitalize()}",
             'barmode': 'group'}]
        ))

        buttons[-1]['args'][0]['x'][i+1] = sorted_data[cat]['x']
        buttons[-1]['args'][0]['y'][i+1] = sorted_data[cat]['y']

    fig.update_layout(
        updatemenus=[dict(
            active=0,
            buttons=buttons,
            x=1.15,
            y=1
        )],
        title="Top 10 Contributors - Total Contribution",
        barmode='group'
    )

    fig.show()

def plot_monthly_unique_committers(commits_df):
    if commits_df.empty:
        print("No commit data available.")
        return
    
    commits_df = commits_df.copy()
    commits_df["month"] = commits_df["date"].dt.to_period("M")
    
    monthly_unique_committers = commits_df.groupby("month")["login"].nunique()

    plt.figure(figsize=(12, 5))
    monthly_unique_committers.plot(marker="o", color="purple")
    plt.xlabel("Month")
    plt.ylabel("Number of Unique Committers")
    plt.title("Monthly Unique Committers Over Time")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.show()

def plot_commit_frequency(commit_df):
    if commit_df.empty or "date" not in commit_df.columns:
        print("No commit data available or missing 'date' column.")
        return
    
    commit_df = commit_df.copy()
    commit_df["month"] = commit_df["date"].dt.to_period("M")
    monthly_commits = commit_df.groupby("month").size()
    
    if monthly_commits.empty:
        print("No commit frequency data to plot.")
        return
    commit_df["month"] = commit_df["date"].dt.to_period("M")
    monthly_commits = commit_df.groupby("month").size()
    plt.figure(figsize=(12, 5))
    monthly_commits.plot(marker='o', color='blue')
    plt.title("Monthly Commit Frequency")
    plt.xlabel("Commit Month (Year-Month)")
    plt.ylabel("Number of Commits")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def plot_pr_trend(pr_df):
    if pr_df.empty:
        print("No PR data available.")
        return
    pr_df = pr_df.copy()
    pr_df["month"] = pr_df["created_at"].dt.to_period("M")
    monthly_pr = pr_df.groupby(["month", "state"]).size().unstack(fill_value=0)

    monthly_pr.plot(kind="bar", stacked=True, figsize=(12, 6), colormap="Paired")
    plt.title("Monthly Pull Requests by State")
    plt.xlabel("Month")
    plt.ylabel("Number of PRs")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def plot_pr_trend1(pr_df):
    if pr_df.empty:
        print("No PR data available.")
        return
    pr_df = pr_df.copy()
    pr_df["created_month"] = pr_df["created_at"].dt.to_period("M")
    pr_df["merged_month"] = pr_df["merged_at"].dt.to_period("M")
    
    created_counts = pr_df.groupby("created_month").size()
    merged_counts = pr_df.groupby("merged_month").size()

    plt.figure(figsize=(12, 5))
    created_counts.plot(label="Created", marker="o", linestyle="-", color="orange")
    merged_counts.plot(label="Merged", marker="x", linestyle="--", color="green")
    plt.xlabel("Month")
    plt.ylabel("Number of PRs")
    plt.title("PR Created vs. Merged Over Time")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.show()

def plot_pr_merge_pie_plotly(pr_df):
    if pr_df.empty:
        print("No PR data available.")
        return

    closed_prs = pr_df[pr_df["state"] == "closed"]

    merged_count = closed_prs["merged_at"].notna().sum()
    not_merged_count = closed_prs["merged_at"].isna().sum()

    df_pie = pd.DataFrame({
        "Status": ["Merged", "Not Merged"],
        "Count": [merged_count, not_merged_count]
    })

    fig = px.pie(df_pie, values="Count", names="Status",
                 title="PR Merge Status Distribution (Closed PRs Only)",
                 color="Status",
                 color_discrete_map={"Merged": "green", "Not Merged": "red"})
    fig.show()

def plot_merge_time(pr_df):
    if pr_df.empty:
        print("No PR data available.")
        return

    pr_df = pr_df.copy()

    pr_df["created_at"] = pd.to_datetime(pr_df["created_at"], errors='coerce')
    pr_df["merged_at"] = pd.to_datetime(pr_df["merged_at"], errors='coerce')

    pr_df["merge_time"] = (pr_df["merged_at"] - pr_df["created_at"]).dt.days
    data = pr_df["merge_time"].dropna()

    if data.nunique() < 2:
        print("Not enough merge time data for plotting.")
        return

    plt.figure(figsize=(10, 5))
    plt.hist(data, bins=20, color="skyblue", edgecolor="black")
    plt.xlabel("Merge Time (days)")
    plt.ylabel("Frequency")
    plt.title("Distribution of PR Merge Time")
    plt.tight_layout()
    plt.show()
    
def plot_commit_heatmap(commit_df):
    if commit_df.empty:
        print("No commit data available.")
        return
    commit_df = commit_df.copy()
    commit_df["weekday"] = commit_df["date"].dt.day_name()
    commit_df["hour"] = commit_df["date"].dt.hour
    heatmap_data = commit_df.groupby(["weekday", "hour"]).size().unstack(fill_value=0)

    weekdays_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(weekdays_order)

    plt.figure(figsize=(12, 6))
    sns.heatmap(heatmap_data, cmap="Blues", linewidths=0.5)
    plt.title("Commit Activity Heatmap (Weekday vs Hour)")
    plt.xlabel("Hour of Day")
    plt.ylabel("Weekday")
    plt.show()

def plot_issue_resolution_time_distribution(issue_df):
    if issue_df.empty:
        print("No Issue data available for plotting resolution time.")
        return

    issue_df = issue_df.copy()
    issue_df["resolution_time"] = (issue_df["closed_at"] - issue_df["created_at"]).dt.days

    data = issue_df["resolution_time"].dropna()

    if data.empty:
        print("No closed issues to plot resolution time.")
        return

    plt.figure(figsize=(14, 6))

    plt.subplot(1, 2, 1)
    plt.boxplot(data, vert=True, patch_artist=True, boxprops=dict(facecolor="skyblue"))
    plt.title("Issue Resolution Time Boxplot")
    plt.ylabel("Resolution Time (days)")
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.hist(data, bins=20, color="lightgreen", edgecolor="black")
    plt.title("Issue Resolution Time Histogram")
    plt.xlabel("Resolution Time (days)")
    plt.ylabel("Frequency")
    plt.grid(True)

    plt.tight_layout()
    plt.show()
