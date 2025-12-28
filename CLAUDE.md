# CLAUDE.md - Job Search Tool

## Project Overview

This is an automated job search and analysis tool powered by the JobSpy library to aggregate positions from multiple job boards. It features parallel execution, relevance scoring, SQLite persistence, an interactive Streamlit dashboard, **automated scheduling**, and **Telegram notifications**.

The tool is **highly customizable** through YAML configuration - no code changes needed to customize for different profiles, locations, or job types.

### Key Features

- **Automated Scheduling**: Run searches automatically at configurable intervals (default: 24 hours)
- **Telegram Notifications**: Receive alerts when new relevant jobs are found
- **Parallel Execution**: Fast searches using ThreadPoolExecutor
- **Rate Limit Prevention**: Configurable throttling with per-site delays and jitter
- **Fuzzy Post-Filtering**: Validate results match query terms with typo tolerance
- **Smart Deduplication**: Track jobs across runs, identify new vs. seen jobs
- **Relevance Scoring**: Customizable keyword-based scoring system
- **Interactive Dashboard**: Streamlit UI for exploring and filtering results

## Architecture

### Technology Stack

- **Python 3.11**: Core language (3.10+ required by JobSpy library)
- **JobSpy v1.1.82**: Web scraping library for job sites (LinkedIn, Indeed, Glassdoor, Google Jobs, etc.)
- **Pandas**: Data manipulation and analysis
- **OpenPyXL**: Excel file generation with formatting
- **Streamlit**: Interactive dashboard with caching
- **PyYAML**: YAML configuration parsing
- **Tenacity**: Retry logic with exponential backoff
- **APScheduler**: Automated periodic execution
- **python-telegram-bot**: Telegram notification integration
- **Jinja2**: Template engine for notification formatting
- **rapidfuzz**: Fuzzy string matching for post-filtering
- **SQLite**: Job persistence and tracking across runs
- **Docker**: Containerized environment for cross-platform compatibility

### Project Structure

