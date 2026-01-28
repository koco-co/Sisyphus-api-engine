"""API Executor for Sisyphus API Engine.

This module implements HTTP/HTTPS request execution.
Following Google Python Style Guide.
"""

import time
from typing import Any, Dict, Optional
import requests
from requests.exceptions import RequestException

from apirun.executor.step_executor import StepExecutor
from apirun.core.models import TestStep, PerformanceMetrics
from apirun.validation.engine import ValidationEngine


class APIExecutor(StepExecutor):
    """Executor for HTTP/HTTPS API requests.

    Supports:
    - All HTTP methods (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
    - Custom headers
    - Query parameters
    - Request body (JSON, form-data, etc.)
    - File upload/download
    - Cookie/Session management
    - SSL verification
    - Performance metrics collection

    Attributes:
        session: Requests session instance
        validation_engine: Validation engine instance
    """

    def __init__(
        self,
        variable_manager,
        step: TestStep,
        timeout: int = 30,
        retry_times: int = 0,
        previous_results=None,
    ):
        """Initialize APIExecutor.

        Args:
            variable_manager: Variable manager instance
            step: Test step to execute
            timeout: Default timeout in seconds
            retry_times: Default retry count
            previous_results: List of previous step results for dependency checking
        """
        super().__init__(variable_manager, step, timeout, retry_times, previous_results)
        self.session = requests.Session()
        self.validation_engine = ValidationEngine()

    def _execute_step(self, rendered_step: Dict[str, Any]) -> Any:
        """Execute HTTP request.

        Args:
            rendered_step: Rendered step data

        Returns:
            Execution result with response, performance, and validations

        Raises:
            RequestException: If request fails
        """
        method = rendered_step.get("method", "GET")
        url = rendered_step.get("url", "")
        headers = rendered_step.get("headers", {})
        params = rendered_step.get("params")
        body = rendered_step.get("body")
        validations = rendered_step.get("validations", [])

        # Prepare request arguments
        request_kwargs = {"method": method, "url": url, "timeout": self.timeout}

        if headers:
            request_kwargs["headers"] = headers

        if params:
            request_kwargs["params"] = params

        # Handle request body
        if body is not None:
            if isinstance(body, dict):
                if "Content-Type" in headers and "multipart/form-data" in headers["Content-Type"]:
                    request_kwargs["files"] = body
                elif "application/json" in headers.get("Content-Type", ""):
                    request_kwargs["json"] = body
                else:
                    request_kwargs["data"] = body
            else:
                request_kwargs["data"] = body

        # Execute request with performance tracking
        start_time = time.time()
        dns_start = time.time()

        try:
            response = self.session.request(**request_kwargs)
            end_time = time.time()

            # Calculate performance metrics
            total_time = (end_time - start_time) * 1000  # Convert to milliseconds

            # For detailed timing, we would need lower-level libraries
            # Using estimates for now
            dns_time = min(total_time * 0.1, 50)
            tcp_time = min(total_time * 0.15, 80)
            tls_time = min(total_time * 0.2, 100) if url.startswith("https") else 0
            server_time = min(total_time * 0.4, 200)
            download_time = total_time - dns_time - tcp_time - tls_time - server_time

            performance = PerformanceMetrics(
                total_time=total_time,
                dns_time=dns_time,
                tcp_time=tcp_time,
                tls_time=tls_time,
                server_time=server_time,
                download_time=download_time,
                size=len(response.content),
            )

        except RequestException as e:
            raise RequestException(f"HTTP request failed: {e}")

        # Parse response
        response_data = self._parse_response(response)

        # Run validations
        validation_results = []
        if validations:
            # Separate status_code validations from body validations
            status_code_validations = []
            body_validations = []

            for val in validations:
                if val.get("type") == "status_code":
                    status_code_validations.append(val)
                else:
                    body_validations.append(val)

            # Run status_code validations against full response
            if status_code_validations:
                status_code_results = self.validation_engine.validate(
                    status_code_validations, response_data
                )
                validation_results.extend(status_code_results)

            # Run other validations against response body
            if body_validations:
                validation_data = response_data.get("body", response_data)
                body_results = self.validation_engine.validate(
                    body_validations, validation_data
                )
                validation_results.extend(body_results)

        # Check if any validation failed
        for val_result in validation_results:
            if not val_result["passed"]:
                raise AssertionError(f"Validation failed: {val_result['description']}")

        return type(
            "Result",
            (),
            {
                "response": response_data,
                "performance": performance,
                "validation_results": validation_results,
            },
        )()

    def _parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """Parse HTTP response into structured data.

        Args:
            response: Requests response object

        Returns:
            Parsed response data
        """
        result = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "cookies": dict(response.cookies),
            "url": response.url,
        }

        # Try to parse body
        content_type = response.headers.get("Content-Type", "")

        if "application/json" in content_type:
            try:
                result["body"] = response.json()
            except ValueError:
                result["body"] = response.text
        else:
            result["body"] = response.text

        return result
