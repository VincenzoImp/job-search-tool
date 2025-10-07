# CLAUDE.md - JobSearch Tool

## Project Overview

This is a generalized, configuration-driven job search tool that scrapes multiple job sites (LinkedIn, Indeed, Glassdoor, Google Jobs) and filters results based on customizable relevance scoring.

**Purpose**: Allow users to automate job searches across multiple sites with personalized relevance scoring
**Technology**: Python 3.11, JobSpy, pandas, PyYAML, Docker
**Architecture**: Configuration-driven with YAML files - no hard-coded search parameters

## Core Principles

1. **Fully Configurable**: All search parameters, queries, locations, and scoring weights defined in YAML
2. **Generic & Reusable**: Works for any job search profile (research, engineering, data science, etc.)
3. **Relevance-Based Filtering**: User-defined keyword categories with custom weights score job matches
4. **Multi-Format Output**: Results saved as CSV and Excel with auto-formatting

## Architecture

### Technology Stack
- **Python 3.11**: Core language (JobSpy requires 3.10+)
- **JobSpy**: Web scraping library for job sites
- **pandas**: Data manipulation and CSV/Excel generation
- **PyYAML**: Configuration file parsing
- **openpyxl**: Excel file generation
- **Docker**: Containerized environment for cross-platform compatibility

### Project Structure

```
jobsearch-tool/
├── config/
│   ├── config.example.yaml     # Template configuration with all options
│   └── config.yaml             # User's configuration (gitignored)
├── scripts/
│   ├── search_jobs.py          # Main job search engine (class-based)
│   └── analyze_jobs.py         # Analysis and reporting tool
├── examples/
│   └── software_engineer_config.yaml  # Example configuration
├── results/                    # Output directory (gitignored)
│   └── .gitkeep
├── Dockerfile                  # Python 3.11 container
├── docker-compose.yml          # Single service orchestration
├── requirements.txt            # Python dependencies
├── .gitignore                  # Excludes config.yaml, results/*
├── LICENSE                     # MIT License
├── README.md                   # User documentation
└── CLAUDE.md                   # This file
```

## Core Components

### 1. Configuration System (config.example.yaml)

**Purpose**: Define all search parameters, queries, and scoring weights without modifying code.

**Sections**:

1. **Profile** (lines 5-18):
   - User's name, email, background summary
   - Career stage and target start date
   - Used for display purposes only

2. **Search Parameters** (lines 20-77):
   - `sites`: Which job sites to search (indeed, linkedin, glassdoor, google)
   - `locations`: Cities/countries to search (e.g., "Berlin, Germany")
   - `queries`: Organized by category (core_areas, technologies, research, industry)
   - `filters`: results_per_query, days_back, job_types, country filters

3. **Relevance Scoring** (lines 79-174):
   - `min_score`: Threshold for filtering jobs
   - `categories`: Keyword groups with weights
     - Each category has a `weight` (importance) and `keywords` list
     - If ANY keyword matches, the category's full weight is added to score
     - Higher weights = more important to user's search

4. **Output Settings** (lines 176-187):
   - results_dir, file formats (csv/xlsx), filename prefix
   - Excel formatting options (auto-adjust columns, freeze headers)

5. **Advanced Settings** (lines 189-206):
   - Deduplication fields, retry logic, rate limiting
   - Logging level, save options

### 2. search_jobs.py (Main Search Engine)

**Purpose**: Execute job searches based on configuration file.

**Class**: `JobSearcher` (lines 20-308)

**Key Methods**:

- `__init__(config_path)` (lines 22-27):
  - Loads YAML configuration
  - Initializes empty job list

- `_load_config(config_path)` (lines 29-43):
  - Loads and validates YAML file
  - Exits if config not found with helpful message

- `_flatten_queries()` (lines 48-57):
  - Converts categorized queries dict to flat list
  - Handles nested query organization