```
job-search-tool/
├── config/
│   ├── settings.yaml          # User configuration (gitignored)
│   └── settings.example.yaml  # Example template with full documentation
├── scripts/
│   ├── main.py                # Unified entry point (scheduler + notifications)
│   ├── search_jobs.py         # Core job search with parallel execution
│   ├── scheduler.py           # APScheduler integration for periodic runs
│   ├── notifier.py            # Telegram notification system
│   ├── report_generator.py    # Report formatting for notifications
│   ├── analyze_jobs.py        # Post-search analysis and reporting
│   ├── dashboard.py           # Streamlit interactive dashboard
│   ├── config.py              # Configuration loader with validation
│   ├── logger.py              # Structured logging with rotation
│   ├── database.py            # SQLite persistence for job tracking
│   └── models.py              # Type-safe dataclasses
├── templates/                  # Jinja2 templates for notifications
│   └── telegram_summary.md.j2 # Telegram message template
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
- **throttling**: enabled, default_delay, site_delays, jitter, rate_limit_cooldown
- **post_filter**: enabled, min_similarity, check_query_terms, check_location
- **logging**: level, file path, rotation settings
- **output**: results_dir, data_dir, database_file, save_csv, save_excel
- **profile**: User information for display
- **scheduler**: enabled, interval_hours, run_on_startup, retry settings
- **notifications**: enabled, telegram configuration

See `config/settings.example.yaml` for full parameter documentation.

### 2. scripts/config.py

Configuration loader with type-safe dataclasses:

**Key Classes**:
- `SearchConfig`: Search parameters (results_wanted, hours_old, etc.)
- `ScoringConfig`: Relevance scoring weights and keywords
- `ParallelConfig`: Concurrency settings (max_workers)
- `RetryConfig`: Retry logic parameters
- `ThrottlingConfig`: Rate limit prevention (default_delay, site_delays, jitter)
- `PostFilterConfig`: Fuzzy post-filtering (enabled, min_similarity, check_query_terms, check_location)
- `LoggingConfig`: Logging configuration
- `OutputConfig`: File paths and output options (save_csv, save_excel)
- `ProfileConfig`: User profile information
- `SchedulerConfig`: Scheduling settings (enabled, interval_hours, etc.)
- `TelegramConfig`: Telegram bot settings (bot_token, chat_ids, etc.)
- `NotificationsConfig`: Notification channel settings
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

Main job search with parallel execution and throttling:

**Key Classes**:

- `ThrottledExecutor`: ThreadPoolExecutor wrapper with rate limiting
  - Per-site delays with configurable jitter
  - Thread-safe locking for concurrent access
  - `throttled_search()`: Execute search with delay enforcement

**Key Functions**:

- `calculate_relevance_score(row, config)`: Calculate score based on keywords
  - Uses weights and keywords from config
  - Returns integer score

- `search_single_query(query, location, config)`: Execute one search
  - Retry logic with exponential backoff via tenacity
  - Returns (query, location, df, error)

- `search_jobs(config)`: Main parallel search with throttling
  - Uses ThreadPoolExecutor with ThrottledExecutor
  - Logs throttling status and estimated time
  - Incremental deduplication during collection
  - Returns (combined_df, SearchSummary)

- `filter_relevant_jobs(df, config)`: Filter by score threshold
  - Calculates scores for all jobs
  - Returns filtered, sorted DataFrame

- `save_results(df, config, prefix)`: Save to CSV and Excel
  - Excel formatting: colored headers, hyperlinks, freeze panes
  - Conditional formatting for high scores

- `main()`: Legacy entry point (use main.py instead)
  - Loads config, sets up logging
  - Runs search, saves results
  - Updates database with full job details, prints summary

### 7. scripts/main.py (NEW - Unified Entry Point)

Main entry point that integrates scheduling and notifications:

**Key Functions**:
- `run_job_search()`: Execute single search iteration with notifications
- `main()`: Entry point that handles both single-shot and scheduled modes

**Execution Flow**:
1. Load configuration
2. Determine mode (single-shot vs scheduled)
3. If scheduled: start APScheduler with configured interval
4. Execute search via `search_jobs()`
5. Save results to CSV/Excel
6. Update database
7. Send Telegram notification if new jobs found

### 8. scripts/scheduler.py (NEW)

APScheduler integration for automated periodic execution:

**Key Class**: `JobSearchScheduler`
- `start()`: Start continuous scheduled execution
- `run_once()`: Execute single search (non-scheduled mode)
- `stop()`: Graceful shutdown

**Features**:
- Configurable interval (default: 24 hours)
- Optional immediate run on startup
- Retry logic on failure
- Graceful signal handling (SIGINT, SIGTERM)

### 9. scripts/notifier.py (NEW)

Telegram notification system:

**Key Classes**:
- `BaseNotifier`: Abstract base class for notification channels
- `TelegramNotifier`: Telegram-specific implementation
- `NotificationManager`: Manages all configured channels

**NotificationData Structure**:
```python
@dataclass
class NotificationData:
    run_timestamp: datetime
    total_jobs_found: int
    new_jobs_count: int
    updated_jobs_count: int
    avg_score: float
    top_jobs: list[JobDBRecord]
    all_new_jobs: list[JobDBRecord]
```

**Telegram Message Format**:
- Summary header with run statistics
- Top N new jobs with details (title, company, location, score)
- Clickable links to job postings
- MarkdownV2 formatting

### 10. scripts/report_generator.py (NEW)

Report formatting utilities:

**Key Functions**:
- `generate_text_summary()`: Plain text report
- `generate_markdown_summary()`: Markdown formatted report
- `jobs_to_dataframe()`: Convert JobDBRecord list to DataFrame
- `generate_excel_report()`: Create Excel file in memory (BytesIO)

### 11. scripts/analyze_jobs.py

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

### 12. scripts/dashboard.py

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

### Run Job Search (Single-Shot Mode)

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

# Run search (new unified entry point)
cd scripts
python main.py

# Or use legacy entry point
python search_jobs.py

# Analyze results
python analyze_jobs.py

# Launch dashboard
streamlit run dashboard.py
```

### Run Scheduled Mode (with Notifications)

First, configure `config/settings.yaml`:
```yaml
scheduler:
  enabled: true
  interval_hours: 24

notifications:
  enabled: true
  telegram:
    enabled: true
    bot_token: "YOUR_BOT_TOKEN"
    chat_ids:
      - "YOUR_CHAT_ID"
```

