Open Source Project Monitoring: GitHub Activity and Quality Assessment of Glosario

1. Project Overview

This project, implemented in Python, comprises two core modules: the Automated Glossary Quality Checking System and GitHub Repository Activity & Collaboration Analysis. It aims to enhance glossary quality management and transparency in open-source community collaboration, providing multi-dimensional automated validation and visual analytics to support knowledge management and community growth in open-source projects.

The project is particularly designed for open-source maintainers, researchers, and community contributors, helping them to quickly identify issues, optimise collaboration workflows, and support continuous integration and automated quality assurance.


2. Key Features

Automated Glossary Quality Checking System

Automated Validation: Covers multi-dimensional checks, including glossary compliance, completeness, citation verification, and cross-language reference consistency.
Tiered Output: Four levels of information (info, warning, error, exception) with colour-coded indicators in a local dashboard for rapid issue localisation.
Structured Reports: Groups cross-language links by entry and language to improve readability.
Interactive Visualisation: Uses Jupyter Notebook with colour blocks to intuitively display validation metrics for easier diagnosis and correction.
Continuous Integration Support: Automatically triggered validation via GitHub Actions to ensure quality in collaborative environments.

GitHub Repository Activity & Collaboration Analysis

This module analyses GitHub repository activity data and collaboration patterns across multiple dimensions, covering contributor behaviour, commit dynamics, pull request (PR) and issue handling, as well as README file content analysis.
Key capabilities include:
Analysing monthly activity, commit trends, PR status and turnaround times, and issue resolution.
Providing in-depth insights into contributor lifecycles, multilingual contributions, and contribution type distributions.
Detecting missing contributor information in README files.
Visualising all metrics with support for interactive exploration.


3. Project Directory Structure

/README.md
/requirements.txt
/GitHub_Activity_Visualisation/
├── analysis.py
├── cache.py
├── config.py
├── data_fetch.py
├── github_client.py
├── language-codes.json
├── main.py
├── preprocess.py
├── repo_activity_dashboard.ipynb
├── utils.py
└── visualisation.py

/Quality_Assessment/
├── glossary_check.yml
├── glossary_checker.ipynb
├── glossary_checker.py
├── glossary_check_runner.py
└── language-codes.json
 

4. Installation and Dependencies

System Requirements
Python 3.8 or later
Jupyter Notebook

Installing Dependencies
pip install -r requirements.txt

Configuration
To run this project, you will need to configure the GitHub access token GITHUB_TOKEN for secure access to the GitHub API.

Setting Environment Variables
(1). Linux/macOS
export GITHUB_TOKEN=your_token_here

(2). Windows (PowerShell)
setx GITHUB_TOKEN "your_token_here"


5. Quick Start

(1). Glossary Check

python glossary_check_runner.py --language-codes language-codes.json --exit-on-error

--language-codes (-l): Path to the language codes JSON file (default: language-codes.json).

--exit-on-error: Exit with non-zero status if any validation issues are found (useful for CI integration).


(2). GitHub Analysis

Open the relevant Notebook files in the notebooks/ directory.

Run the data collection, analysis, and visualisation scripts in sequence.

Interactive Plotly charts can be viewed directly within the Notebook.


6. Usage Instructions

(1).Script Execution

All glossary validation logic is contained in glossary_checker.py.

The command-line entry point is glossary_check_runner.py.

(2).Notebook Execution Order

After opening the Jupyter Notebook, the following steps are executed automatically in sequence:

Data collection and processing: retrieving repository activity data via the GitHub API.

Data analysis: calculating statistics and metrics to generate analytical results.

Data visualisation: producing interactive visualisation charts.

Once complete, you can view the interactive dashboard.

