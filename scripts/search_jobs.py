#!/usr/bin/env python3
"""
Switzerland Jobs Search - PhD & Software Engineering Positions.

Searches for blockchain, distributed systems, and data analysis roles in Switzerland.
Features parallel execution, retry logic, SQLite persistence, and configurable scoring.
"""

from __future__ import annotations

import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any

import pandas as pd
from jobspy import scrape_jobs
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import Config, get_config
from database import get_database
from logger import ProgressLogger, get_logger, log_section, setup_logging
from models import Job, SearchSummary


# Thread-safe lock for shared data structures
_jobs_lock = threading.Lock()


def calculate_relevance_score(row: pd.Series, config: Config) -> int:
    """
    Calculate relevance score based on user profile and configuration.

    Args:
        row: DataFrame row with job data.
        config: Configuration with scoring weights and keywords.

    Returns:
        Relevance score as integer.
    """
    score = 0
    text = " ".join(
        [
            str(row.get("title", "") or ""),
            str(row.get("description", "") or ""),
            str(row.get("company", "") or ""),
        ]
    ).lower()

    weights = config.scoring.weights
    keywords = config.scoring.keywords

    # Blockchain & Distributed Systems
    if any(kw in text for kw in keywords.get("blockchain", [])):
        score += weights.get("blockchain", 20)

    # PhD/Research positions
    if any(kw in text for kw in keywords.get("phd", [])):
        score += weights.get("phd_research", 18)

    # Data analysis & user behavior
    if any(kw in text for kw in keywords.get("data", [])):
        score += weights.get("data_analysis", 15)

    # Security & Privacy
    if any(kw in text for kw in keywords.get("security", [])):
        score += weights.get("security", 12)

    # Social network analysis
    if any(kw in text for kw in keywords.get("social", [])):
        score += weights.get("social_network", 10)

    # Technical skills
    if any(kw in text for kw in keywords.get("tech", [])):
        score += weights.get("tech_skills", 8)

    # Summer programs
    if any(kw in text for kw in keywords.get("summer", [])):
        score += weights.get("summer_programs", 15)

    # Academic institutions
    if any(kw in text for kw in keywords.get("academic", [])):
        score += weights.get("academic", 12)

    # Open source
    if "open source" in text or "opensource" in text:
        score += weights.get("open_source", 8)

    # Hackathon/competition
    if "hackathon" in text or "competition" in text:
        score += weights.get("hackathon", 5)

    # Teaching
    if "teaching" in text or "lecturer" in text:
        score += weights.get("teaching", 6)

    # Computer Science
    if "computer science" in text:
        score += weights.get("computer_science", 5)

    # Location bonuses
    if "zurich" in text or "zürich" in text:
        score += weights.get("location_bonus", 5)
    elif "lausanne" in text or "epfl" in text:
        score += weights.get("location_bonus", 5)

    # ETH Zurich specific bonus
    if "eth zurich" in text or "eth zürich" in text:
        score += weights.get("eth_zurich", 10)

    return score


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
            country_indeed="Switzerland",
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
            return query, location, jobs, None
        else:
            return query, location, None, None

    except Exception as e:
        error_msg = str(e)
        logger.warning(f"Query failed: {query} @ {location}: {error_msg}")
        return query, location, None, error_msg


