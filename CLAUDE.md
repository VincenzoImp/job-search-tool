# CLAUDE.md - JobSpy Dashboard

## Project Overview

This is an automated job search and analysis tool using JobSpy to aggregate positions from multiple job boards. It features parallel execution, relevance scoring, SQLite persistence, and an interactive Streamlit dashboard.

The tool is **highly customizable** through YAML configuration - no code changes needed to customize for different profiles, locations, or job types.

## Architecture

### Technology Stack

- **Python 3.11**: Core language (JobSpy requires 3.10+)
- **JobSpy v1.1.82**: Web scraping library for job sites (LinkedIn, Indeed, Glassdoor, Google Jobs, etc.)
- **Pandas**: Data manipulation and analysis
- **OpenPyXL**: Excel file generation with formatting
- **Streamlit**: Interactive dashboard with caching
- **PyYAML**: YAML configuration parsing
- **Tenacity**: Retry logic with exponential backoff
- **SQLite**: Job persistence and tracking across runs
- **Docker**: Containerized environment for cross-platform compatibility

### Project Structure

```
jobspy-dashboard/
├── config/
│   ├── settings.yaml          # User configuration (gitignored)
│   └── settings.example.yaml  # Example template with full documentation
├── scripts/
│   ├── search_jobs.py         # Main job search with parallel execution
│   ├── analyze_jobs.py        # Post-search analysis and reporting
│   ├── dashboard.py           # Streamlit interactive dashboard
│   ├── config.py              # Configuration loader with validation
│   ├── logger.py              # Structured logging with rotation
│   ├── database.py            # SQLite persistence for job tracking
│   └── models.py              # Type-safe dataclasses
├── results/                    # Generated CSV/Excel files (gitignored)
├── data/                       # SQLite database (gitignored)
├── logs/                       # Log files with rotation (gitignored)
├── Dockerfile                  # Python 3.11 container
├── docker-compose.yml          # Service orchestration with profiles
├── requirements.txt            # Python dependencies
├── .dockerignore               # Docker build optimization
├── .gitignore                  # Git exclusions
├── LICENSE                     # MIT License
├── README.md                   # User documentation
└── CLAUDE.md                   # Developer documentation (this file)
```

## Core Components

### 1. config/settings.yaml

Central configuration file containing all customizable settings with extensive documentation:

- **search**: results_wanted, hours_old, job_types, sites, locations, distance, is_remote, etc.
- **queries**: Organized by category (software_engineering, data, etc.)
- **scoring**: threshold, weights, keywords for relevance calculation
- **parallel**: max_workers for concurrent execution
- **retry**: max_attempts, base_delay, backoff_factor
- **logging**: level, file path, rotation settings
- **output**: results_dir, data_dir, database_file
- **profile**: User information for display

See `config/settings.example.yaml` for full parameter documentation.

### 2. scripts/config.py

Configuration loader with type-safe dataclasses:

**Key Classes**:
- `SearchConfig`: Search parameters (results_wanted, hours_old, etc.)
- `ScoringConfig`: Relevance scoring weights and keywords
- `ParallelConfig`: Concurrency settings (max_workers)
- `RetryConfig`: Retry logic parameters
- `LoggingConfig`: Logging configuration
- `OutputConfig`: File paths
- `ProfileConfig`: User profile information
- `Config`: Main configuration class combining all above

**Key Functions**:
- `load_config()`: Load from YAML with fallback to defaults
- `get_config()`: Get singleton configuration instance
- `reload_config()`: Force reload from file

**Properties**:
- `config.results_path`: Absolute path to results directory
- `config.data_path`: Absolute path to data directory
- `config.database_path`: Absolute path to SQLite database
- `config.log_path`: Absolute path to log file
- `config.get_all_queries()`: Flattened list of all search queries

### 3. scripts/logger.py

Structured logging with console colors and file rotation:

**Key Components**:
- `ColoredFormatter`: ANSI colors for console output
- `PlainFormatter`: Plain text for file output
- `ProgressLogger`: Track progress with counts and percentages

**Key Functions**:
- `setup_logging(config)`: Initialize logging handlers
- `get_logger(name)`: Get logger instance
- `log_section(logger, title)`: Log section header
- `log_subsection(logger, title)`: Log subsection header

### 4. scripts/models.py

Type-safe dataclasses for data structures:

**Key Classes**:
- `Job`: Single job listing with all fields
  - `job_id` property: SHA256 hash of title+company+location
  - `from_dict()`: Create from DataFrame row
  - `to_dict()`: Convert to dictionary
- `SearchResult`: Results from a single query
- `SearchSummary`: Statistics for complete search run
- `JobDBRecord`: Database record for persistence (with all columns)

