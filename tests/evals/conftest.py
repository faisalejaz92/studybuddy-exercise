"""Pytest configuration for eval tests.

Eval tests require API keys from .env. This conftest loads the environment
at test execution time (not collection time) to avoid polluting the
environment for non-eval tests.
"""

import pytest
from dotenv import load_dotenv


@pytest.fixture(scope="session", autouse=True)
def load_env_for_evals():
    """Load .env for eval tests that need API keys."""
    load_dotenv()
