"""Template Functions for Sisyphus API Engine.

This module provides built-in functions that can be used in variable templates.
These functions are automatically available in all template expressions.

Available functions:
- random(): Generate random integer
- random_str(): Generate random string
- uuid(): Generate UUID
- timestamp(): Generate current timestamp
- date(): Generate formatted date string
- now(): Generate current datetime
- db_query(): Execute database query (requires database config in variables)

Following Google Python Style Guide.
"""

import random
import re
import string
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


def random_int(min_val: int = 0, max_val: int = 1000000) -> int:
    """Generate a random integer.

    Args:
        min_val: Minimum value (default: 0)
        max_val: Maximum value (default: 1000000)

    Returns:
        Random integer between min_val and max_val

    Examples:
        ${random()} -> 123456
        ${random(1, 100)} -> 42
    """
    return random.randint(min_val, max_val)


def random_str(length: int = 8, chars: Optional[str] = None) -> str:
    """Generate a random string.

    Args:
        length: Length of the string (default: 8)
        chars: Character set to use (default: alphanumeric)

    Returns:
        Random string of specified length

    Examples:
        ${random_str()} -> "aB3xK9mZ"
        ${random_str(16)} -> "xY7mP2kL9qR4nT3j"
        ${random_str(4, 'ABC')} -> "ABCA"
    """
    if chars is None:
        chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def uuid_str() -> str:
    """Generate a random UUID string (without dashes).

    Returns:
        UUID string without dashes

    Examples:
        ${uuid()} -> "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
    """
    return uuid.uuid4().hex


def uuid4() -> str:
    """Generate a standard UUID v4 string (with dashes).

    Returns:
        Standard UUID v4 string

    Examples:
        ${uuid4()} -> "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
    """
    return str(uuid.uuid4())


def timestamp() -> int:
    """Generate current Unix timestamp.

    Returns:
        Current Unix timestamp (seconds since epoch)

    Examples:
        ${timestamp()} -> 1706508000
    """
    return int(datetime.now().timestamp())


def timestamp_ms() -> int:
    """Generate current Unix timestamp in milliseconds.

    Returns:
        Current Unix timestamp in milliseconds

    Examples:
        ${timestamp_ms()} -> 1706508000000
    """
    return int(datetime.now().timestamp() * 1000)


def timestamp_us() -> int:
    """Generate current Unix timestamp in microseconds.

    Returns:
        Current Unix timestamp in microseconds

    Examples:
        ${timestamp_us()} -> 1706508000000000
    """
    return int(datetime.now().timestamp() * 1000000)


def now_us() -> str:
    """Get current datetime with microsecond precision as formatted string.

    Returns:
        Current datetime in YYYYMMDDHHMMSS%f format (microseconds)

    Examples:
        ${now_us()} -> "20260129133045123456"
    """
    return datetime.now().strftime('%Y%m%d%H%M%S%f')


