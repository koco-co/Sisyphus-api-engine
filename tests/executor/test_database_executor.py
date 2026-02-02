"""Unit tests for DatabaseExecutor.

Tests the database step executor functionality, including:
- Connection string parsing
- Multiple database types (MySQL, PostgreSQL, SQLite)
- Query execution
- Prepared statements
- Error handling

Following Google Python Style Guide.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from apirun.executor.database_executor import DatabaseExecutor
from apirun.core.models import TestStep, StepResult
from apirun.core.variable_manager import VariableManager


class TestDatabaseExecutor:
    """Test cases for DatabaseExecutor class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.variable_manager = VariableManager()
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db_path = self.temp_db_file.name

    def teardown_method(self):
        """Cleanup test fixtures."""
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)

    def test_initialization_with_sqlite(self):
        """Test initialization with SQLite database."""
        step = TestStep(
            name="Database Test",
            type="database",
            database={
                "type": "sqlite",
                "path": self.temp_db_path
            },
            sql="SELECT 1"
        )

        executor = DatabaseExecutor(
            variable_manager=self.variable_manager,
            step=step,
            timeout=30
        )

        assert executor.db_type == "sqlite"
        assert executor.connection_string is not None
        assert self.temp_db_path in executor.connection_string

    def test_connection_string_mysql(self):
        """Test MySQL connection string parsing."""
        step = TestStep(
            name="MySQL Test",
            type="database",
            database={
                "type": "mysql",
                "host": "localhost",
                "port": 3306,
                "user": "testuser",
                "password": "testpass",
                "database": "testdb"
            },
            sql="SELECT 1"
        )

        executor = DatabaseExecutor(
            variable_manager=self.variable_manager,
            step=step,
            timeout=30
        )

        assert "mysql+pymysql://" in executor.connection_string
        assert "testuser:testpass" in executor.connection_string
        assert "localhost:3306" in executor.connection_string
        assert "testdb" in executor.connection_string

    def test_connection_string_postgresql(self):
        """Test PostgreSQL connection string parsing."""
        step = TestStep(
            name="PostgreSQL Test",
            type="database",
            database={
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "user": "testuser",
                "password": "testpass",
                "database": "testdb"
            },
            sql="SELECT 1"
        )

        executor = DatabaseExecutor(
            variable_manager=self.variable_manager,
            step=step,
            timeout=30
        )

        assert "postgresql://" in executor.connection_string
        assert "testuser:testpass" in executor.connection_string
        assert "localhost:5432" in executor.connection_string
        assert "testdb" in executor.connection_string

    def test_missing_database_config(self):
        """Test error handling when database config is missing."""
        step = TestStep(
            name="Invalid Database Test",
            type="database",
            sql="SELECT 1"
        )

        with pytest.raises(ValueError, match="Database configuration is required"):
            DatabaseExecutor(
                variable_manager=self.variable_manager,
                step=step,
                timeout=30
            )

    def test_database_type_validation(self):
        """Test supported database types."""
        valid_types = ["mysql", "postgresql", "sqlite", "MySQL", "PostgreSQL", "SQLite"]

        for db_type in valid_types:
            step = TestStep(
                name=f"Test {db_type}",
                type="database",
                database={
                    "type": db_type,
                    "path": self.temp_db_path if db_type.lower() == "sqlite" else "test"
                },
                sql="SELECT 1"
            )

            executor = DatabaseExecutor(
                variable_manager=self.variable_manager,
                step=step,
                timeout=30
            )

            assert executor.db_type == db_type.lower()

    def test_query_parameterization(self):
        """Test query with parameters."""
        step = TestStep(
            name="Parameterized Query",
            type="database",
            database={
                "type": "sqlite",
                "path": self.temp_db_path
            },
            operation="select",
            sql="SELECT * FROM users WHERE id = :user_id",
            params={
                "user_id": 123
            }
        )

        executor = DatabaseExecutor(
            variable_manager=self.variable_manager,
            step=step,
            timeout=30
        )

        assert executor.step.params == {"user_id": 123}

    def test_different_operations(self):
        """Test different database operations."""
        operations = ["select", "insert", "update", "delete", "execute", "script"]

        for operation in operations:
            step = TestStep(
                name=f"Test {operation}",
                type="database",
                database={
                    "type": "sqlite",
                    "path": self.temp_db_path
                },
                operation=operation,
                sql="SELECT 1" if operation == "select" else "INSERT INTO test VALUES (1)"
            )

            executor = DatabaseExecutor(
                variable_manager=self.variable_manager,
                step=step,
                timeout=30
            )

            assert executor.step.operation == operation

    def test_variable_rendering_in_query(self):
        """Test variable rendering in database queries."""
        self.variable_manager.set_variable("table_name", "users")
        self.variable_manager.set_variable("user_id", 123)

        step = TestStep(
            name="Variable Rendering Test",
            type="database",
            database={
                "type": "sqlite",
                "path": self.temp_db_path
            },
            sql="SELECT * FROM ${table_name} WHERE id = ${user_id}"
        )

        executor = DatabaseExecutor(
            variable_manager=self.variable_manager,
            step=step,
            timeout=30
        )

        # Query should contain variables
        assert "${table_name}" in executor.step.sql
        assert "${user_id}" in executor.step.sql

    def test_connection_with_ssl_options(self):
        """Test database connection with SSL options (config stored but not used in connection string)."""
        step = TestStep(
            name="SSL Test",
            type="database",
            database={
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "user": "testuser",
                "password": "testpass",
                "database": "testdb",
                "sslmode": "require",
                "sslrootcert": "/path/to/cert.pem"
            },
            sql="SELECT 1"
        )

        executor = DatabaseExecutor(
            variable_manager=self.variable_manager,
            step=step,
            timeout=30
        )

        # SSL options are stored in database config
        assert executor.step.database["sslmode"] == "require"
        assert executor.step.database["sslrootcert"] == "/path/to/cert.pem"
        # Basic connection string is built
        assert executor.connection_string is not None

    def test_connection_pooling_parameters(self):
        """Test connection pooling parameters."""
        step = TestStep(
            name="Connection Pooling Test",
            type="database",
            database={
                "type": "mysql",
                "host": "localhost",
                "port": 3306,
                "user": "testuser",
                "password": "testpass",
                "database": "testdb",
                "pool_size": 10,
                "max_overflow": 20,
                "pool_timeout": 30,
                "pool_recycle": 3600
            },
            sql="SELECT 1"
        )

        executor = DatabaseExecutor(
            variable_manager=self.variable_manager,
            step=step,
            timeout=30
        )

        # Connection string should be built
        assert executor.connection_string is not None
        assert "mysql+pymysql://" in executor.connection_string

    def test_validations_in_database_step(self):
        """Test database step with validation rules."""
        from unittest.mock import Mock

        step = TestStep(
            name="Database with Validation",
            type="database",
            database={
                "type": "sqlite",
                "path": self.temp_db_path
            },
            sql="SELECT COUNT(*) as count FROM users",
            validations=[
                Mock(type="gt", path="$.count", expect=0, description="Count should be positive")
            ]
        )

        executor = DatabaseExecutor(
            variable_manager=self.variable_manager,
            step=step,
            timeout=30
        )

        assert executor.step.validations is not None
        assert len(executor.step.validations) == 1

    def test_extractors_in_database_step(self):
        """Test database step with variable extraction."""
        step = TestStep(
            name="Database with Extraction",
            type="database",
            database={
                "type": "sqlite",
                "path": self.temp_db_path
            },
            sql="SELECT user_id, username FROM users LIMIT 1",
            extractors=[
                Mock(name="user_id", path="$.user_id", from_="response"),
                Mock(name="username", path="$.username", from_="response")
            ]
        )

        executor = DatabaseExecutor(
            variable_manager=self.variable_manager,
            step=step,
            timeout=30
        )

        assert executor.step.extractors is not None
        assert len(executor.step.extractors) == 2

    def test_timeout_configuration(self):
        """Test timeout configuration for database operations."""
        step = TestStep(
            name="Timeout Test",
            type="database",
            database={
                "type": "sqlite",
                "path": self.temp_db_path
            },
            sql="SELECT 1"
        )

        # Test with default timeout
        executor1 = DatabaseExecutor(
            variable_manager=self.variable_manager,
            step=step,
            timeout=30
        )

        assert executor1.timeout == 30

        # Test with custom timeout
        executor2 = DatabaseExecutor(
            variable_manager=self.variable_manager,
            step=step,
            timeout=60
        )

        assert executor2.timeout == 60

    def test_retry_configuration(self):
        """Test retry configuration for database operations."""
        step = TestStep(
            name="Retry Test",
            type="database",
            database={
                "type": "sqlite",
                "path": self.temp_db_path
            },
            sql="SELECT 1"
        )

        executor = DatabaseExecutor(
            variable_manager=self.variable_manager,
            step=step,
            timeout=30,
            retry_times=3
        )

        assert executor.retry_times == 3

    def test_multiple_statements_in_script(self):
        """Test executing multiple SQL statements as a script."""
        script = """
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        INSERT INTO test_table VALUES (1, 'test');
        SELECT * FROM test_table;
        DROP TABLE test_table;
        """

        step = TestStep(
            name="Script Execution",
            type="database",
            database={
                "type": "sqlite",
                "path": self.temp_db_path
            },
            operation="script",
            sql=script.strip()
        )

        executor = DatabaseExecutor(
            variable_manager=self.variable_manager,
            step=step,
            timeout=30
        )

        assert executor.step.operation == "script"
        assert "CREATE TABLE" in executor.step.sql
        assert "INSERT INTO" in executor.step.sql
        assert "DROP TABLE" in executor.step.sql
