# glosario-dashboard


## 1. Glosario Context

Glosario is an open-source, multilingual glossary of data science terms developed by The Carpentries community. It provides standardised definitions to improve clarity and consistency in educational materials.

It is maintained as a structured glossary.yml file and designed for integration with R and Python workflows. It is widely used in educational metadata to ensure consistent terminology across open learning resources.


## 2. Glosario Context & GitHub Analytics Toolkit

A Python-based toolkit for validating multilingual glossary quality and analyzing GitHub repository activity, with CI automation and interactive dashboards.

### 2.1 Overview

This project provides a dual-purpose analytics system for open-source repositories:

### 2.2 Glossary Quality Assessment System

Automated multi-dimensional glossary validation with CI-integrated checks via GitHub Actions.

- Core validation is implemented in Python scripts
- Interactive exploration and debugging are supported through Jupyter Notebooks
- The Streamlit interface provides an interactive dashboard for quality inspection
- A CI runner script (`glossary_check_runner.py`) enables local execution of automated checks and outputs results as JSON for further analysis or CI integration  

### 2.3 GitHub Repository Activity Analysis

Repository activity visualisation and contributor behaviour analysis for open-source projects.

- Core data processing and analysis are implemented in Python scripts
- Interactive visualisation dashboards are provided via Jupyter Notebooks
- Analysis covers commits, pull requests, and issues to track project evolution
- Outputs include contributor metrics and repository activity trends

### 2.4 Output

The system supports reproducible analytics workflows for automated quality validation and repository activity analysis, enabling both documentation quality improvement and insight into contributor behaviour and project evolution.


##  3. Key Features

### 3.1 Glossary Quality Assessment

Automated validation of glossary structure, format compliance, consistency, and data integrity.

Key checks and insights include:

- Slug and multi-language entry ordering rules  
- Completeness and structural validity of glossary entries  
- Format compliance with YAML structure and field requirements  
- Reference validation and consistency of links across language definitions
- Severity classification (info, warning, error, exception)  
- Structured reporting by entry and language  
- CI integration via GitHub Actions  
- Local and CI-compatible execution   
- Interactive quality inspection via Streamlit and Jupyter dashboards  

### 3.2 GitHub Activity Analysis

Repository-wide analysis of contributor behaviour and project evolution, presented through multiple visualisations and tables.

Key insights include:

- Contributor activity, ranking, and engagement analysis  
- Contributor retention and behavioural pattern analysis  
- Commit, pull request, and issue lifecycle tracking  
- Repository collaboration and participation patterns  
- Temporal trends in repository activity (commits, pull requests, issues)  
- Codebase contribution analysis by programming language and file type  
- README content and repository metadata consistency validation


## 4. Project Structure
```text
.
├── .env
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE

├── GitHub_Activity_Visualisation/
│   ├── analysis.py
│   ├── cache.py
│   ├── config.py
│   ├── data_fetch.py
│   ├── github_client.py
│   ├── language-codes.json
│   ├── main.py
│   ├── preprocess.py
│   ├── repo_activity_dashboard.ipynb
│   ├── utils.py
│   └── visualisation.py

├── Quality_Assessment/
│   ├── app.py
│   ├── glossary_checker.ipynb
│   ├── glossary_checker.py
│   ├── glossary_check_runner.py
│   └── language-codes.json

└── .github/
    └── workflows/
        └── glossary_check.yml
```

## 5. Installation 

### 5.1 System Requirements
- Python 3.8 or later
- Jupyter Notebook

### 5.2 Installing Dependencies

```bash
pip install -r requirements.txt
```

### 5.3 Environment setup

- A `.env` file has already been created in the project root directory.

- Add your GitHub Personal Access Token as follows:

```bash
   GITHUB_TOKEN=your_github_token_here
```

- This token is required to access the GitHub API and retrieve repository data.


## 6. Quick Start

### 6.1 Glossary Check

#### Notebook
- Open the Jupyter notebook：
  `Quality_Assessment/glossary_checker.ipynb`

#### Local execution
```bash
python glossary_check_runner.py 
```
##### CI execution
- This same command is executed automatically in GitHub Actions on push and pull requests, generating validation reports as artifacts.

### 6.2 GitHub Activity Analysis

#### Notebook
- Open the Jupyter notebook：
   `GitHub_Activity_Visualisation/repo_activity_dashboard.ipynb`

- Run all cells sequentially to perform analysis:

  - Data collection (GitHub API)
  - Data preprocessing
  - Metric computation
  - Visualisation dashboards

### 6.3 CI Integration

This project uses GitHub Actions for automated glossary validation.

#### Workflow file:

- Configuration file:
`.github/workflows/glossary_check.yml`

#### Trigger Conditions

The CI pipeline is triggered on:

- Push events to main and develop branches
- Pull request events targeting the main branch

#### CI Workflow Overview

- The CI pipeline performs automated glossary validation and report generation.

#### CI Execution

- In GitHub Actions, the following command is executed automatically:
  ```bash
  python glossary_check_runner.py
  ```
- This step runs the glossary validation process and generates the output report.

#### CI Outputs

The CI produces:
- A JSON report file: report.json
- A GitHub Actions artifact: glossary-report