Then run:
```bash
# Using Docker (recommended - runs continuously)
docker-compose --profile scheduler up scheduler --build

# Or using local Python
cd scripts
python main.py
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

### Setup Telegram Bot

1. **Create bot with @BotFather**:
   - Open Telegram and search for `@BotFather`
   - Send `/newbot` and follow instructions
   - Copy the bot token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Get your chat_id**:
   - Start a chat with your new bot (send any message)
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Look for `"chat":{"id": YOUR_CHAT_ID}`

3. **Configure settings.yaml**:
   ```yaml
   notifications:
     enabled: true
     telegram:
       enabled: true
       bot_token: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
       chat_ids:
         - "987654321"  # Your chat ID
   ```

4. **Test notification**:
   ```bash
   docker-compose --profile scheduler up scheduler --build
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
  country_indeed: "USA" # Country for Indeed domain
  locations:
    - "New York, NY"
    - "Remote"
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

### Configure Scheduling

Edit `config/settings.yaml`:

```yaml
scheduler:
  enabled: true           # Enable scheduled mode
  interval_hours: 24      # Run every 24 hours
  run_on_startup: true    # Run immediately when starting
  retry_on_failure: true  # Retry if search fails
  retry_delay_minutes: 30 # Wait 30 min before retry
```

### Configure Throttling

Throttling adds delays between requests to prevent rate limiting from job boards. Edit `config/settings.yaml`:

```yaml
throttling:
  enabled: true           # Enable throttling (recommended)
  default_delay: 1.5      # Default delay between requests (seconds)
  site_delays:            # Per-site delay overrides
    linkedin: 3.0         # LinkedIn has aggressive rate limiting
    indeed: 1.0           # Indeed is more lenient
    glassdoor: 1.5        # Glassdoor is moderate
    google: 2.0
    ziprecruiter: 1.5
  jitter: 0.3             # Random variation (0.3 = 30%)
  rate_limit_cooldown: 30.0  # Cooldown after rate limit error
```

**Expected performance with throttling enabled:**

| Configuration | 100 Searches | Notes |
|---------------|--------------|-------|
| No throttling, 4 workers | ~3 min | High rate limit risk |
| 1.5s delay, 4 workers | ~8 min | Moderate risk |
| 3.0s delay, 2 workers | ~15 min | Low risk |

### Configure Fuzzy Post-Filtering

Post-filtering validates that returned jobs actually match your search query and location. This is important because job boards often return "related" results that don't match the original query. Edit `config/settings.yaml`:

```yaml
post_filter:
  enabled: true           # Enable fuzzy post-filtering (recommended)
  min_similarity: 80      # Similarity threshold 0-100 (80 = allows zürich/zurich)
  check_query_terms: true # Verify all query words are in job data
  check_location: true    # Verify location matches (skipped for "Remote")
```

**How it works:**
- For query `"python developer"` with location `"Zurich, Switzerland"`:
  - Job must contain "python" somewhere (title/description/company)
  - Job must contain "developer" somewhere
  - Job must contain "zurich" OR "switzerland" in location
- Uses fuzzy matching: `zürich` ≈ `zurich` ≈ `zuerich` (within 80% similarity)
- Handles typos: `pythom` ≈ `python`

### Configure Telegram Notifications

Edit `config/settings.yaml`:

```yaml
notifications:
  enabled: true
  telegram:
    enabled: true
    bot_token: "YOUR_BOT_TOKEN"        # From @BotFather
    chat_ids:
      - "YOUR_CHAT_ID"                 # Your personal chat ID
    send_summary: true                 # Send after each run
    min_score_for_notification: 15     # Only jobs with score >= 15
    max_jobs_in_message: 50            # Max jobs in message (was hardcoded to 10)
```

### Disable CSV/Excel Output

Edit `config/settings.yaml`:

```yaml
output:
  results_dir: "results"
  data_dir: "data"
  database_file: "jobs.db"
  save_csv: false   # Disable CSV file generation
  save_excel: false # Disable Excel file generation
```

The SQLite database is always used (required for core functionality). CSV/Excel are optional exports for human review.

## Output Files

All files saved with timestamp format `YYYYMMDD_HHMMSS`:

**Required (core system):**
- `data/jobs.db` - SQLite database with full job history (PRIMARY storage)
- `logs/search.log` - Structured log file with rotation

**Optional (controlled by `save_csv` and `save_excel` in config):**
- `results/all_jobs_{timestamp}.csv` - All jobs found
- `results/all_jobs_{timestamp}.xlsx` - Excel with formatting
- `results/relevant_jobs_{timestamp}.csv` - Jobs with score > threshold
- `results/relevant_jobs_{timestamp}.xlsx` - Excel with highlighting