### 5. scripts/database.py

SQLite database for job persistence with full job details:

**Schema** (updated with all columns):
```sql
CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT NOT NULL,
    job_url TEXT,
    site TEXT,
    job_type TEXT,
    is_remote BOOLEAN,
    job_level TEXT,
    description TEXT,
    date_posted DATE,
    min_amount REAL,
    max_amount REAL,
    currency TEXT,
    company_url TEXT,
    first_seen DATE NOT NULL,
    last_seen DATE NOT NULL,
    relevance_score INTEGER DEFAULT 0,
    applied BOOLEAN DEFAULT FALSE
)
```

**Automatic Migration**: When opening an existing database, new columns are automatically added using `ALTER TABLE` statements.

**Key Methods**:
- `save_job(job, site, job_level, company_url)`: Insert or update job with full details
- `save_jobs_from_dataframe(df)`: Save from DataFrame with all columns
- `get_new_job_ids(job_ids)`: Identify which jobs are new
- `filter_new_jobs(df)`: Filter DataFrame to only new jobs
- `get_all_jobs()`: Get all jobs from database
- `mark_as_applied(job_id)`: Mark job as applied
- `get_statistics()`: Get database statistics
- `export_to_dataframe()`: Export all jobs with full details

**Update Logic**: On conflict (same job_id), updates:
- `last_seen` to today
- `relevance_score` only if new score is higher
- All other fields use COALESCE (keep existing if new is NULL)

### 6. scripts/search_jobs.py

Main job search with parallel execution:

**Key Functions**:

- `calculate_relevance_score(row, config)`: Calculate score based on keywords
  - Uses weights and keywords from config
  - Returns integer score

- `search_single_query(query, location, config)`: Execute one search
  - Retry logic with exponential backoff via tenacity
  - Returns (query, location, df, error)

- `search_jobs(config)`: Main parallel search
  - Uses ThreadPoolExecutor with configurable workers
  - Incremental deduplication during collection
  - Returns (combined_df, SearchSummary)

- `filter_relevant_jobs(df, config)`: Filter by score threshold
  - Calculates scores for all jobs
  - Returns filtered, sorted DataFrame

- `save_results(df, config, prefix)`: Save to CSV and Excel
  - Excel formatting: colored headers, hyperlinks, freeze panes
  - Conditional formatting for high scores

- `main()`: Entry point
  - Loads config, sets up logging
  - Runs search, saves results
  - Updates database with full job details, prints summary

### 7. scripts/analyze_jobs.py

Results analysis and reporting:

**Key Functions**:
- `load_latest_results(config)`: Load most recent CSV file
- `analyze_companies(df)`: Top 15 companies by job count
- `analyze_locations(df)`: Top 10 locations
- `analyze_keywords(df)`: Top 20 keywords in titles
- `analyze_salary(df)`: Salary statistics if available
- `analyze_job_types(df)`: Job type distribution
- `analyze_remote(df)`: Remote vs on-site
- `generate_report(df, config)`: Comprehensive report
- `analyze_database(config)`: Database statistics
- `export_filtered_by_company(df, companies, config)`: Filter by company

### 8. scripts/dashboard.py

Streamlit interactive dashboard:

**Key Features**:
- Data loading from CSV files AND SQLite database (same columns now!)
- Robust path detection for both local and Docker execution
- Comprehensive filtering (text search, job level, sites, companies, etc.)
- Statistics view with metrics and charts
- Sortable/configurable job table with clickable job links
- Job details view with full description
- Export to CSV/Excel
- Cache refresh button

**Key Functions**:
- `load_csv_files()`: Load all CSV files from results directory (cached)
- `load_database()`: Load jobs from SQLite database (cached)
- `apply_filters(df, filters)`: Apply all filters to dataframe
- `render_sidebar_filters(df)`: Render filter UI
- `render_statistics(df, filtered_df)`: Render statistics section
- `render_job_table(df)`: Render job results table with clickable links
- `render_job_details(df)`: Render detailed job view
- `render_export_section(df)`: Render export options

**Path Resolution** (for Docker compatibility):
```python
# Handles both local and Docker/Streamlit execution
_script_dir = Path(__file__).resolve().parent
if _script_dir.name == "scripts":
    BASE_DIR = _script_dir.parent
else:
    # Fallback for Docker
    ...
if str(BASE_DIR).startswith("/app"):
    BASE_DIR = Path("/app")
```

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

# Launch dashboard
streamlit run dashboard.py
```

### Launch Dashboard

```bash
# Using Docker
docker-compose --profile dashboard up dashboard
# Open http://localhost:8501

