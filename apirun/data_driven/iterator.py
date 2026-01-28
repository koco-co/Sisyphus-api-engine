"""Data-Driven Testing Iterator.

This module implements test case generation from data sources.
Following Google Python Style Guide.
"""

from typing import Any, Dict, List, Optional
from copy import deepcopy

from apirun.core.models import TestCase, TestStep
from apirun.data_driven.data_source import DataSourceFactory, DataSourceReader


class DataDrivenIterator:
    """Iterator for data-driven testing.

    This iterator:
    - Reads data from data sources
    - Generates test cases for each data row
    - Injects data variables into test steps
    - Supports data filtering and batching

    Usage:
        iterator = DataDrivenIterator(test_case, data_source_config)
        for data_row, augmented_test_case in iterator:
            # Execute test with data_row
            pass
    """

    def __init__(
        self,
        test_case: TestCase,
        data_source_config: Dict[str, Any],
        variable_prefix: str = "",
    ):
        """Initialize DataDrivenIterator.

        Args:
            test_case: Base test case template
            data_source_config: Data source configuration
                - type: Data source type (csv/json/database)
                - file_path: File path (for CSV/JSON)
                - ... other source-specific configs
            variable_prefix: Prefix for injected variables (default: "")
        """
        self.base_test_case = test_case
        self.data_source_config = data_source_config
        self.variable_prefix = variable_prefix
        self._data_reader: Optional[DataSourceReader] = None
        self._data_rows: List[Dict[str, Any]] = []

        # Initialize data reader
        self._init_data_reader()

    def _init_data_reader(self) -> None:
        """Initialize data source reader.

        Raises:
            ValueError: If data source configuration is invalid
        """
        factory = DataSourceFactory()
        source_type = self.data_source_config.get("type")

        if not source_type:
            raise ValueError("Data source type is required")

        # Create reader based on source type
        if source_type == "csv":
            self._data_reader = factory.create_reader(
                "csv",
                file_path=self.data_source_config["file_path"],
                delimiter=self.data_source_config.get("delimiter", ","),
                encoding=self.data_source_config.get("encoding", "utf-8"),
                has_header=self.data_source_config.get("has_header", True),
            )
        elif source_type == "json":
            self._data_reader = factory.create_reader(
                "json",
                file_path=self.data_source_config["file_path"],
                data_key=self.data_source_config.get("data_key"),
            )
        elif source_type == "database":
            self._data_reader = factory.create_reader(
                "database",
                db_type=self.data_source_config["db_type"],
                connection_config=self.data_source_config["connection_config"],
                sql=self.data_source_config["sql"],
                params=self.data_source_config.get("params"),
            )
        else:
            raise ValueError(f"Unsupported data source type: {source_type}")

        # Read data
        self._data_rows = self._data_reader.read()

    def __iter__(self):
        """Get iterator for data-driven test cases.

        Yields:
            Tuple of (data_row, augmented_test_case)
        """
        for i, data_row in enumerate(self._data_rows):
            # Create augmented test case with data variables
            augmented_test_case = self._create_augmented_test_case(data_row, i)

            yield data_row, augmented_test_case

    def __len__(self) -> int:
        """Get number of data rows.

        Returns:
            Number of test iterations
        """
        return len(self._data_rows)

    def _create_augmented_test_case(
        self, data_row: Dict[str, Any], index: int
    ) -> TestCase:
        """Create augmented test case with data variables.

        Args:
            data_row: Data row from source
            index: Data row index

        Returns:
            Augmented test case with injected variables
        """
        # Deep copy test case to avoid modifying original
        augmented_test_case = deepcopy(self.base_test_case)

        # Add data variables to global config
        if augmented_test_case.config is None:
            from apirun.core.models import GlobalConfig

            augmented_test_case.config = GlobalConfig(
                name=self.base_test_case.name,
                description=self.base_test_case.description,
            )

        # Prepare data variables with prefix
        data_vars = {}
        for key, value in data_row.items():
            var_key = f"{self.variable_prefix}{key}" if self.variable_prefix else key
            data_vars[var_key] = value

        # Add special variables
        data_vars["_data_index"] = index
        data_vars["_data_total"] = len(self._data_rows)

        # Merge data variables with existing global variables
        existing_vars = augmented_test_case.config.variables or {}
        augmented_test_case.config.variables = {**existing_vars, **data_vars}

        # Update test case name with data index
        augmented_test_case.name = f"{self.base_test_case.name} [Data #{index + 1}]"

        return augmented_test_case

    def get_data_rows(self) -> List[Dict[str, Any]]:
        """Get all data rows.

        Returns:
            List of data rows
        """
        return self._data_rows

    def filter_data(self, filter_func: callable) -> None:
        """Filter data rows based on condition.

        Args:
            filter_func: Function that takes a data row and returns True to keep it
        """
        self._data_rows = [row for row in self._data_rows if filter_func(row)]

    def limit_data(self, count: int) -> None:
        """Limit number of data rows.

        Args:
            count: Maximum number of data rows to keep
        """
        self._data_rows = self._data_rows[:count]

    def batch_data(self, batch_size: int) -> List[List[Dict[str, Any]]]:
        """Split data into batches.

        Args:
            batch_size: Size of each batch

        Returns:
            List of data batches
        """
        batches = []
        for i in range(0, len(self._data_rows), batch_size):
            batches.append(self._data_rows[i : i + batch_size])
        return batches