**Note:** The SQLite database is the PRIMARY storage used by the core system for:
- Tracking all jobs seen across runs
- Identifying new vs already-seen jobs
- Determining which jobs to notify about
- Marking jobs as "applied"

CSV/Excel files are OPTIONAL and only used for human review/export. Set `save_csv: false` and `save_excel: false` in config to disable them.

## Troubleshooting

### Rate Limiting

**Symptoms**: Empty results, connection errors after some queries, 429 errors

**Solutions**:
1. Enable throttling if disabled: `throttling.enabled: true`
2. Increase delays: `throttling.default_delay: 2.0` or higher
3. Increase LinkedIn-specific delay: `throttling.site_delays.linkedin: 5.0`
4. Reduce `parallel.max_workers` to 2-3 in settings.yaml
5. Reduce `search.results_wanted` to 20
6. Increase `retry.base_delay` to 5
7. Run at different times of day

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

This tool requires Python 3.10+ (JobSpy library requirement). Check your version:

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

### Parallel Execution with Throttling

- Default 5 workers with throttling enabled provides balance between speed and rate limit safety
- Throttling uses per-site delays (LinkedIn: 3s, Indeed: 1s, etc.)
- Jitter (default 30%) randomizes delays to avoid detection patterns
- Reduce workers to 2-3 if still hitting rate limits
- Each worker handles one query-location pair

**Estimated execution times (100 searches):**

| Throttling | Workers | Est. Time | Rate Limit Risk |
|------------|---------|-----------|-----------------|
| Disabled | 5 | ~3 min | High |
| 1.5s delay | 5 | ~8 min | Moderate |
| 3.0s delay | 3 | ~15 min | Low |
| 3.0s delay | 1 | ~30 min | Minimal |

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

**Last Updated**: 2025-12-27

## Changelog

### v2.3.0 (2025-12-28) - Professional Audit & Fixes
- **CRITICAL FIX**: Scheduler retry time calculation bug (incorrect modulo arithmetic)
- **CRITICAL FIX**: SQL error handling now only ignores duplicate column errors
- **HIGH FIX**: Telegram token now supports environment variable (security)
- **HIGH FIX**: Removed hardcoded personal information from ProfileConfig defaults
- **HIGH FIX**: SQLite connection properly managed with context manager
- **HIGH FIX**: Race condition in job deduplication resolved
- **HIGH FIX**: asyncio.run() now works in async contexts
- **MEDIUM FIX**: N+1 database query optimized to single batch query
- **MEDIUM FIX**: Dockerfile gcc removed after build (smaller image)
- **MEDIUM FIX**: Config singleton now thread-safe with locking
- **MEDIUM FIX**: Input validation for all config parameters
- **MEDIUM FIX**: Version upper bounds added to all dependencies
- **LOW FIX**: Type hints corrected (any → Any)
- **LOW FIX**: Color codes only applied to TTY output
- **LOW FIX**: All print() replaced with logger
- Improved code quality, security, and thread safety throughout
- See [AUDIT_FIXES.md](AUDIT_FIXES.md) for complete details

### v2.2.0 (2025-12-27)
- **NEW**: Fuzzy post-filtering to validate results match query terms
- **NEW**: `PostFilterConfig` with min_similarity, check_query_terms, check_location
- **NEW**: Added `rapidfuzz` dependency for fuzzy string matching
- **FIX**: Removed hardcoded 10 job limit in Telegram notifications (now uses config)
- Handles character variations (ü/u, ö/o) and typos automatically

### v2.1.0 (2025-12-27)
- **NEW**: Configurable throttling to prevent rate limiting
- **NEW**: Per-site delay configuration with jitter
- **NEW**: `country_indeed` configuration option
- **REFACTOR**: Renamed `search_switzerland_jobs()` to `search_jobs()` for genericity
- **REFACTOR**: Removed Switzerland-specific defaults (now uses generic defaults)
- **REFACTOR**: Updated logger names from `switzerland_jobs` to `job_search`
- Simplified banner display

### v2.0.0 (2025-12-23)
- **NEW**: Automated scheduling with APScheduler
- **NEW**: Telegram notifications for new jobs
- **NEW**: Unified entry point (`main.py`)
- **NEW**: Report generator for notification formatting
- **NEW**: Templates directory for Jinja2 templates
- Updated Docker configuration with scheduler service
- Backward compatible - existing workflows still work