# Using local Python
cd scripts
streamlit run dashboard.py
```

### Database Queries

```bash
# Statistics
sqlite3 data/jobs.db "SELECT COUNT(*), AVG(relevance_score) FROM jobs"

# New jobs today
sqlite3 data/jobs.db "SELECT title, company FROM jobs WHERE first_seen = date('now')"

# Top jobs not yet applied
sqlite3 data/jobs.db "SELECT title, company, relevance_score FROM jobs WHERE applied = 0 ORDER BY relevance_score DESC LIMIT 10"

# Mark job as applied
sqlite3 data/jobs.db "UPDATE jobs SET applied = 1 WHERE job_id = 'abc123...'"

# Jobs by site
sqlite3 data/jobs.db "SELECT site, COUNT(*) FROM jobs GROUP BY site"

# Remote jobs
sqlite3 data/jobs.db "SELECT title, company FROM jobs WHERE is_remote = 1 ORDER BY relevance_score DESC"

# Jobs with salary info
sqlite3 data/jobs.db "SELECT title, company, min_amount, max_amount, currency FROM jobs WHERE min_amount IS NOT NULL"
```

### View Logs

```bash
# Latest log
tail -f logs/search.log

# Search for errors
grep ERROR logs/search.log
```

## Configuration Guide

### Modify Search Queries

Edit `config/settings.yaml`:

```yaml
queries:
  my_custom_category:
    - "my custom query"
    - "another query"
```

No code changes required!

### Adjust Relevance Scoring

Edit `config/settings.yaml`:

```yaml
scoring:
  threshold: 15  # Increase for stricter filtering
  weights:
    primary_skills: 25  # Increase priority
    teaching: 0         # Disable category
  keywords:
    primary_skills:
      - "newkeyword"    # Add new keyword
```

### Change Search Parameters

Edit `config/settings.yaml`:

```yaml
search:
  results_wanted: 20    # Reduce if rate limited
  hours_old: 168        # 7 days instead of 30
  locations:
    - "Zurich, Switzerland"
```

### Adjust Parallelism

Edit `config/settings.yaml`:

```yaml
parallel:
  max_workers: 3  # Reduce if rate limited

retry:
  max_attempts: 5
  base_delay: 5
```

## Output Files

All files saved with timestamp format `YYYYMMDD_HHMMSS`:

- `results/all_jobs_{timestamp}.csv` - All jobs found
- `results/all_jobs_{timestamp}.xlsx` - Excel with formatting
- `results/relevant_jobs_{timestamp}.csv` - Jobs with score > threshold
- `results/relevant_jobs_{timestamp}.xlsx` - Excel with highlighting
- `data/jobs.db` - SQLite database with full job history
- `logs/search.log` - Structured log file with rotation

## Troubleshooting

### Rate Limiting

**Symptoms**: Empty results, connection errors after some queries

**Solutions**:
1. Reduce `parallel.max_workers` to 3 in settings.yaml
2. Reduce `search.results_wanted` to 20
3. Increase `retry.base_delay` to 5
4. Run at different times of day

### Docker Build Fails

```bash
docker-compose down
docker system prune -f
docker-compose up --build
```

### Import Errors

Ensure you're running from the scripts directory:

```bash
cd scripts
python search_jobs.py
```

### Database Locked

SQLite can only have one writer at a time. Wait for current operation or:

```bash
# Kill any running search
docker-compose down
```

### Dashboard Shows Different Data (CSV vs DB)

After updating the database schema, run a new search to populate all columns:

```bash
docker-compose up --build
```

Or delete the old database and start fresh:

```bash
rm data/jobs.db
docker-compose up --build
```

### Python Version

JobSpy requires Python 3.10+. Check your version:

```bash
python3 --version
```

If below 3.10, use Docker.

## Development Notes

### Adding a New Scoring Category

1. Add keywords to `config/settings.yaml`:
```yaml
scoring:
  keywords:
    my_category:
      - "keyword1"
      - "keyword2"
  weights:
    my_category: 10
