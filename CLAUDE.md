# CLAUDE.md - Switzerland Jobs Search Tool

## Project Overview

This is an automated job search tool using JobSpy to find positions in Switzerland matching Vincenzo Imperati's profile as a PhD researcher in distributed systems, blockchain, and social network analysis.

**Owner**: Vincenzo Imperati (vincenzo@imperati.dev)
**Profile**: PhD candidate at Sapienza University (Nov 2023 - Oct 2026), Visiting PhD at ETH Zurich (Sep 2025 - Oct 2026)
**Research**: User behavior analysis in distributed systems & blockchains, published at USENIX Security
**Grant**: OpenSats grant recipient for Nostr protocol development (Bigbrotr, nostr-tools)

## Architecture

### Technology Stack
- **Python 3.11**: Core language (JobSpy requires 3.10+)
- **JobSpy**: Web scraping library for job sites (LinkedIn, Indeed, Glassdoor, Google Jobs)
- **Pandas**: Data manipulation and analysis
- **OpenPyXL**: Excel file generation
- **Matplotlib/Seaborn**: Data visualization for analysis
- **Docker**: Containerized environment for cross-platform compatibility

### Project Structure

```
switzerland-jobs-search/
├── scripts/
│   ├── search_jobs.py      # Main job search engine with CV-specific queries
│   └── analyze_jobs.py     # Post-search analysis and reporting tool
├── results/                # Generated CSV/Excel files (gitignored)
│   └── .gitkeep
├── config/                 # Configuration files (if needed)
├── cv.pdf                  # Vincenzo's CV (reference for customization)
├── Dockerfile             # Python 3.11 container
├── docker-compose.yml     # Single service orchestration
├── requirements.txt       # Python dependencies
├── .gitignore            # Excludes results/*.csv, results/*.xlsx
├── LICENSE               # MIT License
└── README.md             # User documentation
```

## Core Components

### 1. search_jobs.py (Main Script)

**Purpose**: Searches for jobs across multiple sites and locations, filters by relevance, and exports results.

**Key Functions**:

- `search_switzerland_jobs()` (lines 12-139)
  - Executes 40+ CV-specific search queries across 6 Swiss locations
  - Searches: indeed, linkedin, glassdoor, google
  - Parameters: 50 results per query, last 30 days (hours_old=720), fulltime positions
  - Returns deduplicated DataFrame

- `filter_relevant_jobs()` (lines 142-250)
  - Calculates relevance scores based on 8 keyword categories
  - Returns jobs with score > 10

