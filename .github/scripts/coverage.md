# Coverage Reporting

This project automatically generates and updates test coverage reports using GitHub Actions.

## How It Works

### Automated Coverage Updates

The project uses GitHub Actions to automatically:

1. **Run tests with coverage** on every push to `main` and `dev` branches
2. **Generate coverage badges** that show the current test coverage percentage
3. **Update the README.md** file with the latest coverage badge
4. **Upload coverage reports** to Codecov for detailed analysis

### Workflow Files

- **`.github/workflows/coverage.yml`** - Main coverage workflow that runs tests, generates badges, and updates README
- **`.github/workflows/tests.yaml`** - Basic test workflow for feature branches
- **`.github/scripts/update_readme.py`** - Python script that updates README with coverage badge

### Coverage Badge

The coverage badge appears in the README.md file right after the sponsor badge:

```
![Coverage](coverage.svg)
```

This badge is automatically updated whenever:
- Code is pushed to `main` or `dev` branches
- Test coverage changes
- The workflow runs successfully

### Local Development

To run coverage locally:

```bash
# Install dependencies
uv sync --dev

# Run tests with coverage
uv run coverage run -m pytest

# View coverage report
uv run coverage report

# Generate coverage badge (requires coverage-badge)
pip install coverage-badge
coverage-badge -o coverage.svg

# Update README with coverage badge
python .github/scripts/update_readme.py
```

### Coverage Reports

- **Terminal output**: `uv run coverage report`
- **HTML report**: Generated in `htmlcov/` directory
- **XML report**: Generated as `coverage.xml` for Codecov integration
- **Badge**: Generated as `coverage.svg` and displayed in README

### Codecov Integration

Coverage reports are automatically uploaded to Codecov for:
- Detailed coverage analysis
- Historical tracking
- Pull request coverage diff
- Coverage trends and insights

Visit your project's Codecov page to see detailed coverage reports and analytics.

## Configuration

Coverage is configured through:
- **`pyproject.toml`** - Test configuration and dependencies
- **`.coveragerc`** (if present) - Coverage-specific settings
- **GitHub Actions workflows** - Automated reporting setup

The current coverage target is to maintain high test coverage across all core functionality.