```

2. The scoring logic in `scripts/search_jobs.py` dynamically reads from config, so no code changes needed!

### Adding a New Database Column

1. Add to `CREATE_TABLE` in `scripts/database.py`
2. Add migration statement to `MIGRATE_COLUMNS` list
3. Update `INSERT_OR_UPDATE` query
4. Update `SELECT_ALL` and `SELECT_NEW` queries
5. Update `JobDBRecord` dataclass in `scripts/models.py`
6. Update `_row_to_record()` method
7. Update `export_to_dataframe()` method
8. Update `save_job()` and `save_jobs_from_dataframe()` methods

### Adding a New Configuration Section

1. Add to `config/settings.yaml`
2. Create dataclass in `scripts/config.py`
3. Add parsing function `_parse_xxx_config()`
4. Update `Config` class with new field
5. Update `load_config()` to include new section

### Type Hints

All functions use type hints. Run type checker:

```bash
pip install mypy
mypy scripts/
```

### Logging Best Practices

- Use `get_logger("module_name")` for module-specific loggers
- Use `log_section()` for major operations
- Use `log_subsection()` for sub-operations
- Log levels: DEBUG for details, INFO for progress, WARNING for issues, ERROR for failures

## Performance

### Parallel Execution

- Default 5 workers provides good balance
- Reduce to 3 if hitting rate limits
- Each worker handles one query-location pair
- Execution time: ~3 minutes (was ~15 minutes sequential)

### Memory Usage

- Incremental deduplication reduces peak memory
- Large result sets (~10k jobs) may use ~500MB
- SQLite database grows with job count

### Database

- Tracks all jobs seen across runs with full details
- Identifies new jobs vs previously seen
- Supports marking jobs as "applied"
- Same columns as CSV for consistent dashboard experience

## External Dependencies

### JobSpy Library
- **GitHub**: https://github.com/speedyapply/JobSpy
- **Version**: 1.1.82 (latest as of December 2025)
- **Capabilities**: Scrapes LinkedIn, Indeed, Glassdoor, Google Jobs, Bayt, Naukri, BDJobs

### Pandas DataFrame Schema (JobSpy Output)
```python
columns = [
    'id', 'site', 'job_url', 'job_url_direct', 'title', 'company',
    'location', 'date_posted', 'job_type', 'salary_source', 'interval',
    'min_amount', 'max_amount', 'currency', 'is_remote', 'job_level',
    'job_function', 'listing_type', 'emails', 'description',
    'company_industry', 'company_url', 'company_logo', 'company_url_direct',
    'company_addresses', 'company_num_employees', 'company_revenue',
    'company_description', 'skills', 'experience_range', 'company_rating',
    'company_reviews_count', 'vacancy_count', 'work_from_home_type',
]
```

## JobSpy Optimization Guide

Based on analysis of JobSpy v1.1.82 source code:

### Key Findings

1. **JobSpy Already Uses Parallelism Internally**
   - In `__init__.py:120`, JobSpy uses ThreadPoolExecutor to scrape all sites concurrently
   - Our parallel query execution complements this (we parallelize queries, JobSpy parallelizes sites)

2. **Indeed Filter Limitation** (Critical!)
   - Indeed can only use ONE of:
     - `hours_old` (date filtering)
     - `job_type + is_remote` (combined filter)
     - `easy_apply`
   - **We prioritize `hours_old` over `job_type`** for fresher results

3. **LinkedIn Rate Limiting**
   - Built-in delays: 3-7 seconds between requests
   - Hard limit at 1000 results
   - Heavy rate limiting around 10th page
   - `linkedin_fetch_description=True` doubles request count

4. **Glassdoor Issues**
   - "Location not parsed" errors occur when location doesn't match database
   - 400 errors can be rate limiting or invalid queries

### Optimized Parameters

| Parameter | Setting | Reason |
|-----------|---------|--------|
| `distance` | 50 | 50 miles (~80km) covers metropolitan areas |
| `enforce_annual_salary` | true | Normalizes all salaries for comparison |
| `description_format` | "markdown" | Best for text analysis |
| `verbose` | 1 | Reduces noise (we have our own logging) |

### Site-Specific Behavior

**Indeed** (best coverage):
- No significant rate limiting
- 100 jobs per page internally
- Supports all filter parameters (with limitations above)

**LinkedIn**:
- Uses guest API (no login required)
- 25 jobs per page
- Aggressive rate limiting
- `linkedin_fetch_description=True` fetches full descriptions (slower but more data)

**Glassdoor**:
- GraphQL API
- 30 jobs per page
- May have location parsing issues

**Google Jobs**:
- Requires specific `google_search_term` syntax
- Normal `search_term` doesn't work well
- Syntax: copy from Google Jobs search bar

### Verbosity Levels

```python
verbose=0  # Errors only
verbose=1  # Errors + warnings (recommended)
verbose=2  # All logs (default, very noisy)
```

### Known Limitations

1. **Cannot filter by job_type AND hours_old on Indeed** - we prioritize freshness
2. **LinkedIn rate limits quickly** - use proxies for heavy scraping
3. **Glassdoor location parsing** - some queries return "location not parsed"
4. **Google Jobs needs specific syntax** - disabled by default

## License

MIT License - See LICENSE file for details.

---

**Last Updated**: 2025-12-22
