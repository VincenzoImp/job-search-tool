"""Compatibility wrapper for pre-package Docker commands."""

from __future__ import annotations

import sys

from job_search_tool.main import main


if __name__ == "__main__":
    sys.exit(main())
