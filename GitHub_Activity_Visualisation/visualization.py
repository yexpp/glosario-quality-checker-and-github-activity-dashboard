import json
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import squarify

from anytree import Node, RenderTree
from data_fetch import get_file_contributors_df


# Default issue labels used by the function `plot_issue_labels` for filtering and plotting issue counts
DEFAULT_TARGET_LABELS = [
    "enhancement", "bug", "question",
    "good first issue", "infrastructure", "help wanted"
]

def plot_contributor_activity_interactive(stats_df, top_n=10, language_cols=None):
    """Plot interactive bar chart of top contributors sorted by overall and per-language commits."""
    stats_df = stats_df.copy()

    if 'all' not in stats_df.columns:
        raise ValueError("DataFrame must contain 'all' column for sorting.")

    # Ensure 'login' column exists for x-axis labels
    if stats_df.index.name is None:
        stats_df = stats_df.reset_index().rename(columns={stats_df.columns[0]: 'login'})
    elif 'login' not in stats_df.columns:
        stats_df = stats_df.reset_index()

    # Determine language columns if not provided
    if language_cols is None:
        language_cols = [col for col in stats_df.columns if col not in ['login', 'all']]

    fig = go.Figure()
    all_traces = []
    visibility_matrix = []

    sort_fields = ['all'] + language_cols

    # Create a trace for each sorting category
    for sort_index, sort_field in enumerate(sort_fields):
        sorted_df = stats_df.sort_values(sort_field, ascending=False).head(top_n)
        x = sorted_df['login']
        y_vals = sorted_df[sort_field]
        trace_name = 'All' if sort_field == 'all' else sort_field.capitalize()

        trace = go.Bar(x=x, y=y_vals, name=trace_name, visible=(sort_index == 0))
        all_traces.append(trace)

        # Visibility toggle for each sorting category
        visibility = [False] * len(sort_fields)
        visibility[sort_index] = True
        visibility_matrix.append(visibility)

    # Add all traces to figure
    for trace in all_traces:
        fig.add_trace(trace)

    # Create buttons to switch between sorting categories
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

    # Layout with update menu for interactive buttons
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
        title={'text': f"Top {top_n} Contributors (Sorted by All)", 'pad': {'b': 50}},
        xaxis_title="Contributors",
        yaxis_title="Commits",
        legend_title="Category",
        height=500,
        width=900
    )

    fig.show()


def plot_contributor_activity_multi(contrib_summary_df):
    """Plot multiple bar charts showing top contributors by commits, PRs, issues, comments and total."""
    contrib_summary_df = contrib_summary_df.copy()

    # Ensure 'login' column for x-axis labels
    if contrib_summary_df.index.name is None and 'login' not in contrib_summary_df.columns:
        raise ValueError("DataFrame must have 'login' column or login as index.")
    elif contrib_summary_df.index.name is not None:
        contrib_summary_df = contrib_summary_df.reset_index().rename(columns={contrib_summary_df.index.name: 'login'})

    categories = ['commits', 'prs', 'issue', 'comments']
    sorted_data = {}

    # Sort top 10 contributors per category
    for cat in categories:
        sorted_df = contrib_summary_df.sort_values(cat, ascending=False).head(10)
        sorted_data[cat] = {'x': sorted_df['login'].tolist(), 'y': sorted_df[cat].tolist()}

    # Calculate total contributions and get top 10
    contrib_summary_df['total'] = contrib_summary_df[categories].sum(axis=1)
    total_sorted = contrib_summary_df.sort_values('total', ascending=False).head(10)
    sorted_data['total'] = {'x': total_sorted['login'].tolist(), 'y': total_sorted['total'].tolist()}

    fig = go.Figure()

    # Add total contributions trace (visible by default)
    fig.add_trace(go.Bar(x=sorted_data['total']['x'], y=sorted_data['total']['y'], name='Total', visible=True))

    # Add category traces (hidden by default)
    for cat in categories:
        fig.add_trace(go.Bar(x=sorted_data[cat]['x'], y=sorted_data[cat]['y'], name=cat.capitalize(), visible=False))

    buttons = []

    # Button for total contributions
    buttons.append(dict(
        label='All',
        method='update',
        args=[{
            'visible': [True] + [False]*len(categories),
            'x': [sorted_data['total']['x']] + [None]*len(categories),
            'y': [sorted_data['total']['y']] + [None]*len(categories)
        },
        {'title': "Top 10 Contributors - Total Contribution", 'barmode': 'group'}]
    ))

    # Buttons for each category
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
            {'title': f"Top 10 Contributors - {cat.capitalize()}", 'barmode': 'group'}]
        ))

        # Set x and y data for selected category trace
        buttons[-1]['args'][0]['x'][i+1] = sorted_data[cat]['x']
        buttons[-1]['args'][0]['y'][i+1] = sorted_data[cat]['y']

    # Configure layout with update menu
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