- `search_jobs()` (lines 59-136):
  - **Main search loop**
  - Iterates through locations × queries
  - Calls JobSpy's `scrape_jobs()` with configured parameters
  - Handles errors, retries, rate limiting
  - Returns combined pandas DataFrame

- `calculate_relevance_score(job_text)` (lines 138-153):
  - Scores a single job based on keyword matches
  - Iterates through scoring categories from config
  - Adds weight if ANY keyword from category is found
  - Returns total score

- `filter_relevant_jobs(jobs_df)` (lines 155-173):
  - Applies relevance scoring to all jobs
  - Filters by min_score threshold
  - Sorts by score descending
  - Returns filtered DataFrame

- `save_results(jobs_df, prefix)` (lines 175-211):
  - Saves to CSV and/or Excel based on config
  - Generates timestamped filenames
  - Auto-adjusts Excel column widths if configured
  - Creates results directory if needed

- `run()` (lines 229-249):
  - **Main execution method**
  - Calls search_jobs() → filter_relevant_jobs() → save_results()
  - Saves both all_jobs and relevant_jobs if configured

**Important Parameters**:

- JobSpy `scrape_jobs()` call (lines 83-94):
  ```python
  scrape_jobs(
      site_name=["indeed", "linkedin", "glassdoor", "google"],
      search_term=query,
      location=location,
      results_wanted=50,
      hours_old=720,  # days_back * 24
      country_indeed='Switzerland',
      linkedin_fetch_description=True,
      job_type="fulltime"  # if single type specified
  )
  ```
  - **Note**: `is_remote` parameter is NOT used (causes validation error in JobSpy 1.1.82+)

### 3. analyze_jobs.py (Analysis Tool)

**Purpose**: Analyze saved job search results and generate insights.

**Class**: `JobAnalyzer` (lines 16-240)

**Key Methods**:

- `load_latest_results(prefix)` (lines 23-38):
  - Finds most recent CSV file in results directory
  - Prefers relevant_jobs_*.csv over all_jobs_*.csv

- `analyze_companies(df, top_n)` (lines 40-46):
  - Returns top N companies by job count

- `analyze_locations(df, top_n)` (lines 48-54):
  - Returns top N locations by job count

- `analyze_keywords(df, top_n)` (lines 56-79):
  - Extracts keywords from job titles
  - Filters stop words
  - Returns top N most common keywords

- `analyze_salary(df)` (lines 81-102):
  - Calculates average/median salaries if available
  - Groups by currency

- `generate_report(df)` (lines 119-189):
  - Comprehensive report including:
    - Overview (total jobs, average score, recent postings)
    - Top companies and locations
    - Common keywords
    - Job type distribution
    - Remote vs on-site breakdown
    - Salary statistics

- `export_filtered_by_company(df, companies)` (lines 191-205):
  - Filters jobs by specific company names
  - Exports to CSV

- `export_top_scoring_jobs(df, top_n)` (lines 207-217):
  - Exports top N jobs by relevance score

### 4. Docker Configuration

**Dockerfile**:
- Base: `python:3.11-slim`
- Installs: python-jobspy, pandas, openpyxl, pyyaml, matplotlib, seaborn
- Copies: scripts/, config/ directories
- Creates: /app/results directory
- Working dir: /app/scripts
- Default command: `python search_jobs.py`

**docker-compose.yml**:
- Service: `jobsearch`
- Volume mounts:
  - `./results:/app/results` (persists output)
  - `./scripts:/app/scripts` (live code editing)
  - `./config:/app/config` (configuration access)
- Environment: `PYTHONUNBUFFERED=1`

## Common Workflows

### Setting Up for First Use

```bash
# Clone repository
git clone https://github.com/VincenzoImp/jobsearch-tool.git
cd jobsearch-tool

# Copy and customize configuration
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your profile, locations, queries, scoring

# Run with Docker (recommended)
docker compose up --build

# OR with local Python (requires 3.10+)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd scripts
python search_jobs.py
```

