"""Database Executor for Sisyphus API Engine.

This module implements database operation execution (MySQL, PostgreSQL, SQLite).
Following Google Python Style Guide.
"""

import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
from sqlmodel import SQLModel, Session, create_engine, select, text
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError

from apirun.executor.step_executor import StepExecutor
from apirun.core.models import TestStep, PerformanceMetrics
from apirun.validation.engine import ValidationEngine


class DatabaseExecutor(StepExecutor):
    """Executor for database operations.

    Supports:
    - MySQL (via PyMySQL)
    - PostgreSQL (via psycopg2)
    - SQLite (built-in)
    - Prepared statements (SQL injection prevention)
    - Connection pooling
    - Transaction management
    - Query execution (SELECT, INSERT, UPDATE, DELETE, DDL)
    - Batch operations
    - Result validation

    Attributes:
        engine: Database engine instance
        session: Database session instance
        db_type: Database type (mysql/postgresql/sqlite)
        validation_engine: Validation engine instance
    """

    # Database type mapping
    DB_TYPE_MYSQL = "mysql"
    DB_TYPE_POSTGRESQL = "postgresql"
    DB_TYPE_SQLITE = "sqlite"

    def __init__(
        self,
        variable_manager,
        step: TestStep,
        timeout: int = 30,
        retry_times: int = 0,
        previous_results=None,
    ):
        """Initialize DatabaseExecutor.

        Args:
            variable_manager: Variable manager instance
            step: Test step to execute
            timeout: Default timeout in seconds
            retry_times: Default retry count
            previous_results: List of previous step results for dependency checking
        """
        super().__init__(variable_manager, step, timeout, retry_times, previous_results)
        self.engine = None
        self.session = None
        self.db_type = None
        self.connection_string = None
        self.validation_engine = ValidationEngine()

        # Extract database configuration from step
        self._parse_database_config()

    def _parse_database_config(self) -> None:
        """Parse database connection configuration from step.

        Raises:
            ValueError: If database configuration is invalid
        """
        if hasattr(self.step, "database"):
            db_config = self.step.database
        else:
            # Try to get from step config
            db_config = getattr(self.step, "connection", None)

        if not db_config:
            raise ValueError("Database configuration is required for database steps")

        # Build connection string
        self.db_type = db_config.get("type", "sqlite").lower()

        if self.db_type == self.DB_TYPE_MYSQL:
            # MySQL connection string
            # Format: mysql+pymysql://user:password@host:port/database
            host = db_config.get("host", "localhost")
            port = db_config.get("port", 3306)
            user = db_config.get("user", "root")
            password = db_config.get("password", "")
            database = db_config.get("database", "test")
            self.connection_string = (
                f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
                f"?charset=utf8mb4"
            )

        elif self.db_type == self.DB_TYPE_POSTGRESQL:
            # PostgreSQL connection string
            # Format: postgresql://user:password@host:port/database
            host = db_config.get("host", "localhost")
            port = db_config.get("port", 5432)
            user = db_config.get("user", "postgres")
            password = db_config.get("password", "")
            database = db_config.get("database", "test")
            self.connection_string = (
                f"postgresql://{user}:{password}@{host}:{port}/{database}"
            )

        elif self.db_type == self.DB_TYPE_SQLITE:
            # SQLite connection string
            # Format: sqlite:///path/to/database.db
            database_path = db_config.get("path", ":memory:")
            self.connection_string = f"sqlite:///{database_path}"

        else:
            raise ValueError(
                f"Unsupported database type: {self.db_type}. "
                f"Supported types: mysql, postgresql, sqlite"
            )

    def _connect(self) -> None:
        """Establish database connection with connection pool.

        Creates an engine and session for database operations.
        """
        # Create engine with connection pool
        self.engine = create_engine(
            self.connection_string,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=False,  # Set to True for SQL query logging
        )

        # Create session
        self.session = Session(self.engine)

    def _disconnect(self) -> None:
        """Close database connection and cleanup resources."""
        if self.session:
            self.session.close()
            self.session = None

        if self.engine:
            self.engine.dispose()
            self.engine = None

    def _execute_step(self, rendered_step: Dict[str, Any]) -> Any:
        """Execute database operation.

        Args:
            rendered_step: Rendered step data with:
                - operation: SQL operation type (query/exec/executemany)
                - sql: SQL statement or template
                - params: Query parameters (for prepared statements)
                - validations: List of validation rules
                - transaction: Whether to use transaction (default: True)

        Returns:
            Execution result with data, performance, and validations

        Raises:
            SQLAlchemyError: If database operation fails
            ValueError: If SQL statement is invalid
        """
        operation = rendered_step.get("operation", "query")
        sql = rendered_step.get("sql", "")
        params = rendered_step.get("params")
        validations = rendered_step.get("validations", [])
        use_transaction = rendered_step.get("transaction", True)

        if not sql:
            raise ValueError("SQL statement is required for database operations")

        # Connect to database
        self._connect()

        # Execute operation with performance tracking
        start_time = time.time()

        try:
            # Execute based on operation type
            if operation == "query":
                result_data = self._execute_query(sql, params)
            elif operation == "exec":
                result_data = self._execute_update(sql, params, use_transaction)
            elif operation == "executemany":
                result_data = self._execute_batch(sql, params, use_transaction)
            elif operation == "script":
                result_data = self._execute_script(sql, use_transaction)
            else:
                raise ValueError(f"Unsupported operation type: {operation}")

            end_time = time.time()

            # Calculate performance metrics
            total_time = (end_time - start_time) * 1000  # Convert to milliseconds

            performance = PerformanceMetrics(
                total_time=total_time,
                dns_time=0,  # Not applicable for database
                tcp_time=0,  # Not applicable for database
                tls_time=0,  # Not applicable for database
                server_time=total_time * 0.8,  # Server processing time
                download_time=total_time * 0.2,  # Data transfer time
                size=len(str(result_data)) if result_data else 0,
            )

        except SQLAlchemyError as e:
            self._disconnect()
            raise SQLAlchemyError(f"Database operation failed: {e}")

        # Run validations
        validation_results = []
        if validations and operation == "query":
            validation_results = self.validation_engine.validate(
                validations, {"data": result_data, "sql": sql}
            )

            # Check if any validation failed
            for val_result in validation_results:
                if not val_result["passed"]:
                    raise AssertionError(
                        f"Validation failed: {val_result['description']}"
                    )

        # Disconnect and return result
        self._disconnect()

        return type(
            "Result",
            (),
            {
                "data": result_data,
                "performance": performance,
                "validation_results": validation_results,
                "sql": sql,
                "operation": operation,
            },
        )()

    def _execute_query(
        self, sql: str, params: Optional[Union[Dict[str, Any], List[Any]]]
    ) -> List[Dict[str, Any]]:
        """Execute SELECT query.

        Args:
            sql: SQL SELECT statement
            params: Query parameters (dict or list)

        Returns:
            List of result rows as dictionaries

        Raises:
            SQLAlchemyError: If query execution fails
        """
        try:
            # Use prepared statement with parameters
            if params:
                if isinstance(params, dict):
                    # Named parameters
                    result = self.session.execute(text(sql), params)
                elif isinstance(params, list):
                    # Positional parameters
                    result = self.session.execute(text(sql), params)
                else:
                    result = self.session.execute(text(sql))
            else:
                result = self.session.execute(text(sql))

            # Convert to list of dictionaries
            columns = result.keys()
            rows = result.fetchall()

            return [dict(zip(columns, row)) for row in rows]

        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Query execution failed: {e}")

    def _execute_update(
        self,
        sql: str,
        params: Optional[Union[Dict[str, Any], List[Any]]],
        use_transaction: bool,
    ) -> Dict[str, Any]:
        """Execute INSERT/UPDATE/DELETE statement.

        Args:
            sql: SQL statement
            params: Statement parameters
            use_transaction: Whether to use transaction

        Returns:
            Dictionary with rowcount and lastrowid

        Raises:
            SQLAlchemyError: If execution fails
        """
        try:
            # Use prepared statement with parameters
            if params:
                if isinstance(params, dict):
                    result = self.session.execute(text(sql), params)
                elif isinstance(params, list):
                    result = self.session.execute(text(sql), params)
                else:
                    result = self.session.execute(text(sql))
            else:
                result = self.session.execute(text(sql))

            # Commit if using transaction
            if use_transaction:
                self.session.commit()

            # Return result info
            return {
                "rowcount": result.rowcount,
                "lastrowid": result.lastrowid if hasattr(result, "lastrowid") else None,
            }

        except SQLAlchemyError as e:
            if use_transaction:
                self.session.rollback()
            raise SQLAlchemyError(f"Update execution failed: {e}")

    def _execute_batch(
        self,
        sql: str,
        params_list: List[Union[Dict[str, Any], List[Any]]],
        use_transaction: bool,
    ) -> Dict[str, Any]:
        """Execute batch operation (INSERT/UPDATE multiple rows).

        Args:
            sql: SQL statement
            params_list: List of parameter sets
            use_transaction: Whether to use transaction

        Returns:
            Dictionary with total rowcount

        Raises:
            SQLAlchemyError: If batch execution fails
        """
        try:
            total_rowcount = 0

            # Execute each parameter set
            for params in params_list:
                if isinstance(params, dict):
                    result = self.session.execute(text(sql), params)
                elif isinstance(params, list):
                    result = self.session.execute(text(sql), params)
                else:
                    raise ValueError("Parameters must be dict or list")

                total_rowcount += result.rowcount

            # Commit if using transaction
            if use_transaction:
                self.session.commit()

            return {"rowcount": total_rowcount, "executed_count": len(params_list)}

        except SQLAlchemyError as e:
            if use_transaction:
                self.session.rollback()
            raise SQLAlchemyError(f"Batch execution failed: {e}")

    def _execute_script(self, script: str, use_transaction: bool) -> Dict[str, Any]:
        """Execute multiple SQL statements (DDL/DML script).

        Args:
            script: SQL script with multiple statements
            use_transaction: Whether to use transaction

        Returns:
            Dictionary with execution results

        Raises:
            SQLAlchemyError: If script execution fails
        """
        try:
            # Split script by semicolon and execute each statement
            statements = [s.strip() for s in script.split(";") if s.strip()]
            results = []

            for statement in statements:
                result = self.session.execute(text(statement))
                results.append(
                    {"statement": statement[:100], "rowcount": result.rowcount}
                )

            # Commit if using transaction
            if use_transaction:
                self.session.commit()

            return {"executed_count": len(statements), "results": results}

        except SQLAlchemyError as e:
            if use_transaction:
                self.session.rollback()
            raise SQLAlchemyError(f"Script execution failed: {e}")

    def __del__(self):
        """Cleanup resources on deletion."""
        self._disconnect()
