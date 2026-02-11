"""Shared YAML loading helpers with !include support.

This module centralizes YAML loading logic used by parser and validator,
so include path resolution is consistent across the project.
"""

from pathlib import Path
from typing import Any

import yaml
from yaml_include import Constructor


def load_yaml_with_include(file_path: str | Path) -> Any:
    """Load YAML file and resolve ``!include`` relative to the file directory.

    Args:
        file_path: YAML file path.

    Returns:
        Parsed YAML content.
    """
    path = Path(file_path).resolve()
    base_dir = path.parent

    # Isolated loader class avoids leaking global constructor registrations.
    class IncludeLoader(yaml.FullLoader):
        """YAML loader with local !include constructor."""

    IncludeLoader.add_constructor('!include', Constructor(base_dir=str(base_dir)))

    with path.open(encoding='utf-8') as file:
        return yaml.load(file, Loader=IncludeLoader)
