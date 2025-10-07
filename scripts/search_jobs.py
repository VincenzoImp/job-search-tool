"""
Generalized Job Search Tool
Searches for jobs across multiple sites and locations based on configuration file.
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
from jobspy import scrape_jobs
import yaml
import logging
from typing import Dict, List, Any, Optional
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JobSearcher:
    """Main job search class that uses configuration file."""

    def __init__(self, config_path: str = "../config/config.yaml"):
        """Initialize with configuration file."""
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.all_jobs = []

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        config_file = Path(config_path)

        if not config_file.exists():
            logger.error(f"Configuration file not found: {config_path}")
            logger.info("Please copy config.example.yaml to config.yaml and customize it.")
            sys.exit(1)

        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        logger.info(f"Loaded configuration from {config_path}")
        return config

    def _setup_logging(self):
        """Setup logging based on config."""
        log_level = self.config.get('advanced', {}).get('log_level', 'INFO')
        logging.getLogger().setLevel(getattr(logging, log_level))

    def _flatten_queries(self) -> List[str]:
        """Flatten query categories into a single list."""
        queries = []
        query_config = self.config['search']['queries']

        for category, query_list in query_config.items():
            if isinstance(query_list, list):
                queries.extend(query_list)

        return queries

    def search_jobs(self) -> pd.DataFrame:
        """Execute job search based on configuration."""
        self._print_banner()

        search_config = self.config['search']
        filters = search_config['filters']

        # Get all queries and locations
        queries = self._flatten_queries()
        locations = search_config['locations']
        sites = search_config['sites']

        logger.info(f"Searching {len(queries)} queries across {len(locations)} locations")
        print(f"\n🔍 Searching for jobs...")
        print("=" * 80)

        rate_limit = self.config.get('advanced', {}).get('rate_limit_delay', 1)

        # Search each location
        for location in locations:
            print(f"\n📍 Searching in: {location}")

            for query in queries:
                try:
                    print(f"   - Query: {query}")

                    # Prepare scrape_jobs parameters
                    scrape_params = {
                        'site_name': sites,
                        'search_term': query,
                        'location': location,
                        'results_wanted': filters.get('results_per_query', 50),
                        'hours_old': filters.get('days_back', 30) * 24,
                        'country_indeed': filters.get('country_indeed', 'Switzerland'),
                        'linkedin_fetch_description': filters.get('linkedin_fetch_description', True),
                    }

                    # Add job types if specified
                    job_types = filters.get('job_types', [])
                    if len(job_types) == 1:
                        scrape_params['job_type'] = job_types[0]

                    jobs = scrape_jobs(**scrape_params)

                    if jobs is not None and len(jobs) > 0:
                        jobs['search_query'] = query
                        jobs['search_location'] = location
                        self.all_jobs.append(jobs)
                        print(f"      ✅ Found {len(jobs)} jobs")
                    else:
                        print(f"      ⚠️  No jobs found")

                    # Rate limiting
                    time.sleep(rate_limit)

                except Exception as e:
                    logger.error(f"Error searching '{query}' in {location}: {e}")
                    print(f"      ❌ Error: {e}")

                    # Retry logic
                    if self.config.get('advanced', {}).get('retry_failed_queries', False):
                        max_retries = self.config.get('advanced', {}).get('max_retries', 2)
                        for retry in range(max_retries):
                            try:
                                logger.info(f"Retrying {query} (attempt {retry + 1}/{max_retries})")
                                time.sleep(rate_limit * 2)
                                jobs = scrape_jobs(**scrape_params)
                                if jobs is not None and len(jobs) > 0:
                                    jobs['search_query'] = query
                                    jobs['search_location'] = location
                                    self.all_jobs.append(jobs)
                                    print(f"      ✅ Retry successful: Found {len(jobs)} jobs")
                                    break
                            except Exception as retry_error:
                                logger.error(f"Retry {retry + 1} failed: {retry_error}")

        # Combine all results
        if not self.all_jobs:
            logger.warning("No jobs found in any search!")
            return pd.DataFrame()

        jobs_df = pd.concat(self.all_jobs, ignore_index=True)

        # Remove duplicates
        dedup_fields = self.config.get('advanced', {}).get('deduplication_fields',
                                                            ['title', 'company', 'location'])
        jobs_df = jobs_df.drop_duplicates(subset=dedup_fields, keep='first')

        print(f"\n📊 Total jobs found: {len(jobs_df)}")
        return jobs_df

    def calculate_relevance_score(self, job_text: str) -> int:
        """Calculate relevance score based on configuration."""
        text = job_text.lower()
        score = 0

        scoring_config = self.config.get('relevance_scoring', {})
        categories = scoring_config.get('categories', {})

        for category_name, category_data in categories.items():
            weight = category_data.get('weight', 0)
            keywords = category_data.get('keywords', [])

            # Check if any keyword from this category appears in text
            if any(keyword.lower() in text for keyword in keywords):
                score += weight

        return score

    def filter_relevant_jobs(self, jobs_df: pd.DataFrame) -> pd.DataFrame:
        """Filter jobs based on relevance score."""
        if jobs_df.empty:
            return jobs_df

        print("\n🎯 Calculating relevance scores...")

        # Calculate relevance for each job
        jobs_df['relevance_score'] = jobs_df.apply(
            lambda row: self.calculate_relevance_score(
                f"{row.get('title', '')} {row.get('description', '')} "
                f"{row.get('company', '')} {row.get('location', '')}"
            ),
            axis=1
        )

        # Filter by minimum score
        min_score = self.config.get('relevance_scoring', {}).get('min_score', 10)
        relevant_jobs = jobs_df[jobs_df['relevance_score'] >= min_score].copy()
        relevant_jobs = relevant_jobs.sort_values('relevance_score', ascending=False)

        print(f"   ✅ {len(relevant_jobs)} relevant jobs (score >= {min_score})")
        print(f"   📈 Average relevance score: {relevant_jobs['relevance_score'].mean():.1f}")

        return relevant_jobs

    def save_results(self, jobs_df: pd.DataFrame, prefix: str = "jobs"):
        """Save results based on configuration."""
        if jobs_df.empty:
            logger.warning("No jobs to save!")
            return

        output_config = self.config.get('output', {})
        results_dir = Path(output_config.get('results_dir', '../results'))
        results_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        prefix = output_config.get('prefix', prefix)
        if output_config.get('include_timestamp', True):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{prefix}_{timestamp}"
        else:
            filename = prefix

        formats = output_config.get('formats', ['csv', 'xlsx'])

        # Save in requested formats
        for fmt in formats:
            filepath = results_dir / f"{filename}.{fmt}"

            if fmt == 'csv':
                jobs_df.to_csv(filepath, index=False)
                print(f"   💾 Saved to {filepath}")
            elif fmt == 'xlsx':
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    jobs_df.to_excel(writer, index=False, sheet_name='Jobs')

                    # Auto-adjust column widths if configured
                    if output_config.get('excel', {}).get('auto_adjust_columns', True):
                        worksheet = writer.sheets['Jobs']
                        for idx, col in enumerate(jobs_df.columns):
                            max_length = max(
                                jobs_df[col].astype(str).apply(len).max(),
                                len(col)
                            )
                            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)

                print(f"   💾 Saved to {filepath}")

    def _print_banner(self):
        """Print search banner with profile info."""
        profile = self.config.get('profile', {})
        name = profile.get('name', 'User')
        career_stage = profile.get('career_stage', 'Job Seeker')

        print("\n    ╔════════════════════════════════════════════════════════════════════╗")
        print(f"    ║          Job Search Tool - {name:<39}║")
        print( "    ║                                                                    ║")
        print(f"    ║  Career Stage: {career_stage:<50}║")

        if 'summary' in profile and profile['summary']:
            summary_lines = profile['summary'].strip().split('\n')
            for line in summary_lines[:3]:  # Show first 3 lines
                print(f"    ║  {line:<65}║")

        print( "    ╚════════════════════════════════════════════════════════════════════╝")

    def run(self):
        """Main execution method."""
        # Search for jobs
        all_jobs = self.search_jobs()

        if all_jobs.empty:
            logger.error("No jobs found. Exiting.")
            return

        # Save all jobs if configured
        if self.config.get('advanced', {}).get('save_all_jobs', True):
            print("\n💾 Saving all jobs...")
            self.save_results(all_jobs, prefix="all_jobs")

        # Filter and save relevant jobs
        if self.config.get('advanced', {}).get('save_relevant_jobs', True):
            relevant_jobs = self.filter_relevant_jobs(all_jobs)
            if not relevant_jobs.empty:
                print("\n💾 Saving relevant jobs...")
                self.save_results(relevant_jobs, prefix="relevant_jobs")

        print("\n✅ Job search completed!")
        print(f"   📁 Results saved to: {self.config.get('output', {}).get('results_dir', '../results')}")


def main():
    """Main entry point."""
    # Allow custom config path via command line
    config_path = sys.argv[1] if len(sys.argv) > 1 else "../config/config.yaml"

    searcher = JobSearcher(config_path)
    searcher.run()


if __name__ == "__main__":
    main()
