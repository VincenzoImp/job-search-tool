#!/usr/bin/env python3
"""
Job Search Tool - Automated Job Aggregation.

Aggregates job listings from multiple job boards using JobSpy.
Features parallel execution, throttling, retry logic, and configurable scoring.

Scoring, filtering, and export functionality are in separate modules:
- scoring.py: Relevance scoring, fuzzy matching, filtering
- exporter.py: CSV/Excel export
"""

from __future__ import annotations

import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pandas as pd
from jobspy import scrape_jobs
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import Config, get_config
from database import get_database
from exporter import save_results
from logger import ProgressLogger, get_logger, log_section, setup_logging
from models import SearchSummary, generate_job_id
from scoring import (
    filter_relevant_jobs,
    fuzzy_post_filter,
)


# Thread-safe lock for shared data structures
_jobs_lock = threading.Lock()


class ThrottledExecutor:
    """ThreadPoolExecutor wrapper with per-site rate limiting."""

    def __init__(self, config: Config):
        """
        Initialize throttled executor.

        Args:
            config: Configuration object with throttling settings.
        """
        self.config = config
        self.site_locks: dict[str, threading.Lock] = {}
        self.site_last_request: dict[str, float] = {}
        self._lock = threading.Lock()
        self._logger = get_logger("throttle")

    def _get_site_lock(self, site: str) -> threading.Lock:
        """Get or create a lock for a specific site."""
        with self._lock:
            if site not in self.site_locks:
                self.site_locks[site] = threading.Lock()
                self.site_last_request[site] = 0
            return self.site_locks[site]

    def throttled_search(
        self,
        query: str,
        location: str,
        config: Config,
    ) -> tuple[str, str, pd.DataFrame | None, str | None]:
        """
        Execute search with throttling based on configured sites.

        Since JobSpy internally searches all configured sites in parallel,
        we throttle based on the slowest (most restrictive) site delay
        to ensure we don't overwhelm any individual site.

        Args:
            query: Search term.
            location: Location to search.
            config: Configuration object.

        Returns:
            Tuple of (query, location, results_df, error_message).
        """
        if not config.throttling.enabled:
            # No throttling, execute immediately
            return search_single_query(query, location, config)

        # Get the maximum delay across all configured sites
        # This ensures we don't overwhelm the most restrictive site
        max_delay = config.throttling.default_delay
        for site in config.search.sites:
            site_delay = config.throttling.site_delays.get(
                site.lower(), config.throttling.default_delay
            )
            max_delay = max(max_delay, site_delay)

        # Use a global lock for throttling since we're searching all sites at once
        global_lock = self._get_site_lock("_global")

        with global_lock:
            # Calculate required delay
            now = time.time()
            elapsed = now - self.site_last_request.get("_global", 0)

            # Apply jitter to the delay
            if config.throttling.jitter > 0:
                jitter_amount = max_delay * config.throttling.jitter
                actual_delay = max_delay + random.uniform(-jitter_amount, jitter_amount)
            else:
                actual_delay = max_delay

            if elapsed < actual_delay:
                sleep_time = actual_delay - elapsed
                self._logger.debug(
                    f"Throttling: waiting {sleep_time:.2f}s before next request"
                )
                time.sleep(sleep_time)

            # Update last request time
            self.site_last_request["_global"] = time.time()

        # Execute search outside the lock
        return search_single_query(query, location, config)


