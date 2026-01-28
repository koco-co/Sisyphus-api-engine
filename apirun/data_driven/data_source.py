"""Data Source Readers for Data-Driven Testing.

This module implements data source readers for CSV, JSON, and database.
Following Google Python Style Guide.
"""

import csv
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pathlib import Path


class DataSourceReader(ABC):
    """Abstract base class for data source readers.

    All data source readers should inherit from this class and implement
    the read() method.
    """

    @abstractmethod
    def read(self) -> List[Dict[str, Any]]:
        """Read data from the data source.

        Returns:
            List of data rows as dictionaries
        """
        raise NotImplementedError("Subclasses must implement read()")


class CsvDataSourceReader(DataSourceReader):
    """Reader for CSV data sources.

    Supports:
    - Reading CSV files
    - Custom delimiter
    - Encoding support
    - Header row detection
    """

    def __init__(
        self,
        file_path: str,
        delimiter: str = ",",
        encoding: str = "utf-8",
        has_header: bool = True,
    ):
        """Initialize CSV data source reader.

        Args:
            file_path: Path to CSV file
            delimiter: CSV delimiter (default: comma)
            encoding: File encoding (default: utf-8)
            has_header: Whether first row is header (default: True)
        """
        self.file_path = file_path
        self.delimiter = delimiter
        self.encoding = encoding
        self.has_header = has_header

    def read(self) -> List[Dict[str, Any]]:
        """Read data from CSV file.

        Returns:
            List of data rows as dictionaries

        Raises:
            FileNotFoundError: If CSV file does not exist
            ValueError: If CSV file is invalid
        """
        if not Path(self.file_path).exists():
            raise FileNotFoundError(f"CSV file not found: {self.file_path}")

        data = []

        try:
            with open(self.file_path, "r", encoding=self.encoding) as f:
                if self.has_header:
                    reader = csv.DictReader(f, delimiter=self.delimiter)
                    for row in reader:
                        # Convert empty strings to None
                        cleaned_row = {
                            k: (v if v != "" else None) for k, v in row.items()
                        }
                        data.append(cleaned_row)
                else:
                    reader = csv.reader(f, delimiter=self.delimiter)
                    for i, row in enumerate(reader):
                        # Use column indices as keys
                        data.append({f"col_{j}": val for j, val in enumerate(row)})

        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {e}")

        return data


class JsonDataSourceReader(DataSourceReader):
    """Reader for JSON data sources.

    Supports:
    - Reading JSON files
    - JSON array format
    - JSON object with data key
    """

    def __init__(self, file_path: str, data_key: Optional[str] = None):
        """Initialize JSON data source reader.

        Args:
            file_path: Path to JSON file
            data_key: Key to extract data from (optional)
                     If not provided, expects root to be an array
        """
        self.file_path = file_path
        self.data_key = data_key

    def read(self) -> List[Dict[str, Any]]:
        """Read data from JSON file.

        Returns:
            List of data rows as dictionaries

        Raises:
            FileNotFoundError: If JSON file does not exist
            ValueError: If JSON file is invalid
        """
        if not Path(self.file_path).exists():
            raise FileNotFoundError(f"JSON file not found: {self.file_path}")

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            # Extract data based on data_key
            if self.data_key:
                if not isinstance(json_data, dict):
                    raise ValueError(
                        f"Expected JSON object when data_key is provided, got {type(json_data)}"
                    )
                if self.data_key not in json_data:
                    raise ValueError(f"Key '{self.data_key}' not found in JSON")
                data = json_data[self.data_key]
            else:
                data = json_data

            # Ensure data is a list
            if not isinstance(data, list):
                raise ValueError(f"Expected data to be a list, got {type(data)}")

            return data

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to read JSON file: {e}")


class DatabaseDataSourceReader(DataSourceReader):
    """Reader for database data sources.

    Supports:
    - MySQL, PostgreSQL, SQLite
    - Custom SQL queries
    - Parameterized queries
    """

    def __init__(
        self,
        db_type: str,
        connection_config: Dict[str, Any],
        sql: str,
        params: Optional[Dict[str, Any]] = None,
    ):
        """Initialize database data source reader.

        Args:
            db_type: Database type (mysql/postgresql/sqlite)
            connection_config: Database connection configuration
            sql: SQL query to fetch data
            params: Query parameters (optional)
        """
        self.db_type = db_type
        self.connection_config = connection_config
        self.sql = sql
        self.params = params

    def read(self) -> List[Dict[str, Any]]:
        """Read data from database.

        Returns:
            List of data rows as dictionaries

        Raises:
            ValueError: If database connection or query fails
        """
        from sqlmodel import Session, create_engine, select, text

        # Build connection string
        if self.db_type == "mysql":
            config = self.connection_config
            conn_str = (
                f"mysql+pymysql://{config['user']}:{config['password']}@"
                f"{config['host']}:{config.get('port', 3306)}/{config['database']}"
                f"?charset=utf8mb4"
            )
        elif self.db_type == "postgresql":
            config = self.connection_config
            conn_str = (
                f"postgresql://{config['user']}:{config['password']}@"
                f"{config['host']}:{config.get('port', 5432)}/{config['database']}"
            )
        elif self.db_type == "sqlite":
            conn_str = f"sqlite:///{self.connection_config['path']}"
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

        # Create engine and session
        engine = create_engine(conn_str)
        session = Session(engine)

        try:
            # Execute query
            if self.params:
                result = session.execute(text(self.sql), self.params)
            else:
                result = session.execute(text(self.sql))

            # Convert to list of dictionaries
            columns = result.keys()
            rows = result.fetchall()
            data = [dict(zip(columns, row)) for row in rows]

            return data

        except Exception as e:
            raise ValueError(f"Failed to read from database: {e}")
        finally:
            session.close()
            engine.dispose()


class DataSourceFactory:
    """Factory for creating data source readers.

    Usage:
        factory = DataSourceFactory()
        reader = factory.create_reader("csv", file_path="data.csv")
        data = reader.read()
    """

    def create_reader(
        self, source_type: str, **kwargs
    ) -> DataSourceReader:
        """Create a data source reader.

        Args:
            source_type: Type of data source (csv/json/database)
            **kwargs: Arguments for the specific reader

        Returns:
            DataSourceReader instance

        Raises:
            ValueError: If source type is not supported
        """
        source_type = source_type.lower()

        if source_type == "csv":
            return CsvDataSourceReader(
                file_path=kwargs["file_path"],
                delimiter=kwargs.get("delimiter", ","),
                encoding=kwargs.get("encoding", "utf-8"),
                has_header=kwargs.get("has_header", True),
            )
        elif source_type == "json":
            return JsonDataSourceReader(
                file_path=kwargs["file_path"], data_key=kwargs.get("data_key")
            )
        elif source_type == "database":
            return DatabaseDataSourceReader(
                db_type=kwargs["db_type"],
                connection_config=kwargs["connection_config"],
                sql=kwargs["sql"],
                params=kwargs.get("params"),
            )
        else:
            raise ValueError(
                f"Unsupported data source type: {source_type}. "
                f"Supported types: csv, json, database"
            )