### Running with Custom Configuration

```bash
# Use custom config file
python search_jobs.py ../config/my_custom_config.yaml

# Analyze results
python analyze_jobs.py ../config/my_custom_config.yaml
```

### Customization Workflow

1. **Define Your Profile** (config.yaml):
   - Edit profile section with your name, career stage, background

2. **Set Locations**:
   - Add cities/countries you want to work in
   - Format: "City, Country" (e.g., "Berlin, Germany")

3. **Create Search Queries**:
   - Organize by category (backend, frontend, research, etc.)
   - Start broad, refine based on results
   - 20-40 queries recommended (more = longer search time)

4. **Configure Relevance Scoring**:
   - Identify must-have skills/keywords (weight: 18-25)
   - Add nice-to-have skills (weight: 10-15)
   - Include preferences (weight: 5-10)
   - Set min_score threshold (10-15 recommended)

5. **Run and Iterate**:
   - Run search, review results
   - Adjust weights based on what scores high/low
   - Add/remove queries as needed

## Configuration Best Practices

### Query Organization

```yaml
search:
  queries:
    # Group by role type
    backend:
      - "backend engineer"
      - "backend developer"
      - "API engineer"

    # Group by technology
    python:
      - "Python developer"
      - "Python engineer"

    # Group by seniority
    senior:
      - "senior engineer"
      - "lead engineer"
```

### Relevance Scoring Strategy

**High Weight (18-25)**: Must-have skills
```yaml
primary_skills:
  weight: 20
  keywords:
    - "distributed systems"
    - "Python"
    - "backend"
```

**Medium Weight (10-17)**: Important but flexible
```yaml
secondary_skills:
  weight: 12
  keywords:
    - "Docker"
    - "Kubernetes"
    - "AWS"
```

**Low Weight (5-9)**: Nice-to-have preferences
```yaml
preferences:
  weight: 6
  keywords:
    - "remote"
    - "startup"
    - "open source"
```

**Formula**: Job gets category's full weight if ANY keyword matches (not additive per keyword)

### Performance Optimization

**For Faster Searches**:
- Reduce number of queries (20-30 instead of 40+)
- Limit locations (3-5 key cities)
- Lower `results_per_query` (20-30 instead of 50)
- Increase `rate_limit_delay` if hitting rate limits

**For Better Results**:
- Start with broad queries, refine based on initial results
- Tune weights after reviewing first search
- Increase `min_score` to filter more aggressively
- Use `export_top_scoring_jobs()` in analyze script

## Troubleshooting Guide

### JobSpy API Issues

**Problem**: `validation error for ScraperInput: is_remote`
**Cause**: JobSpy 1.1.82+ doesn't accept `is_remote=None`
**Solution**: Remove `is_remote` parameter from `scrape_jobs()` call (already done in v1.0)

**Problem**: Glassdoor returns 400 errors
**Cause**: Glassdoor API frequently rejects requests
**Solution**: This is normal - other sites (LinkedIn, Indeed, Google) will still work

### Rate Limiting

**Symptoms**: Empty results after several successful queries
**Solutions**:
1. Reduce `results_per_query` from 50 to 20-30
2. Increase `rate_limit_delay` to 2-3 seconds
3. Reduce number of total queries
4. Wait a few hours before re-running

### No Jobs Found

**Check**:
1. Are queries too specific? Try broader terms
2. Location format correct? Use "City, Country"
3. `days_back` too narrow? Try 60-90 days
4. Network issues? Check internet connection

### Python Version Issues

**Error**: `Could not find a version that satisfies the requirement python-jobspy`
**Cause**: JobSpy requires Python 3.10+
**Solution**: Use Docker OR upgrade Python:
```bash
# Check version
python3 --version

# Install Python 3.11 (macOS)
brew install python@3.11

# Use in venv
python3.11 -m venv venv
```

## Output Schema

### CSV/Excel Columns (from JobSpy)