def search_single_query(
    query: str,
    location: str,
    config: Config,
) -> tuple[str, str, pd.DataFrame | None, str | None]:
    """
    Execute a single search query with retry logic.

    Args:
        query: Search term.
        location: Location to search.
        config: Configuration object.

    Returns:
        Tuple of (query, location, results_df, error_message).
    """
    logger = get_logger("search")

    @retry(
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        stop=stop_after_attempt(config.retry.max_attempts),
        wait=wait_exponential(
            multiplier=config.retry.base_delay,
            exp_base=config.retry.backoff_factor,
        ),
        reraise=True,
    )
    def _do_search() -> pd.DataFrame:
        # NOTE: For Indeed, using hours_old disables job_type filtering (JobSpy limitation)
        # We prioritize date filtering over job type for broader results
        return scrape_jobs(
            # Core parameters
            site_name=config.search.sites,
            search_term=query,
            location=location,
            results_wanted=config.search.results_wanted,
            hours_old=config.search.hours_old,
            country_indeed=config.search.country_indeed,
            # JobSpy core parameters
            distance=config.search.distance,
            is_remote=config.search.is_remote,
            easy_apply=config.search.easy_apply,
            offset=config.search.offset,
            # Output format parameters
            enforce_annual_salary=config.search.enforce_annual_salary,
            description_format=config.search.description_format,
            verbose=config.search.verbose,
            # LinkedIn-specific parameters
            linkedin_fetch_description=config.search.linkedin_fetch_description,
            linkedin_company_ids=config.search.linkedin_company_ids,
            # Google Jobs-specific parameters
            google_search_term=config.search.google_search_term,
            # Network/Proxy parameters
            proxies=config.search.proxies,
            ca_cert=config.search.ca_cert,
            user_agent=config.search.user_agent,
        )

    try:
        jobs = _do_search()

        if jobs is not None and len(jobs) > 0:
            jobs["search_query"] = query
            jobs["search_location"] = location
            jobs["search_date"] = datetime.now().strftime("%Y-%m-%d")

            # Apply fuzzy post-filter to validate results match query terms
            original_count = len(jobs)
            jobs = fuzzy_post_filter(jobs, query, location, config)

            if len(jobs) < original_count:
                logger.debug(
                    f"Post-filter: {query} @ {location}: "
                    f"{original_count} -> {len(jobs)} jobs"
                )

            if len(jobs) == 0:
                return query, location, None, None

            return query, location, jobs, None
        else:
            return query, location, None, None

    except (ConnectionError, TimeoutError) as e:
        # Network errors - may be recoverable on retry
        error_msg = f"Network error: {e}"
        logger.warning(f"Query failed: {query} @ {location}: {error_msg}")
        return query, location, None, error_msg
    except ValueError as e:
        # Invalid data from JobSpy
        error_msg = f"Data error: {e}"
        logger.warning(f"Query failed: {query} @ {location}: {error_msg}")
        return query, location, None, error_msg
    except (KeyError, AttributeError) as e:
        # Unexpected response structure
        error_msg = f"Parse error: {e}"
        logger.error(f"Query failed: {query} @ {location}: {error_msg}")
        return query, location, None, error_msg
    except Exception as e:
        # Catch-all for unexpected errors (e.g. upstream JobSpy bugs)
        error_msg = f"Unexpected error ({type(e).__name__}): {e}"
        logger.warning(f"Query failed: {query} @ {location}: {error_msg}")
        return query, location, None, error_msg


def search_jobs(config: Config) -> tuple[pd.DataFrame | None, SearchSummary]:
    """
    Search for jobs using parallel execution with throttling.

    Args:
        config: Configuration object.

    Returns:
        Tuple of (combined_jobs_df, search_summary).
    """
    logger = get_logger("search")
    summary = SearchSummary()

    log_section(logger, "SEARCHING FOR JOBS")

    queries = config.get_all_queries()
    locations = config.search.locations

    # Build list of all search tasks
    tasks = [(q, loc) for loc in locations for q in queries]
    summary.total_queries = len(tasks)

    logger.info(f"Total search tasks: {len(tasks)}")
    logger.info(f"Queries: {len(queries)}, Locations: {len(locations)}")
    logger.info(f"Parallel workers: {config.parallel.max_workers}")

    # Log throttling status
    if config.throttling.enabled:
        # Calculate effective delay (max of configured sites)
        max_delay = config.throttling.default_delay
        for site in config.search.sites:
            site_delay = config.throttling.site_delays.get(
                site.lower(), config.throttling.default_delay
            )
            max_delay = max(max_delay, site_delay)
        logger.info(
            f"Throttling enabled: {max_delay:.1f}s delay "
            f"(jitter={config.throttling.jitter:.0%})"
        )
        # Estimate total time
        estimated_time = len(tasks) * max_delay / config.parallel.max_workers
        logger.info(f"Estimated minimum time: {estimated_time / 60:.1f} minutes")
    else:
        logger.info("Throttling disabled")

    all_jobs: list[pd.DataFrame] = []
    seen_jobs: set[str] = set()  # For deduplication

    progress = ProgressLogger(logger, len(tasks), "Job search")

    # Create throttled executor
    throttled_executor = ThrottledExecutor(config)

    # Execute searches in parallel with throttling
    with ThreadPoolExecutor(max_workers=config.parallel.max_workers) as executor:
        futures = {
            executor.submit(throttled_executor.throttled_search, q, loc, config): (
                q,
                loc,
            )
            for q, loc in tasks
        }

        for future in as_completed(futures):
            query, location = futures[future]

            try:
                q, loc, jobs_df, error = future.result()

                if error:
                    summary.failed_queries += 1
                    progress.update(
                        success=False, message=f"FAILED: {query} @ {location}"
                    )
                elif jobs_df is not None and len(jobs_df) > 0:
                    summary.successful_queries += 1
                    summary.total_jobs_found += len(jobs_df)

                    # Deduplicate incrementally
                    # Step 1: Generate keys outside lock (compute-intensive)
                    job_keys = [
                        generate_job_id(
                            str(row.get("title", "")),
                            str(row.get("company", "")),
                            str(row.get("location", "")),
                        )
                        for _, row in jobs_df.iterrows()
                    ]

                    # Step 2: Lock for both set operations AND list append (thread safety)
                    with _jobs_lock:
                        new_indices = [
                            i for i, key in enumerate(job_keys) if key not in seen_jobs
                        ]
                        seen_jobs.update(job_keys[i] for i in new_indices)

                        # Append inside the lock to prevent concurrent list mutations
                        if new_indices:
                            new_df = jobs_df.iloc[new_indices].copy()
                            all_jobs.append(new_df)

                    progress.update(
                        success=True,
                        message=f"Found {len(jobs_df)} jobs: {query} @ {location}",
                    )
                else:
                    summary.successful_queries += 1
                    progress.update(
                        success=True, message=f"No results: {query} @ {location}"
                    )

            except Exception as e:
                summary.failed_queries += 1
                logger.error(f"Unexpected error for {query} @ {location}: {e}")
                progress.update(success=False, message=f"ERROR: {query}")

    progress.summary()

    if not all_jobs:
        logger.warning("No jobs found in any search.")
        summary.finish()
        return None, summary

    # Combine all results
    combined_jobs = pd.concat(all_jobs, ignore_index=True)
    summary.unique_jobs = len(combined_jobs)

    logger.info(f"Total unique jobs after deduplication: {len(combined_jobs)}")

    summary.finish()
    return combined_jobs, summary