def date(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Generate formatted current date/time string.

    Args:
        format_str: strftime format string (default: "%Y-%m-%d %H:%M:%S")

    Returns:
        Formatted date/time string

    Examples:
        ${date()} -> "2026-01-29 13:30:00"
        ${date('%Y-%m-%d')} -> "2026-01-29"
        ${date('%Y%m%d')} -> "20260129"
    """
    return datetime.now().strftime(format_str)


def now() -> datetime:
    """Get current datetime object.

    Returns:
        Current datetime object

    Examples:
        ${now()} -> datetime object
        ${now().strftime('%Y-%m-%d')} -> "2026-01-29"
    """
    return datetime.now()


def choice(choices: list) -> any:
    """Choose a random element from a list.

    Args:
        choices: List of choices

    Returns:
        Randomly chosen element

    Examples:
        ${choice(['a', 'b', 'c'])} -> "b"
        ${choice([1, 2, 3])} -> 2
    """
    return random.choice(choices)


def randint(min_val: int = 0, max_val: int = 100) -> int:
    """Alias for random_int() for compatibility.

    Args:
        min_val: Minimum value (default: 0)
        max_val: Maximum value (default: 100)

    Returns:
        Random integer between min_val and max_val
    """
    return random_int(min_val, max_val)


# Global database connection pool manager
_db_connection_pool: Dict[str, Any] = None
_variable_manager_ref = None


def register_db_connection_pool(pool: Dict[str, Any]) -> None:
    """Register the global database connection pool.

    Args:
        pool: Database connection pool dictionary
    """
    global _db_connection_pool
    _db_connection_pool = pool


def register_variable_manager(vm: Any) -> None:
    """Register the variable manager for database access.

    Args:
        vm: VariableManager instance
    """
    global _variable_manager_ref
    _variable_manager_ref = vm


def db_query(sql: str, *params, connection_alias: str = "default") -> Any:
    """Execute a database query and return results.

    This function allows querying databases directly from templates.
    Only SELECT queries are allowed for security.

    Args:
        sql: SQL query string (must be SELECT)
        *params: Query parameters for prepared statements
        connection_alias: Database connection alias (default: "default")

    Returns:
        - Single value for single column queries
        - Dict for single row, multi column queries
        - List of dicts for multi row queries

    Raises:
        ValueError: If SQL is not SELECT, connection not found, or query fails

    Examples:
        ${db_query('SELECT name FROM users WHERE id = %s', 123)}
        ${db_query('SELECT * FROM products WHERE sku = %s', 'SKU123')}
        ${db_query('SELECT COUNT(*) FROM orders', connection_alias='mysql_main')}
    """
    global _variable_manager_ref

    # Security check: Only allow SELECT queries
    sql_stripped = sql.strip().upper()
    if not sql_stripped.startswith("SELECT"):
        raise ValueError(
            f"db_query() only allows SELECT queries for security. Got: {sql[:50]}"
        )

    # Check for dangerous keywords
    dangerous_keywords = [
        "DROP",
        "DELETE",
        "INSERT",
        "UPDATE",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "EXEC",
        "EXECUTE",
    ]
    for keyword in dangerous_keywords:
        if keyword in sql_stripped:
            raise ValueError(
                f"db_query() does not allow {keyword} operations. Got: {sql[:50]}"
            )

    # Get database config from variable manager
    if _variable_manager_ref is None:
        raise ValueError(
            "Database connection not configured. "
            "Please add database config to config.variables."
        )

    # Try to get database config from variables
    db_config = None

    # Check for connection config in variables
    all_vars = _variable_manager_ref.get_all_variables()

    # Look for database config with specific alias
    if f"db_{connection_alias}" in all_vars:
        db_config = all_vars[f"db_{connection_alias}"]
    elif "database" in all_vars:
        db_config = all_vars["database"]
    else:
        raise ValueError(
            f"Database connection '{connection_alias}' not found in variables. "
            f"Please configure it in config.variables."
        )

    # Execute query
    try:
        return _execute_db_query(db_config, sql, params)
    except Exception as e:
        raise ValueError(f"Database query failed: {e}")


def _execute_db_query(
    db_config: Dict[str, Any], sql: str, params: tuple
) -> Any:
    """Execute database query with given config.

    Args:
        db_config: Database configuration dict
        sql: SQL query
        params: Query parameters

    Returns:
        Query results
    """
    db_type = db_config.get("type", "sqlite")
    connection = db_config.get("connection")

    if db_type == "sqlite":
        return _execute_sqlite_query(connection, sql, params)
    elif db_type == "mysql":
        return _execute_mysql_query(connection, sql, params)
    elif db_type == "postgresql":
        return _execute_postgresql_query(connection, sql, params)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def _execute_sqlite_query(db_path: str, sql: str, params: tuple) -> Any:
    """Execute SQLite query.

    Args:
        db_path: Path to SQLite database file
        sql: SQL query
        params: Query parameters

    Returns:
        Query results
    """
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # Convert to list of dicts
        results = [dict(row) for row in rows]

        # Return based on result structure
        if len(results) == 0:
            return None
        elif len(results) == 1:
            row = results[0]
            if len(row) == 1:
                # Single column, return value
                return list(row.values())[0]
            else:
                # Multiple columns, return dict
                return row
        else:
            # Multiple rows
            if len(results[0]) == 1:
                # Single column, return list of values
                return [list(row.values())[0] for row in results]
            else:
                # Multiple columns, return list of dicts
                return results
    finally:
        conn.close()


def _execute_mysql_query(connection_string: str, sql: str, params: tuple) -> Any:
    """Execute MySQL query.

    Args:
        connection_string: MySQL connection string
        sql: SQL query
        params: Query parameters

    Returns:
        Query results
    """
    try:
        import pymysql

        # Parse connection string: mysql://user:password@host:port/database
        match = re.match(
            r"mysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", connection_string
        )
        if not match:
            raise ValueError(f"Invalid MySQL connection string: {connection_string}")

        user, password, host, port, database = match.groups()

        conn = pymysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor,
        )
        cursor = conn.cursor()

        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            # Return based on result structure
            if len(rows) == 0:
                return None
            elif len(rows) == 1:
                row = rows[0]
                if len(row) == 1:
                    return list(row.values())[0]
                else:
                    return row
            else:
                if len(rows[0]) == 1:
                    return [list(row.values())[0] for row in rows]
                else:
                    return rows
        finally:
            conn.close()
    except ImportError:
        raise ValueError(
            "pymysql is required for MySQL queries. "
            "Install it with: pip install pymysql"
        )


def _execute_postgresql_query(
    connection_string: str, sql: str, params: tuple
) -> Any:
    """Execute PostgreSQL query.

    Args:
        connection_string: PostgreSQL connection string
        sql: SQL query
        params: Query parameters

    Returns:
        Query results
    """
    try:
        import psycopg2
        import psycopg2.extras

        # Parse connection string: postgresql://user:password@host:port/database
        match = re.match(
            r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", connection_string
        )
        if not match:
            raise ValueError(
                f"Invalid PostgreSQL connection string: {connection_string}"
            )

        user, password, host, port, database = match.groups()

        conn = psycopg2.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database,
        )
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            # Convert to list of dicts
            results = [dict(row) for row in rows]

            # Return based on result structure
            if len(results) == 0:
                return None
            elif len(results) == 1:
                row = results[0]
                if len(row) == 1:
                    return list(row.values())[0]
                else:
                    return row
            else:
                if len(results[0]) == 1:
                    return [list(row.values())[0] for row in results]
                else:
                    return results
        finally:
            conn.close()
    except ImportError:
        raise ValueError(
            "psycopg2 is required for PostgreSQL queries. "
            "Install it with: pip install psycopg2-binary"
        )


# Dictionary of all built-in functions
TEMPLATE_FUNCTIONS = {
    "random": random_int,
    "randint": randint,
    "random_str": random_str,
    "uuid": uuid_str,
    "uuid4": uuid4,
    "timestamp": timestamp,
    "timestamp_ms": timestamp_ms,
    "timestamp_us": timestamp_us,
    "date": date,
    "now": now,
    "now_us": now_us,
    "choice": choice,
    "db_query": db_query,
}


def get_template_functions(variable_manager: Any = None) -> dict:
    """Get all available template functions.

    Args:
        variable_manager: Optional VariableManager instance for db_query support

    Returns:
        Dictionary of function name to function object
    """
    if variable_manager is not None:
        register_variable_manager(variable_manager)

    return TEMPLATE_FUNCTIONS.copy()