def search_switzerland_jobs(config: Config) -> tuple[pd.DataFrame | None, SearchSummary]:
    """
    Search for relevant jobs in Switzerland using parallel execution.

    Args:
        config: Configuration object.

    Returns:
        Tuple of (combined_jobs_df, search_summary).
    """
    logger = get_logger("search")
    summary = SearchSummary()

    log_section(logger, "SEARCHING FOR JOBS IN SWITZERLAND")

    queries = config.get_all_queries()
    locations = config.search.locations

    # Build list of all search tasks
    tasks = [(q, loc) for loc in locations for q in queries]
    summary.total_queries = len(tasks)

    logger.info(f"Total search tasks: {len(tasks)}")
    logger.info(f"Queries: {len(queries)}, Locations: {len(locations)}")
    logger.info(f"Parallel workers: {config.parallel.max_workers}")

    all_jobs: list[pd.DataFrame] = []
    seen_jobs: set[str] = set()  # For deduplication

    progress = ProgressLogger(logger, len(tasks), "Job search")

    # Execute searches in parallel
    with ThreadPoolExecutor(max_workers=config.parallel.max_workers) as executor:
        futures = {
            executor.submit(search_single_query, q, loc, config): (q, loc)
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
                    new_jobs = []
                    for _, row in jobs_df.iterrows():
                        job_key = _generate_job_key(row)
                        with _jobs_lock:
                            if job_key not in seen_jobs:
                                seen_jobs.add(job_key)
                                new_jobs.append(row)

                    if new_jobs:
                        new_df = pd.DataFrame(new_jobs)
                        with _jobs_lock:
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


def _generate_job_key(row: pd.Series) -> str:
    """Generate unique key for job deduplication."""
    identifier = f"{row.get('title', '')}|{row.get('company', '')}|{row.get('location', '')}".lower()
    return hashlib.sha256(identifier.encode()).hexdigest()[:16]


def filter_relevant_jobs(jobs_df: pd.DataFrame, config: Config) -> pd.DataFrame:
    """
    Filter jobs based on relevance score.

    Args:
        jobs_df: DataFrame with all jobs.
        config: Configuration with scoring settings.

    Returns:
        Filtered DataFrame with relevant jobs.
    """
    logger = get_logger("filter")

    log_section(logger, "FILTERING RELEVANT JOBS")

    # Calculate relevance scores
    jobs_df = jobs_df.copy()
    jobs_df["relevance_score"] = jobs_df.apply(
        lambda row: calculate_relevance_score(row, config), axis=1
    )

    # Filter by threshold
    threshold = config.scoring.threshold
    relevant_jobs = jobs_df[jobs_df["relevance_score"] > threshold].copy()
    relevant_jobs = relevant_jobs.sort_values("relevance_score", ascending=False)

    logger.info(f"Score threshold: {threshold}")
    logger.info(f"Relevant jobs found: {len(relevant_jobs)}")

    if len(relevant_jobs) > 0:
        logger.info(f"Highest score: {relevant_jobs['relevance_score'].max()}")
        logger.info(f"Average score: {relevant_jobs['relevance_score'].mean():.1f}")

    return relevant_jobs


def save_results(
    jobs_df: pd.DataFrame,
    config: Config,
    filename_prefix: str = "jobs",
) -> tuple[str, str]:
    """
    Save results to CSV and Excel with formatting.

    Args:
        jobs_df: DataFrame to save.
        config: Configuration object.
        filename_prefix: Prefix for output files.

    Returns:
        Tuple of (csv_path, excel_path).
    """
    logger = get_logger("output")

    # Check if any output is enabled
    if not config.output.save_csv and not config.output.save_excel:
        logger.info("File output disabled (save_csv and save_excel are both false)")
        return "", ""

    results_dir = config.results_path
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = ""
    excel_path = ""

    # Save to CSV
    if config.output.save_csv:
        csv_file = results_dir / f"{filename_prefix}_{timestamp}.csv"
        jobs_df.to_csv(csv_file, index=False)
        logger.info(f"Saved CSV: {csv_file}")
        csv_path = str(csv_file)

    # Save to Excel with formatting
    if config.output.save_excel:
        excel_file = results_dir / f"{filename_prefix}_{timestamp}.xlsx"

        try:
            with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
                jobs_df.to_excel(writer, index=False, sheet_name="Jobs")
                worksheet = writer.sheets["Jobs"]

                # Format header row
                header_fill = PatternFill(
                    start_color="4472C4", end_color="4472C4", fill_type="solid"
                )
                header_font = Font(bold=True, color="FFFFFF")

                for col_num, column_title in enumerate(jobs_df.columns, 1):
                    cell = worksheet.cell(row=1, column=col_num)
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="center")

                # Auto-adjust column widths
                for col_num, column in enumerate(jobs_df.columns, 1):
                    max_length = max(
                        jobs_df[column].astype(str).map(len).max(),
                        len(str(column)),
                    )
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[get_column_letter(col_num)].width = (
                        adjusted_width
                    )

                # Make URLs clickable
                if "job_url" in jobs_df.columns:
                    url_col = jobs_df.columns.get_loc("job_url") + 1
                    for row_num in range(2, len(jobs_df) + 2):
                        cell = worksheet.cell(row=row_num, column=url_col)
                        if cell.value and str(cell.value).startswith("http"):
                            cell.hyperlink = cell.value
                            cell.font = Font(color="0563C1", underline="single")

                # Freeze header row
                worksheet.freeze_panes = "A2"

                # Conditional formatting for relevance score
                if "relevance_score" in jobs_df.columns:
                    score_col = jobs_df.columns.get_loc("relevance_score") + 1
                    high_score_fill = PatternFill(
                        start_color="C6EFCE", end_color="C6EFCE", fill_type="solid"
                    )
                    for row_num in range(2, len(jobs_df) + 2):
                        cell = worksheet.cell(row=row_num, column=score_col)
                        if cell.value and int(cell.value) >= 30:
                            cell.fill = high_score_fill

            logger.info(f"Saved Excel: {excel_file}")
            excel_path = str(excel_file)

        except Exception as e:
            logger.warning(f"Could not save Excel file: {e}")

    return csv_path, excel_path


def print_banner(config: Config) -> None:
    """Print application banner with profile info."""
    profile = config.profile
    banner = f"""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║          Switzerland Jobs Search - {profile.name:<29} ║
    ║                                                                      ║
    ║  Profile:                                                            ║
    ║  • {profile.current_position:<65} ║
    ║  • {profile.visiting_position:<65} ║
    ║  • Research: {profile.research_focus:<54} ║
    ║  • Published: {profile.publication:<53} ║
    ║  • {profile.grant:<65} ║
    ║  • Skills: {profile.skills:<56} ║
    ║  • Target: {profile.target:<56} ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


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
    all_jobs, summary = search_switzerland_jobs(config)

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
    logger.info(f"Check the 'results' folder for detailed CSV and Excel files.")


if __name__ == "__main__":
    main()