def plot_top_contributors(glossary_contribs_df, top_n=10, contrib_type="commits"):
    """Plot bar chart for top contributors by a specific contribution type."""
    if contrib_type not in glossary_contribs_df.columns:
        print(f"[!] '{contrib_type}' not in the DataFrame.")
        return

    # Sort and select top contributors
    contrib_df = glossary_contribs_df.sort_values(by=contrib_type, ascending=True).tail(top_n)

    plt.figure(figsize=(10,6))
    sns.barplot(x=contrib_type, y="contributor", data=contrib_df, hue="contributor",
                palette="Blues_d", legend=False)
    plt.xlabel("Number of Contributions")
    plt.ylabel("Contributor")
    plt.title(f"Top {top_n} Contributors by the number of commits on glossary.yml")
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()


def plot_contribution_type_barplot(readme_contribs_df):
    """Plot bar chart showing total contributions by type."""
    # Ensure 'login' column exists
    if 'login' not in readme_contribs_df.columns:
        if readme_contribs_df.index.name == 'login':
            readme_contribs_df = readme_contribs_df.reset_index()
        else:
            raise ValueError("DataFrame lacks 'login' column and index is not 'login'.")

    contrib_types = readme_contribs_df.columns.difference(['login'])

    # Sum contributions per type
    sums = readme_contribs_df[contrib_types].sum().sort_values(ascending=False)

    plt.figure(figsize=(6, 5))
    sns.barplot(x=sums.index, y=sums.values)

    plt.title("Contributions by Contribution Type")
    plt.xlabel("Contribution Type")
    plt.ylabel("Total Number of Contributions")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def plot_commit_count_barchart(contributors_df):
    """Plot distribution of contributors by commit count ranges."""
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


def plot_monthly_unique_committers(commits_df):
    """Plot monthly count of unique committers."""
    if commits_df.empty:
        print("No commit data available.")
        return
    
    commits_df = commits_df.copy()
    commits_df["month"] = commits_df["date"].dt.to_period("M")
    
    monthly_unique_committers = commits_df.groupby("month")["login"].nunique()

    plt.figure(figsize=(12, 5))
    monthly_unique_committers.plot(marker="o", color="green")
    plt.xlabel("Month")
    plt.ylabel("Number of Unique Committers")
    plt.title("Monthly Unique Committers Over Time")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.show()


def plot_commit_heatmap(commit_df):
    """Plot heatmap of commit activity by weekday and hour."""
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
    


def plot_commit_frequency(commit_df):
    """Plot monthly commit frequency over time."""
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



def plot_retention_curve(commits_df):
    """Plot contributor retention curve showing how many contributors remain active over months since their first commit."""
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

    
def plot_pr_trend(pr_df):
    """Plot monthly pull requests counts broken down by their state (open, closed) as a stacked bar chart."""
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


def plot_pr_created_vs_merged(pr_df):
    """Plot the monthly counts of pull requests created versus merged over time."""
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
    plt.title("Pull Request Created vs. Merged Over Time")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.show()