def print_banner(config: Config) -> None:
    """Print application banner with profile info using logger."""
    logger = get_logger("banner")
    profile = config.profile

    # Truncate long strings to fit banner width
    def truncate(text: str, max_len: int) -> str:
        return text[:max_len] if len(text) <= max_len else text[: max_len - 3] + "..."

    name = truncate(profile.name, 33)
    position = truncate(profile.current_position, 65)
    skills = truncate(profile.skills, 56)
    target = truncate(profile.target, 56)

    banner_lines = [
        "",
        "╔══════════════════════════════════════════════════════════════════════╗",
        f"║             Job Search Tool - {name:<33} ║",
        "║                                                                      ║",
        "║  Profile:                                                            ║",
        f"║  • {position:<65} ║",
        f"║  • Skills: {skills:<56} ║",
        f"║  • Target: {target:<56} ║",
        "╚══════════════════════════════════════════════════════════════════════╝",
        "",
    ]

    for line in banner_lines:
        logger.info(line)


def print_top_jobs(jobs_df: pd.DataFrame, count: int = 10) -> None:
    """Print top N jobs by relevance score."""
    logger = get_logger("results")

    log_section(logger, f"TOP {count} MOST RELEVANT JOBS")

    for idx, (_, row) in enumerate(jobs_df.head(count).iterrows(), 1):
        logger.info(f"\n{idx}. {row['title']}")
        logger.info(f"   Company: {row['company']}")
        logger.info(f"   Location: {row['location']}")
        logger.info(f"   Relevance Score: {row['relevance_score']}")
        if pd.notna(row.get("job_url")):
            logger.info(f"   URL: {row['job_url']}")


def main() -> None:
    """Main execution function."""
    # Load configuration
    config = get_config()

    # Setup logging
    logger = setup_logging(config)

    # Print banner
    print_banner(config)

    # Initialize database
    db = get_database(config)
    db_stats = db.get_statistics()
    logger.info(f"Database: {db_stats['total_jobs']} jobs tracked")

    # Search for jobs
    all_jobs, summary = search_jobs(config)

    if all_jobs is None or len(all_jobs) == 0:
        logger.error("No jobs found. Exiting.")
        return

    # Save all results
    log_section(logger, "SAVING ALL RESULTS")
    save_results(all_jobs, config, "all_jobs")

    # Filter relevant jobs
    relevant_jobs = filter_relevant_jobs(all_jobs, config)
    summary.relevant_jobs = len(relevant_jobs)

    if len(relevant_jobs) == 0:
        logger.warning("No highly relevant jobs found after filtering.")
        logger.info("Tip: Check the 'all_jobs' file for broader results.")
        return

    # Save filtered results
    log_section(logger, "SAVING FILTERED RESULTS")
    save_results(relevant_jobs, config, "relevant_jobs")

    # Save to database and identify new jobs
    new_count, updated_count = db.save_jobs_from_dataframe(relevant_jobs)
    summary.new_jobs = new_count

    logger.info(f"Database updated: {new_count} new, {updated_count} existing")

    # Print top matches
    print_top_jobs(relevant_jobs)

    # Print summary
    log_section(logger, "SEARCH COMPLETE")
    logger.info(f"Duration: {summary.duration_formatted}")
    logger.info(f"Total unique jobs: {summary.unique_jobs}")
    logger.info(f"Highly relevant jobs: {summary.relevant_jobs}")
    logger.info(f"New jobs (first time seen): {summary.new_jobs}")
    logger.info("Check the 'results' folder for detailed CSV and Excel files.")


if __name__ == "__main__":
    main()
