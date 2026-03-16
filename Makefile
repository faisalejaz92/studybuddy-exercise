.PHONY: dev sync test test-unit test-integration test-eval test-all check-env

# ============================================================================
# Development
# ============================================================================

# Start LangGraph dev server (default port 2024)
dev: check-env
	uv run langgraph dev

# Install dependencies
sync:
	uv sync

# Check that .env has been customized (not identical to .env.example)
check-env:
	@if [ -f .env ] && [ -f .env.example ] && cmp -s .env .env.example; then \
		echo ""; \
		echo "\033[1;31m ERROR: .env has not been configured\033[0m"; \
		echo ""; \
		echo "Edit .env and replace the placeholder values with your actual API keys."; \
		echo "See .env.example for the required variables."; \
		echo ""; \
		exit 1; \
	fi

# ============================================================================
# Testing
# ============================================================================

# Run tests (unit + integration, skips eval by default)
test:
	uv run pytest

# Run only unit tests (fast, no LLM)
test-unit:
	uv run pytest tests/unit -v

# Run only integration tests (mocked LLM)
test-integration:
	uv run pytest tests/integration -v

# Run eval tests (real LLM, slower)
test-eval:
	uv run pytest -m eval -v

# Run all tests including evals
test-all:
	uv run pytest -m "" -v