def plot_pr_merge_pie_plotly(pr_df):
    """Plot a pie chart showing the distribution of pull request statuses: open, closed and merged, closed but not merged."""
    if pr_df.empty:
        print("No PR data available.")
        return

    open_count = pr_df[pr_df["state"] == "open"].shape[0]

    closed_prs = pr_df[pr_df["state"] == "closed"]
    merged_count = closed_prs["merged_at"].notna().sum()
    not_merged_count = closed_prs["merged_at"].isna().sum()

    df_pie = pd.DataFrame({
        "Status": ["Open", "Closed and Merged", "Closed but Not Merged"],
        "Count": [open_count, merged_count, not_merged_count]
    })

    df_pie = df_pie[df_pie["Count"] > 0]

    fig = px.pie(
        df_pie,
        values="Count",
        names="Status",
        title="Pull Request Status Distribution",
        color="Status",
        color_discrete_map={
            "Open": "#4B79A1",
            "Closed and Merged": "#70A99A",
            "Closed but Not Merged": "#D9534F"
        }
    )
    fig.show()


def plot_merge_time(pr_df):
    """Plot the distribution of pull request merge times (in days) as a histogram."""
    if pr_df.empty:
        print("No PR data available.")
        return

    pr_df = pr_df.copy()

    pr_df["merge_time"] = (pr_df["merged_at"] - pr_df["created_at"]).dt.days
    data = pr_df["merge_time"].dropna()

    if data.nunique() < 2:
        print("Not enough merge time data for plotting.")
        return

    plt.figure(figsize=(10, 5))
    plt.hist(data, bins=20, color="skyblue", edgecolor="black")
    plt.xlabel("Merge Time (days)")
    plt.ylabel("Frequency")
    plt.title("Distribution of Pull Requests Merge Time")
    plt.tight_layout()
    plt.show()



def plot_language_label_treemap(pr_df, label_col='language_labels', top_n=10, font_size=14, lang_json_path='language-codes.json'):
    """Plot a treemap of the top N natural language labels in pull requests."""
    try:
        with open(lang_json_path, 'r', encoding='utf-8') as f:
            lang_map = json.load(f)
    except Exception as e:
        print(f"Failed to load language code mapping file: {e}")
        return

    all_languages = []
    for langs in pr_df[label_col]:
        if langs:
            all_languages.extend([lang.strip().lower() for lang in langs])


    language_counts = Counter(all_languages)
    lang_df = pd.DataFrame(language_counts.items(), columns=['Language', 'Count'])
    lang_df = lang_df.sort_values(by='Count', ascending=False).head(top_n)
    
    def get_lang_name(code):
        return f"{code} ({lang_map.get(code, 'Unknown')})"

    labels = [f"{get_lang_name(lang)}\n{count}" for lang, count in zip(lang_df['Language'], lang_df['Count'])]

    cmap = cm.get_cmap('tab20')
    colors = [cmap(i / top_n) for i in range(top_n)]

    plt.figure(figsize=(12, 8))
    squarify.plot(
        sizes=lang_df['Count'],
        label=labels,
        color=colors,
        alpha=0.8,
        text_kwargs={'fontsize': font_size}
    )
    plt.axis('off')
    plt.title(f'Top {top_n} Natural Language Labels in Pull Requests (Treemap)', fontsize=font_size + 2)
    plt.show()



def print_language_label_tree(pr_df, label_col='language_labels', state_col='state', root_label='lang', lang_json_path='language-codes.json'):
    """Print a hierarchical tree of language labels in pull requests, showing counts by open and closed states."""
    with open(lang_json_path, 'r', encoding='utf-8') as f:
        lang_map = json.load(f)

    pr_with_lang = pr_df[pr_df[label_col].apply(lambda x: bool(x) and len(x) > 0)]
    pr_count = len(pr_with_lang)

    total_counter = Counter()
    open_counter = Counter()
    closed_counter = Counter()

    for _, row in pr_with_lang.iterrows():
        langs = [lang.strip().lower() for lang in row[label_col]]
        state = str(row.get(state_col, '')).lower()
        for lang in langs:
            total_counter[lang] += 1
            if state == 'open':
                open_counter[lang] += 1
            elif state == 'closed':
                closed_counter[lang] += 1

    total_occurrences = sum(total_counter.values())

    print(f"There are {pr_count} pull requests involving languages ({total_occurrences} total language label occurrences)\n")
    print(root_label)

    top_langs = total_counter.most_common()
    for i, (lang, count) in enumerate(top_langs):
        connector = "└──" if i == len(top_langs) - 1 else "├──"
        lang_name = lang_map.get(lang, "Unknown")
        open_count = open_counter.get(lang, 0)
        closed_count = closed_counter.get(lang, 0)
        print(f"{connector} {lang_name} ({lang}): total {count}, open {open_count}, closed {closed_count}")

    