```
title               - Job title
company             - Company name
location            - Job location
description         - Full job description (if fetched)
job_url             - Link to original posting
date_posted         - When job was posted
job_type            - fulltime, parttime, contract, internship
is_remote           - Boolean: remote work available
min_amount          - Minimum salary (if available)
max_amount          - Maximum salary (if available)
currency            - Salary currency (CHF, EUR, USD, etc.)
interval            - yearly, monthly, hourly
search_query        - Query that found this job (added by tool)
search_location     - Location searched (added by tool)
relevance_score     - Calculated score (added by filter_relevant_jobs)
```

## Extending the Tool

### Adding Custom Analysis

```python
# In analyze_jobs.py, add new method to JobAnalyzer class:

def analyze_tech_stack(self, df: pd.DataFrame) -> Counter:
    """Analyze most common technologies mentioned."""
    tech_keywords = ['python', 'javascript', 'go', 'rust', 'java',
                     'react', 'vue', 'angular', 'docker', 'kubernetes']

    all_text = ' '.join(df['description'].fillna('').astype(str)).lower()

    tech_counts = Counter()
    for tech in tech_keywords:
        tech_counts[tech] = all_text.count(tech)

    return tech_counts.most_common(10)
```

### Adding Custom Filters

```python
# After loading results in analyze_jobs.py:

def export_by_criteria(self, df: pd.DataFrame,
                       min_score: int = 20,
                       locations: List[str] = None,
                       companies: List[str] = None):
    """Export jobs matching multiple criteria."""
    filtered = df[df['relevance_score'] >= min_score]

    if locations:
        filtered = filtered[filtered['location'].isin(locations)]

    if companies:
        filtered = filtered[filtered['company'].isin(companies)]

    filtered.to_csv('../results/custom_filtered.csv', index=False)
    return filtered
```

## Important Notes

### JobSpy Limitations
- Rate limiting: Don't run excessive searches
- Some sites block scrapers: Results may vary
- Glassdoor frequently returns errors: Expected behavior
- Description fetching: Not always available

### Configuration Guidelines
- Keep `config.yaml` out of git if it contains personal info
- Use `config.example.yaml` as template
- Version control your custom configs separately if needed

### Performance Considerations
- 40 queries × 6 locations × 50 results = 12,000+ potential jobs
- Deduplication typically reduces this by 30-50%
- Full search can take 10-30 minutes depending on rate limits
- Consider running searches during off-peak hours

## Future Enhancements

**Potential Additions** (not yet implemented):
1. Negative keyword scoring (penalize jobs with certain terms)
2. Company whitelist/blacklist
3. Scheduled searches with cron integration
4. Email notifications for new high-scoring jobs
5. Machine learning-based relevance prediction
6. Multi-user configuration management
7. Web UI for configuration and results viewing

## Contributing Guidelines

When modifying the tool:

1. **Maintain Configuration-Driven Design**:
   - Never hard-code search parameters
   - Add new features via config options
   - Preserve backward compatibility with existing configs

2. **Update Documentation**:
   - Update CLAUDE.md for code changes
   - Update README.md for user-facing changes
   - Update config.example.yaml with new options

3. **Test with Multiple Configs**:
   - Test with different profiles (research, engineering, etc.)
   - Verify both Docker and local Python execution
   - Check both CSV and Excel output formats

4. **Follow Code Style**:
   - Use type hints where appropriate
   - Document classes and methods with docstrings
   - Keep methods focused and single-purpose

## Contact & Support

**Repository**: https://github.com/VincenzoImp/jobsearch-tool
**Issues**: https://github.com/VincenzoImp/jobsearch-tool/issues
**License**: MIT

**For JobSpy Issues**: https://github.com/speedyapply/JobSpy/issues

---

**Last Updated**: 2025-10-07
**Version**: 1.0.0
**Claude Instance**: Use this document to understand the project architecture and assist with modifications or extensions.
