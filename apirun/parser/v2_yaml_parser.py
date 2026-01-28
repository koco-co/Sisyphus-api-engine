"""V2 YAML Parser for Sisyphus API Engine.

This module parses YAML test case files conforming to the v2.0 protocol.
Following Google Python Style Guide.
"""

import os
import copy
from typing import Any, Dict, List, Optional
from yaml import safe_load, YAMLError
from yaml_include import Constructor

from apirun.core.models import (
    TestCase,
    TestStep,
    GlobalConfig,
    ProfileConfig,
    ValidationRule,
    Extractor,
    HttpMethod,
)
from apirun.utils.template import render_template


class YamlParseError(Exception):
    """Exception raised for YAML parsing errors."""

    pass


class V2YamlParser:
    """Parser for v2.0 YAML test case format.

    This parser supports:
    - Config section with profiles
    - Variable extraction and rendering
    - Multiple step types
    - Validation rules
    - Step control (skip_if, only_if, depends_on)
    - Setup/teardown hooks

    Usage:
        parser = V2YamlParser()
        test_case = parser.parse("test_case.yaml")
    """

    def __init__(self):
        """Initialize V2YamlParser."""
        pass

    def _load_yaml_with_include(self, yaml_file: str) -> Dict[str, Any]:
        """Load YAML with !include support.

        Args:
            yaml_file: Path to YAML file

        Returns:
            Parsed YAML data
        """
        from yaml import Loader
        from yaml_include import Constructor

        # Set up include constructor
        base_dir = os.path.dirname(os.path.abspath(yaml_file))

        def include_constructor(loader, node):
            """Handle !include tag."""
            filename = loader.construct_scalar(node)
            if not os.path.isabs(filename):
                filename = os.path.join(base_dir, filename)

            with open(filename, "r", encoding="utf-8") as f:
                return safe_load(f)

        Loader.add_constructor("!include", include_constructor)

        with open(yaml_file, "r", encoding="utf-8") as f:
            return safe_load(f)

    def parse(self, yaml_file: str) -> TestCase:
        """Parse YAML file into TestCase object.

        Args:
            yaml_file: Path to YAML file

        Returns:
            TestCase object

        Raises:
            YamlParseError: If parsing fails
            FileNotFoundError: If file not found
        """
        if not os.path.exists(yaml_file):
            raise FileNotFoundError(f"YAML file not found: {yaml_file}")

        try:
            data = self._load_yaml_with_include(yaml_file)
        except YAMLError as e:
            raise YamlParseError(f"Failed to parse YAML file: {e}")

        if not data:
            raise YamlParseError(f"Empty YAML file: {yaml_file}")

        self._current_file = yaml_file
        return self._parse_test_case(data)

    def parse_string(self, yaml_content: str) -> TestCase:
        """Parse YAML string content into TestCase object.

        Args:
            yaml_content: YAML content as string

        Returns:
            TestCase object

        Raises:
            YamlParseError: If parsing fails
        """
        try:
            data = safe_load(yaml_content)
        except YAMLError as e:
            raise YamlParseError(f"Failed to parse YAML content: {e}")

        if not data:
            raise YamlParseError("Empty YAML content")

        return self._parse_test_case(data)

    def _parse_test_case(self, data: Dict[str, Any]) -> TestCase:
        """Parse test case from YAML data.

        Args:
            data: Parsed YAML data

        Returns:
            TestCase object
        """
        name = data.get("name", "Unnamed Test Case")
        description = data.get("description", "")

        # Parse config section
        config = self._parse_config(data.get("config", {}))

        # Parse setup/teardown
        setup = data.get("setup")
        teardown = data.get("teardown")

        # Parse tags
        tags = data.get("tags", [])

        # Parse enabled flag
        enabled = data.get("enabled", True)

        # Parse steps
        steps_data = data.get("steps", [])
        steps = []
        for step_data in steps_data:
            step = self._parse_step(step_data)
            if step:
                steps.append(step)

        return TestCase(
            name=name,
            description=description,
            config=config,
            steps=steps,
            setup=setup,
            teardown=teardown,
            tags=tags,
            enabled=enabled,
        )

    def _parse_config(self, config_data: Dict[str, Any]) -> Optional[GlobalConfig]:
        """Parse global config section.

        Args:
            config_data: Config section from YAML

        Returns:
            GlobalConfig object or None
        """
        if not config_data:
            return None

        name = config_data.get("name", "Test Suite")
        description = config_data.get("description", "")

        # Parse profiles
        profiles = {}
        profiles_data = config_data.get("profiles", {})
        for profile_name, profile_config in profiles_data.items():
            profiles[profile_name] = ProfileConfig(
                base_url=profile_config.get("base_url", ""),
                variables=profile_config.get("variables", {}),
                timeout=profile_config.get("timeout", 30),
                verify_ssl=profile_config.get("verify_ssl", True),
            )

        active_profile = config_data.get("active_profile")

        # Parse global variables
        variables = config_data.get("variables", {})

        # Parse other config options
        timeout = config_data.get("timeout", 30)
        retry_times = config_data.get("retry_times", 0)
        concurrent = config_data.get("concurrent", False)
        concurrent_threads = config_data.get("concurrent_threads", 3)

        # Parse data source configuration
        data_source = config_data.get("data_source")
        data_iterations = config_data.get("data_iterations", False)
        variable_prefix = config_data.get("variable_prefix", "")

        return GlobalConfig(
            name=name,
            description=description,
            profiles=profiles,
            active_profile=active_profile,
            variables=variables,
            timeout=timeout,
            retry_times=retry_times,
            concurrent=concurrent,
            concurrent_threads=concurrent_threads,
            data_source=data_source,
            data_iterations=data_iterations,
            variable_prefix=variable_prefix,
        )

    def _parse_step(self, step_data: Dict[str, Any]) -> Optional[TestStep]:
        """Parse single test step.

        Args:
            step_data: Step data from YAML

        Returns:
            TestStep object or None
        """
        # Extract step name (key or name field)
        if len(step_data) == 1 and isinstance(list(step_data.values())[0], dict):
            name = list(step_data.keys())[0]
            step_details = step_data[name]
        else:
            name = step_data.get("name", "Unnamed Step")
            step_details = step_data

        step_type = step_details.get("type", "request")

        # Parse request-specific fields
        method = step_details.get("method")
        url = step_details.get("url")
        params = step_details.get("params")
        headers = step_details.get("headers")
        body = step_details.get("body")

        # Parse database-specific fields
        database = step_details.get("database")
        operation = step_details.get("operation")
        sql = step_details.get("sql")

        # Parse wait-specific fields
        seconds = step_details.get("seconds")
        condition = step_details.get("condition")
        interval = step_details.get("interval")
        max_wait = step_details.get("max_wait")

        # Parse loop-specific fields
        loop_type = step_details.get("loop_type")
        loop_count = step_details.get("loop_count")
        loop_condition = step_details.get("loop_condition")
        loop_variable = step_details.get("loop_variable")
        loop_steps = step_details.get("loop_steps")

        # Parse concurrent-specific fields
        max_concurrency = step_details.get("max_concurrency")
        concurrent_steps = step_details.get("concurrent_steps")

        # Parse validations
        validations = []
        validations_data = step_details.get("validations", [])
        for val_data in validations_data:
            validation = self._parse_validation(val_data)
            if validation:
                validations.append(validation)

        # Parse extractors
        extractors = []
        extractors_data = step_details.get("extractors", [])
        for ext_data in extractors_data:
            extractor = self._parse_extractor(ext_data)
            if extractor:
                extractors.append(extractor)

        # Parse step control
        skip_if = step_details.get("skip_if")
        only_if = step_details.get("only_if")
        depends_on = step_details.get("depends_on", [])

        # Parse timeout and retry
        timeout = step_details.get("timeout")
        retry_times = step_details.get("retry_times")
        retry_policy = step_details.get("retry_policy")

        # Parse setup/teardown
        setup = step_details.get("setup")
        teardown = step_details.get("teardown")

        return TestStep(
            name=name,
            type=step_type,
            method=method,
            url=url,
            params=params,
            headers=headers,
            body=body,
            validations=validations,
            extractors=extractors,
            skip_if=skip_if,
            only_if=only_if,
            depends_on=depends_on,
            timeout=timeout,
            retry_times=retry_times,
            setup=setup,
            teardown=teardown,
            database=database,
            operation=operation,
            sql=sql,
            seconds=seconds,
            condition=condition,
            interval=interval,
            max_wait=max_wait,
            loop_type=loop_type,
            loop_count=loop_count,
            loop_condition=loop_condition,
            loop_variable=loop_variable,
            loop_steps=loop_steps,
            retry_policy=retry_policy,
            max_concurrency=max_concurrency,
            concurrent_steps=concurrent_steps,
        )

    def _parse_validation(self, val_data: Dict[str, Any]) -> Optional[ValidationRule]:
        """Parse validation rule.

        Args:
            val_data: Validation data from YAML

        Returns:
            ValidationRule object or None
        """
        if not isinstance(val_data, dict):
            return None

        val_type = val_data.get("type", "eq")
        path = val_data.get("path", "$")
        expect = val_data.get("expect")
        description = val_data.get("description", "")

        return ValidationRule(
            type=val_type, path=path, expect=expect, description=description
        )

    def _parse_extractor(self, ext_data: Dict[str, Any]) -> Optional[Extractor]:
        """Parse variable extractor.

        Args:
            ext_data: Extractor data from YAML

        Returns:
            Extractor object or None
        """
        if not isinstance(ext_data, dict):
            return None

        name = ext_data.get("name")
        ext_type = ext_data.get("type", "jsonpath")
        path = ext_data.get("path", "")
        index = ext_data.get("index", 0)

        if not name:
            return None

        return Extractor(name=name, type=ext_type, path=path, index=index)

    def validate_yaml(self, yaml_file: str) -> List[str]:
        """Validate YAML file without parsing.

        Args:
            yaml_file: Path to YAML file

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not os.path.exists(yaml_file):
            errors.append(f"File not found: {yaml_file}")
            return errors

        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = safe_load(f)

            if not data:
                errors.append("Empty YAML file")
                return errors

            # Check required fields
            if "name" not in data:
                errors.append("Missing required field: name")

            if "steps" not in data:
                errors.append("Missing required field: steps")
            elif not isinstance(data["steps"], list):
                errors.append("Field 'steps' must be a list")
            elif len(data["steps"]) == 0:
                errors.append("Field 'steps' cannot be empty")

        except YAMLError as e:
            errors.append(f"YAML syntax error: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")

        return errors


def parse_yaml_file(yaml_file: str) -> TestCase:
    """Convenience function to parse YAML file.

    Args:
        yaml_file: Path to YAML file

    Returns:
        TestCase object
    """
    parser = V2YamlParser()
    return parser.parse(yaml_file)


def parse_yaml_string(yaml_content: str) -> TestCase:
    """Convenience function to parse YAML string.

    Args:
        yaml_content: YAML content as string

    Returns:
        TestCase object
    """
    parser = V2YamlParser()
    return parser.parse_string(yaml_content)