def plot_issue_monthly_trend(issue_df):
    """Plot the monthly trend of GitHub issues based on their creation dates."""
    issue_df['created_at'] = pd.to_datetime(issue_df['created_at'], errors='coerce')

    issue_df = issue_df.dropna(subset=['created_at'])

    issue_df['year_month'] = issue_df['created_at'].dt.to_period('M')
    monthly_counts = issue_df.groupby('year_month').size().reset_index(name='count')


    monthly_counts['year_month'] = monthly_counts['year_month'].astype(str)

    plt.figure(figsize=(11, 6))
    plt.plot(monthly_counts['year_month'], monthly_counts['count'], marker='o')
    plt.xticks(rotation=45)
    plt.xlabel('Year-Month')
    plt.ylabel('Number of Issues')
    plt.title('Monthly Trend of GitHub Issues')
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_issue_resolution_time_distribution(issue_df):
    """Plot boxplot and histogram showing the distribution of issue resolution times."""
    if issue_df.empty:
        print("No Issue data available for plotting resolution time.")
        return

    issue_df = issue_df.copy()
    issue_df["resolution_time"] = (issue_df["closed_at"] - issue_df["created_at"]).dt.days

    data = issue_df["resolution_time"].dropna()

    if data.empty:
        print("No closed issues to plot resolution time.")
        return

    plt.figure(figsize=(12, 6))

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


def plot_issue_labels(issue_df, target_labels=None):
    """Plot a horizontal bar chart of issue counts for selected target labels."""
    if target_labels is None:
        target_labels = DEFAULT_TARGET_LABELS
    
    label_counter = Counter()

    for labels in issue_df['labels']:
        for label in labels:
            if label in target_labels:
                label_counter[label] += 1

    if not label_counter:
        print("No data found for the specified labels.")
        return

    label_df = pd.DataFrame(label_counter.items(), columns=['label', 'count']).sort_values(by='count', ascending=False)


    palette = sns.color_palette("Blues_d", n_colors=len(label_df))
    colors = palette[::-1]  

    plt.figure(figsize=(10, 6))
    bars = plt.barh(label_df['label'], label_df['count'], color=colors)

    plt.title("Issue Count by Label (based on repository management)")
    plt.xlabel("Issue Count")
    plt.ylabel("Label")
    plt.gca().invert_yaxis() 
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

    
def plot_lang_labels(issue_df, lang_json_path='language-codes.json'):
    """Print a hierarchical tree of language-related issue labels, with counts separated by open and closed states."""
    with open(lang_json_path, 'r', encoding='utf-8') as f:
        lang_map = json.load(f)

    label_counter = Counter()
    open_counter = Counter()
    closed_counter = Counter()

    for idx, row in issue_df.iterrows():
        labels = row['labels']
        state = row.get('state', '').lower()  
        for label in labels:
            if label.startswith("lang:"):
                label_counter[label] += 1
                if state == 'open':
                    open_counter[label] += 1
                elif state == 'closed':
                    closed_counter[label] += 1

    if not label_counter:
        print("No labels starting with 'lang:' were found.")
        return

    total_issues = sum(label_counter.values())
    total_open = sum(open_counter.values())
    total_closed = sum(closed_counter.values())

    print(f"There are {total_issues} issues involving languages (open: {total_open}, closed: {total_closed}).\n")


    root = Node("lang")


    for label, count in sorted(label_counter.items(), key=lambda x: x[1], reverse=True):
        lang_code = label.split("lang:")[1].strip().lower()
        lang_name = lang_map.get(lang_code, "Unknown")
        open_count = open_counter.get(label, 0)
        closed_count = closed_counter.get(label, 0)
        node_label = f"{lang_name} ({lang_code}): total: {count}, open: {open_count}, closed: {closed_count}"
        Node(node_label, parent=root)

    for pre, fill, node in RenderTree(root):
        print(f"{pre}{node.name}")

