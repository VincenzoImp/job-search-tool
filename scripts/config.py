"""
Configuration loader for Switzerland Jobs Search.

Loads settings from YAML configuration file with fallback to defaults.
Provides type-safe access to all configuration values.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# Base directory is the project root (parent of scripts/)
BASE_DIR = Path(__file__).parent.parent.resolve()
CONFIG_FILE = BASE_DIR / "config" / "settings.yaml"


@dataclass
class SearchConfig:
    """Search-related configuration."""

    # Core search parameters
    results_wanted: int = 50
    hours_old: int = 720
    job_types: list[str] = field(default_factory=lambda: ["fulltime"])
    sites: list[str] = field(
        default_factory=lambda: ["indeed", "linkedin", "glassdoor"]
    )
    locations: list[str] = field(
        default_factory=lambda: [
            "Zurich, Switzerland",
            "Switzerland",
        ]
    )

    # JobSpy core parameters
    distance: int = 50  # Search radius in miles
    is_remote: bool = False  # Filter for remote-only jobs
    easy_apply: bool | None = None  # Filter for easy apply jobs
    offset: int = 0  # Start search from offset

    # Output format parameters
    enforce_annual_salary: bool = True  # Convert all salaries to yearly
    description_format: str = "markdown"  # markdown, html, plain
    verbose: int = 1  # 0=errors, 1=warnings, 2=all logs

    # LinkedIn-specific parameters
    linkedin_fetch_description: bool = True  # Fetch full descriptions (slower)
    linkedin_company_ids: list[int] | None = None  # Filter by company IDs

    # Google Jobs-specific parameters
    google_search_term: str | None = None  # Special syntax for Google Jobs

    # Network/Proxy parameters
    proxies: list[str] | None = None  # Proxy list for rate limiting
    ca_cert: str | None = None  # CA certificate for proxies
    user_agent: str | None = None  # Custom user agent


@dataclass
class ScoringConfig:
    """Relevance scoring configuration."""

    threshold: int = 10
    weights: dict[str, int] = field(
        default_factory=lambda: {
            "blockchain": 20,
            "phd_research": 18,
            "data_analysis": 15,
            "summer_programs": 15,
            "security": 12,
            "academic": 12,
            "eth_zurich": 10,
            "social_network": 10,
            "tech_skills": 8,
            "open_source": 8,
            "teaching": 6,
            "computer_science": 5,
            "location_bonus": 5,
            "hackathon": 5,
        }
    )
    keywords: dict[str, list[str]] = field(
        default_factory=lambda: {
            "phd": [
                "phd",
                "doctoral",
                "research",
                "postdoc",
                "scientist",
                "researcher",
                "visiting",
                "academic",
            ],
            "blockchain": [
                "blockchain",
                "crypto",
                "distributed",
                "web3",
                "ethereum",
                "bitcoin",
                "smart contract",
                "defi",
                "consensus",
                "nostr",
                "decentralized",
                "peer-to-peer",
                "p2p",
            ],
            "data": [
                "data",
                "analysis",
                "analytics",
                "behavior",
                "behavioral",
                "network analysis",
                "visualization",
                "mining",
                "transaction",
                "pattern",
                "graph",
                "user behavior",
            ],
            "security": [
                "security",
                "privacy",
                "cryptography",
                "encryption",
                "zero-knowledge",
                "zk",
                "homomorphic",
                "usenix",
            ],
            "social": [
                "social network",
                "telegram",
                "community",
                "user engagement",
                "monetization",
                "social media",
            ],
            "tech": [
                "python",
                "typescript",
                "javascript",
                "react",
                "node.js",
                "postgresql",
                "mongodb",
                "docker",
                "c++",
                "solidity",
            ],
            "summer": ["summer", "2026", "intern", "temporary", "short-term"],
            "academic": [
                "eth zurich",
                "epfl",
                "university",
                "institute",
                "academia",
                "sapienza",
            ],
        }
    )


@dataclass
class ParallelConfig:
    """Parallelism configuration."""

    max_workers: int = 5


@dataclass
class RetryConfig:
    """Retry configuration for handling rate limits."""

    max_attempts: int = 3
    base_delay: float = 2.0
    backoff_factor: float = 2.0


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    file: str = "logs/search.log"
    max_size_mb: int = 10
    backup_count: int = 5


@dataclass
class OutputConfig:
    """Output paths configuration."""

    results_dir: str = "results"
    data_dir: str = "data"
    database_file: str = "jobs.db"
    save_csv: bool = True  # Save CSV files
    save_excel: bool = True  # Save Excel files


@dataclass
class ProfileConfig:
    """User profile information for display."""

    name: str = "Vincenzo Imperati"
    current_position: str = "PhD Candidate @ Sapienza University (Nov 2023 - Oct 2026)"
    visiting_position: str = "Visiting PhD @ ETH Zurich (Sep 2025 - Oct 2026)"
    research_focus: str = "User behavior in distributed systems & blockchains"
    publication: str = "USENIX Security (Telegram conspiracy channels)"
    grant: str = "OpenSats Grant: Nostr protocol development"
    skills: str = "Python, TypeScript, C++, React, Data Analysis"
    target: str = "Research, Software Engineering, Summer 2026 positions"


@dataclass
class SchedulerConfig:
    """Scheduler configuration for automated periodic execution."""

    enabled: bool = False  # If False, single-shot mode (backward compatible)
    interval_hours: int = 24  # Run every N hours
    run_on_startup: bool = True  # Execute immediately on startup
    retry_on_failure: bool = True  # Retry if search fails
    retry_delay_minutes: int = 30  # Wait time before retry


@dataclass
class TelegramConfig:
    """Telegram notification configuration."""

    enabled: bool = False
    bot_token: str = ""  # From @BotFather
    chat_ids: list[str] = field(default_factory=list)  # Recipients
    send_summary: bool = True  # Send run summary
    min_score_for_notification: int = 0  # Min score to include in notifications
    max_jobs_in_message: int = 10  # Max jobs to show in message


@dataclass
class NotificationsConfig:
    """Notifications configuration."""

    enabled: bool = False
    telegram: TelegramConfig = field(default_factory=TelegramConfig)


@dataclass
class Config:
    """Main configuration class containing all settings."""

    search: SearchConfig = field(default_factory=SearchConfig)
    queries: dict[str, list[str]] = field(default_factory=dict)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    parallel: ParallelConfig = field(default_factory=ParallelConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    profile: ProfileConfig = field(default_factory=ProfileConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    notifications: NotificationsConfig = field(default_factory=NotificationsConfig)

    @property
    def results_path(self) -> Path:
        """Get absolute path to results directory."""
        return BASE_DIR / self.output.results_dir

    @property
    def data_path(self) -> Path:
        """Get absolute path to data directory."""
        return BASE_DIR / self.output.data_dir

    @property
    def database_path(self) -> Path:
        """Get absolute path to SQLite database."""
        return self.data_path / self.output.database_file

    @property
    def log_path(self) -> Path:
        """Get absolute path to log file."""
        return BASE_DIR / self.logging.file

    def get_all_queries(self) -> list[str]:
        """Get flattened list of all search queries."""
        all_queries = []
        for category_queries in self.queries.values():
            all_queries.extend(category_queries)
        return all_queries


def _load_yaml() -> dict[str, Any]:
    """Load YAML configuration file."""
    if not CONFIG_FILE.exists():
        return {}

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _parse_search_config(data: dict[str, Any]) -> SearchConfig:
    """Parse search configuration from dict."""
    search_data = data.get("search", {})
    return SearchConfig(
        # Core search parameters
        results_wanted=search_data.get("results_wanted", 50),
        hours_old=search_data.get("hours_old", 720),
        job_types=search_data.get("job_types", ["fulltime"]),
        sites=search_data.get("sites", ["indeed", "linkedin", "glassdoor"]),
        locations=search_data.get(
            "locations",
            ["Zurich, Switzerland", "Switzerland"],
        ),
        # JobSpy core parameters
        distance=search_data.get("distance", 50),
        is_remote=search_data.get("is_remote", False),
        easy_apply=search_data.get("easy_apply"),
        offset=search_data.get("offset", 0),
        # Output format parameters
        enforce_annual_salary=search_data.get("enforce_annual_salary", True),
        description_format=search_data.get("description_format", "markdown"),
        verbose=search_data.get("verbose", 1),
        # LinkedIn-specific parameters
        linkedin_fetch_description=search_data.get("linkedin_fetch_description", True),
        linkedin_company_ids=search_data.get("linkedin_company_ids"),
        # Google Jobs-specific parameters
        google_search_term=search_data.get("google_search_term"),
        # Network/Proxy parameters
        proxies=search_data.get("proxies"),
        ca_cert=search_data.get("ca_cert"),
        user_agent=search_data.get("user_agent"),
    )


def _parse_scoring_config(data: dict[str, Any]) -> ScoringConfig:
    """Parse scoring configuration from dict."""
    scoring_data = data.get("scoring", {})
    config = ScoringConfig()

    if "threshold" in scoring_data:
        config.threshold = scoring_data["threshold"]
    if "weights" in scoring_data:
        config.weights.update(scoring_data["weights"])
    if "keywords" in scoring_data:
        config.keywords.update(scoring_data["keywords"])

    return config


def _parse_parallel_config(data: dict[str, Any]) -> ParallelConfig:
    """Parse parallel configuration from dict."""
    parallel_data = data.get("parallel", {})
    return ParallelConfig(
        max_workers=parallel_data.get("max_workers", 5),
    )


def _parse_retry_config(data: dict[str, Any]) -> RetryConfig:
    """Parse retry configuration from dict."""
    retry_data = data.get("retry", {})
    return RetryConfig(
        max_attempts=retry_data.get("max_attempts", 3),
        base_delay=retry_data.get("base_delay", 2.0),
        backoff_factor=retry_data.get("backoff_factor", 2.0),
    )


def _parse_logging_config(data: dict[str, Any]) -> LoggingConfig:
    """Parse logging configuration from dict."""
    logging_data = data.get("logging", {})
    return LoggingConfig(
        level=logging_data.get("level", "INFO"),
        file=logging_data.get("file", "logs/search.log"),
        max_size_mb=logging_data.get("max_size_mb", 10),
        backup_count=logging_data.get("backup_count", 5),
    )


def _parse_output_config(data: dict[str, Any]) -> OutputConfig:
    """Parse output configuration from dict."""
    output_data = data.get("output", {})
    return OutputConfig(
        results_dir=output_data.get("results_dir", "results"),
        data_dir=output_data.get("data_dir", "data"),
        database_file=output_data.get("database_file", "jobs.db"),
        save_csv=output_data.get("save_csv", True),
        save_excel=output_data.get("save_excel", True),
    )


def _parse_profile_config(data: dict[str, Any]) -> ProfileConfig:
    """Parse profile configuration from dict."""
    profile_data = data.get("profile", {})
    defaults = ProfileConfig()
    return ProfileConfig(
        name=profile_data.get("name", defaults.name),
        current_position=profile_data.get(
            "current_position", defaults.current_position
        ),
        visiting_position=profile_data.get(
            "visiting_position", defaults.visiting_position
        ),
        research_focus=profile_data.get("research_focus", defaults.research_focus),
        publication=profile_data.get("publication", defaults.publication),
        grant=profile_data.get("grant", defaults.grant),
        skills=profile_data.get("skills", defaults.skills),
        target=profile_data.get("target", defaults.target),
    )


def _parse_scheduler_config(data: dict[str, Any]) -> SchedulerConfig:
    """Parse scheduler configuration from dict."""
    scheduler_data = data.get("scheduler", {})
    return SchedulerConfig(
        enabled=scheduler_data.get("enabled", False),
        interval_hours=scheduler_data.get("interval_hours", 24),
        run_on_startup=scheduler_data.get("run_on_startup", True),
        retry_on_failure=scheduler_data.get("retry_on_failure", True),
        retry_delay_minutes=scheduler_data.get("retry_delay_minutes", 30),
    )


def _parse_telegram_config(data: dict[str, Any]) -> TelegramConfig:
    """Parse Telegram configuration from dict."""
    telegram_data = data.get("telegram", {})
    return TelegramConfig(
        enabled=telegram_data.get("enabled", False),
        bot_token=telegram_data.get("bot_token", ""),
        chat_ids=telegram_data.get("chat_ids", []),
        send_summary=telegram_data.get("send_summary", True),
        min_score_for_notification=telegram_data.get("min_score_for_notification", 0),
        max_jobs_in_message=telegram_data.get("max_jobs_in_message", 10),
    )


def _parse_notifications_config(data: dict[str, Any]) -> NotificationsConfig:
    """Parse notifications configuration from dict."""
    notifications_data = data.get("notifications", {})
    return NotificationsConfig(
        enabled=notifications_data.get("enabled", False),
        telegram=_parse_telegram_config(notifications_data),
    )


def _parse_queries(data: dict[str, Any]) -> dict[str, list[str]]:
    """Parse search queries from dict."""
    queries_data = data.get("queries", {})
    if not queries_data:
        # Default queries if none provided
        return {
            "core_research": [
                "distributed systems researcher",
                "blockchain researcher",
                "network analysis",
                "social network analysis",
                "user behavior analysis",
            ],
            "blockchain_web3": [
                "blockchain engineer",
                "web3 developer",
                "smart contracts",
                "cryptocurrency",
                "Nostr protocol",
                "decentralized systems",
            ],
            "phd_research": [
                "PhD researcher computer science",
                "postdoc distributed systems",
                "research scientist blockchain",
                "visiting researcher",
            ],
            "data_science": [
                "data scientist",
                "data analyst",
                "data engineer",
                "behavioral analytics",
                "network data analysis",
            ],
            "software_engineering": [
                "backend engineer Python",
                "full-stack TypeScript",
                "software engineer blockchain",
                "open source developer",
            ],
            "security_privacy": [
                "security researcher",
                "privacy engineer",
                "cryptography",
                "zero knowledge proofs",
            ],
            "academic_teaching": [
                "teaching assistant computer science",
                "university lecturer",
                "research associate",
            ],
            "technologies": [
                "Python developer",
                "React developer",
                "Node.js",
                "PostgreSQL",
                "Docker",
            ],
            "summer_temporary": [
                "summer internship 2026",
                "research internship",
                "temporary researcher",
            ],
        }
    return queries_data


def load_config() -> Config:
    """
    Load configuration from YAML file with fallback to defaults.

    Returns:
        Config object with all settings.
    """
    data = _load_yaml()

    config = Config(
        search=_parse_search_config(data),
        queries=_parse_queries(data),
        scoring=_parse_scoring_config(data),
        parallel=_parse_parallel_config(data),
        retry=_parse_retry_config(data),
        logging=_parse_logging_config(data),
        output=_parse_output_config(data),
        profile=_parse_profile_config(data),
        scheduler=_parse_scheduler_config(data),
        notifications=_parse_notifications_config(data),
    )

    # Ensure directories exist
    config.results_path.mkdir(parents=True, exist_ok=True)
    config.data_path.mkdir(parents=True, exist_ok=True)
    config.log_path.parent.mkdir(parents=True, exist_ok=True)

    return config


# Singleton instance for easy access
_config: Config | None = None


def get_config() -> Config:
    """
    Get configuration singleton.

    Returns:
        Config object with all settings.
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> Config:
    """
    Force reload configuration from file.

    Returns:
        Fresh Config object.
    """
    global _config
    _config = load_config()
    return _config
