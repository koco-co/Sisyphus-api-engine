"""Test configuration for Sisyphus API Engine."""

from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        'markers',
        'unit: Unit tests',
    )
    config.addinivalue_line(
        'markers',
        'integration: Integration tests',
    )
    config.addinivalue_line(
        'markers',
        'slow: Slow running tests',
    )