- `calculate_relevance_score()` (lines 175-239)
  - **Scoring weights** (customized for Vincenzo's profile):
    - Blockchain & distributed systems: +20
    - PhD/research positions: +18
    - Data analysis & user behavior: +15
    - Summer 2026 programs: +15
    - Security & privacy (ZK, crypto): +12
    - Academic institutions (ETH/EPFL): +12
    - ETH Zurich specifically: +10
    - Social network analysis: +10
    - Technical stack (Python/TypeScript/React): +8
    - Open source development: +8
    - Teaching positions: +6
    - Computer Science: +5
    - Zurich/Lausanne location: +5
    - Hackathon/competition: +5

- `save_results()` (lines 253-284)
  - Saves to both CSV and Excel with timestamp
  - Excel includes auto-adjusted column widths
  - Output format: `{prefix}_{YYYYMMDD_HHMMSS}.{csv|xlsx}`

**Search Queries** (lines 19-76):
- 40+ queries organized in 8 categories:
  1. Core Research Areas: distributed systems, blockchain, network analysis, social networks, user behavior
  2. Blockchain & Web3: engineer, web3, smart contracts, cryptocurrency, Nostr, decentralized systems
  3. PhD & Research: PhD researcher, postdoc, research scientist, visiting researcher
  4. Data Science: data scientist/analyst/engineer, behavioral analytics, network data analysis
  5. Software Engineering: backend Python, full-stack TypeScript, blockchain engineer, open source
  6. Security & Privacy: security researcher, privacy engineer, cryptography, zero-knowledge proofs
  7. Academic & Teaching: teaching assistant, university lecturer, research associate
  8. Technologies: Python, React, Node.js, PostgreSQL, Docker
  9. Summer/Temporary: summer internship 2026, research internship, temporary researcher

**Locations Searched** (lines 79-86):
- Zurich, Switzerland (primary focus)
- Lausanne, Switzerland (EPFL)
- Geneva, Switzerland
- Bern, Switzerland
- Basel, Switzerland
- Switzerland (general)

### 2. analyze_jobs.py (Analysis Tool)

**Purpose**: Analyzes saved job search results and generates insights.

**Key Functions**:

- `load_latest_results()` (lines 15-39)
  - Loads most recent CSV file from results/ directory
  - Prefers relevant_jobs_*.csv over all_jobs_*.csv

- `analyze_companies()` (lines 42-53)
  - Top 15 companies by job count

- `analyze_locations()` (lines 56-67)
  - Top 10 locations by job count

- `analyze_keywords()` (lines 70-93)
  - Extracts top 20 keywords from job titles
  - Filters common stop words

- `analyze_salary()` (lines 96-118)
  - Salary statistics if available (min/max amounts, currencies)

- `generate_report()` (lines 121-163)
  - Comprehensive report including:
    - Total jobs, average relevance score
    - Company/location/keyword breakdowns
    - Job types (fulltime/contract/internship)
    - Remote vs on-site distribution

- `export_filtered_by_company()` (lines 165-179)
  - Filters jobs by specific companies (currently commented out)
  - Usage example in main() lines 194-195

### 3. Docker Configuration

**Dockerfile**:
- Base image: `python:3.11-slim`
- Installs: python-jobspy, pandas, openpyxl, matplotlib, seaborn
- Creates /app/results directory
- Working directory: /app/scripts
- Default command: `python search_jobs.py`

**docker-compose.yml**:
- Single service: `jobsearch`
- Volume mounts:
  - `./results:/app/results` (persists output)
  - `./scripts:/app/scripts` (live script editing)
  - `./config:/app/config` (configuration files)
- Environment: `PYTHONUNBUFFERED=1` (immediate output)

## Common Commands

### Run Job Search

**Using Docker** (recommended):
```bash
# Build and run (first time)
docker-compose up --build

# Subsequent runs
docker-compose up

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f
```

**Using Local Python** (requires 3.10+):
```bash
# Install dependencies
pip install -r requirements.txt

# Run search
cd scripts
python search_jobs.py

# Analyze results
python analyze_jobs.py
```

### Analyze Results

```bash
# Using Docker
docker-compose run jobsearch python analyze_jobs.py

# Using local Python
cd scripts
python analyze_jobs.py
```

### View Results

```bash
# List all result files
ls -lth results/

# View latest CSV
cat results/relevant_jobs_*.csv | tail -n 20

# Open Excel file (Mac)
open results/relevant_jobs_*.xlsx
```

## Output Files

All files saved to `results/` directory with timestamp format `YYYYMMDD_HHMMSS`:

- `all_jobs_{timestamp}.csv` - All jobs found (before filtering)
- `all_jobs_{timestamp}.xlsx` - Excel version with formatting
- `relevant_jobs_{timestamp}.csv` - Jobs with relevance score > 10
- `relevant_jobs_{timestamp}.xlsx` - Excel version
- `filtered_by_company.csv` - Optional company-filtered results (if using analyze_jobs.py filter)

## Customization Guide

### Modify Search Queries

Edit `scripts/search_jobs.py` lines 19-76:

```python
search_queries = [
    "your new query",
    "another query",
]
```

**Tip**: Current queries are highly specific to Vincenzo's CV. Keep blockchain, distributed systems, and research focus.

### Adjust Relevance Scoring

Edit `calculate_relevance_score()` function (lines 175-239):

```python
# Example: Increase blockchain weight
if any(keyword in text for keyword in blockchain_keywords):
    score += 25  # Changed from 20

# Example: Add new keyword category
nostr_keywords = ['nostr', 'nip', 'relay', 'zap']
if any(keyword in text for keyword in nostr_keywords):
    score += 15
```

### Change Search Parameters

Edit `scrape_jobs()` call in search_jobs.py (lines 97-108):

```python
jobs = scrape_jobs(
    site_name=["indeed", "linkedin", "glassdoor", "google"],
    search_term=query,
    location=location,
    results_wanted=50,      # Increase for more results (may hit rate limits)
    hours_old=720,          # 720 = 30 days, 168 = 7 days
    job_type="fulltime",    # Options: fulltime, parttime, internship, contract
    is_remote=None,         # True = remote only, False = on-site only, None = both
)
```

### Filter by Specific Companies

Edit `analyze_jobs.py` lines 194-195:

```python
# Uncomment and customize:
target_companies = ['ETH Zurich', 'EPFL', 'Google Research', 'IBM Research']
export_filtered_by_company(df, target_companies)
```

### Add New Locations

Edit `scripts/search_jobs.py` lines 79-86:

```python
locations = [
    "Zurich, Switzerland",
    "Lausanne, Switzerland",
    # Add new locations:
    "Lugano, Switzerland",
    "St. Gallen, Switzerland",
]
```

## Troubleshooting

### Issue: JobSpy Installation Fails (Python version)

**Error**: `ERROR: Could not find a version that satisfies the requirement python-jobspy`

**Cause**: JobSpy requires Python 3.10+

**Solution**: Use Docker instead of local Python:
```bash
docker-compose up --build
```

### Issue: No Jobs Found

**Possible causes**:
1. **Rate limiting**: Job sites may be blocking requests
   - Solution: Reduce `results_wanted` from 50 to 20
   - Wait a few hours before re-running

2. **Network issues**: Check internet connection

3. **Query too specific**: Broaden search queries

4. **Time range too narrow**: Increase `hours_old` parameter (e.g., 1440 for 60 days)

### Issue: Docker Build Fails

```bash
# Clear Docker cache and rebuild
docker-compose down
docker system prune -f
docker-compose up --build
```

### Issue: Permission Denied on results/ Directory

```bash
# Fix permissions
chmod 755 results/
```

### Issue: Excel File Won't Open

**Error**: Corrupted Excel file

**Solution**: Use CSV files instead, or check openpyxl version:
```bash
pip install --upgrade openpyxl
```

### Issue: Search Taking Too Long

**Causes**:
- 40+ queries × 6 locations = 240+ searches
- Each search requests 50 results

**Solutions**:
1. Reduce number of queries (comment out less relevant ones)
2. Reduce locations (focus on Zurich only)
3. Reduce `results_wanted` to 20
4. Run searches in batches

```python
# Example: Zurich-only search
locations = [
    "Zurich, Switzerland",
    # "Lausanne, Switzerland",  # Commented out
]
```

## Important Notes

### Rate Limiting
- JobSpy scrapes public job sites and may hit rate limits
- Symptoms: Errors after several successful queries, empty results
- Solutions:
  - Run at different times of day
  - Reduce `results_wanted` parameter
  - Add delays between searches (modify code)

### Python Version Requirements
- **Minimum**: Python 3.10
- **Recommended**: Python 3.11+ (as used in Docker)
- **Check version**: `python3 --version`
- **If version < 3.10**: Must use Docker

### Results Freshness
- Default: Last 30 days (`hours_old=720`)
- Modify for different ranges:
  - 7 days: `hours_old=168`
  - 60 days: `hours_old=1440`
  - 90 days: `hours_old=2160`

### Duplicate Removal
- Automatically removes duplicates based on: title + company + location
- Keeps first occurrence encountered

### Data Privacy
- `cv.pdf` is committed to repository (be aware if making repo public)
- Results files are gitignored for privacy

## CV-Specific Customization Notes

This tool is **highly customized** for Vincenzo Imperati's profile:

**Research Focus**:
- Distributed systems & blockchain (+20 relevance score)
- Social network analysis (+10, specifically Telegram research)
- User behavior analysis (+15)
- Nostr protocol (OpenSats grant project)

**Career Stage**:
- Currently visiting ETH Zurich (Sep 2025 - Oct 2026)
- Graduating Oct 2026 → Summer 2026 programs prioritized (+15)
- PhD positions & postdoc roles (+18)

**Technical Skills**:
- Python, TypeScript, C++, React, Node.js (+8)
- PostgreSQL, MongoDB, Docker
- Blockchain development (Solidity)

**Academic Credentials**:
- USENIX Security publication (top-tier security conference)
- Outstanding University Student 2025 award
- Teaching experience (3 fellowships) → teaching positions (+6)
- Hackathon team lead (10 prizes) → competition roles (+5)

**If adapting for another user**: Modify:
1. `search_queries` list (lines 19-76)
2. `calculate_relevance_score()` weights (lines 175-239)
3. Profile banner in `main()` (lines 290-303)
4. README.md profile section

## Workflow for Regular Job Search

### Weekly Search Routine

```bash
# 1. Run search (Friday mornings recommended)
cd /Users/vincenzo/Documents/GitHub/switzerland-jobs-search
docker-compose up

# 2. Analyze results
docker-compose run jobsearch python analyze_jobs.py

# 3. Review top matches
open results/relevant_jobs_*.xlsx

# 4. Optional: Archive old results
mkdir -p results/archive
mv results/*_2025*.csv results/archive/  # Example for archiving
```

### Automated Scheduling (Optional)

**Using cron (Mac/Linux)**:
```bash
# Edit crontab
crontab -e

# Add weekly job search (every Friday at 9 AM)
0 9 * * 5 cd /Users/vincenzo/Documents/GitHub/switzerland-jobs-search && docker-compose up
```

**Using launchd (Mac)**:
Create `~/Library/LaunchAgents/com.vincenzo.jobsearch.plist`

## Git Workflow

```bash
# Check status
git status

# Commit code changes (not results)
git add scripts/ Dockerfile docker-compose.yml
git commit -m "Update search queries for new research focus"

# Push to GitHub
git push origin main

# Pull updates
git pull origin main
```

**Note**: `results/` directory is gitignored. Job search outputs stay local.

## Performance Tips

### Optimize Search Time
1. **Parallel execution**: JobSpy runs searches sequentially. Consider modifying code to parallelize.
2. **Caching**: Store previously seen job IDs to avoid re-processing
3. **Targeted searches**: Focus on high-value queries (blockchain, research positions)

### Reduce False Positives
1. **Negative keywords**: Modify relevance scoring to penalize irrelevant terms
2. **Company whitelist**: Focus on academic institutions and blockchain companies
3. **Increase score threshold**: Change `jobs_df['relevance_score'] > 10` to `> 15`

### Improve Relevance Scoring
```python
# Example: Penalize non-research roles for PhD focus
if 'sales' in text or 'marketing' in text:
    score -= 10

# Example: Boost ETH/EPFL even more
if 'eth zurich' in text or 'eth zürich' in text:
    score += 20  # Increased from 10
```

## External Dependencies

### JobSpy Library
- **GitHub**: https://github.com/speedyapply/JobSpy
- **Documentation**: https://github.com/speedyapply/JobSpy#readme
- **Version**: >=1.1.80 (see requirements.txt)
- **Capabilities**:
  - Scrapes: LinkedIn, Indeed, Glassdoor, Google Jobs
  - Supports: Filters by job type, remote status, date range
  - Returns: Pandas DataFrame with standardized schema

### Pandas DataFrame Schema (JobSpy Output)
```python
columns = [
    'title',           # Job title
    'company',         # Company name
    'location',        # Job location
    'description',     # Full job description (if available)
    'job_url',         # Link to job posting
    'date_posted',     # When job was posted
    'job_type',        # fulltime, parttime, contract, internship
    'is_remote',       # Boolean: remote work available
    'min_amount',      # Minimum salary (if available)
    'max_amount',      # Maximum salary (if available)
    'currency',        # Salary currency (CHF, EUR, USD)
    'interval',        # Salary interval (yearly, monthly)
]
```

## Contact & Support

**Repository Owner**: Vincenzo Imperati
**Email**: vincenzo@imperati.dev
**GitHub**: https://github.com/VincenzoImp/switzerland-jobs-search (private)

**For JobSpy issues**: https://github.com/speedyapply/JobSpy/issues

## License

MIT License - See LICENSE file for details.

---

**Last Updated**: 2025-10-07
**Claude Instance**: Use this document to understand the project structure and assist with modifications.
