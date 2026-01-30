"""API Executor for Sisyphus API Engine.

This module implements HTTP/HTTPS request execution with detailed
performance metrics collection.
Following Google Python Style Guide.
"""

import time
from typing import Any, Dict, Optional
import requests
from requests.exceptions import RequestException

from apirun.executor.step_executor import StepExecutor
from apirun.core.models import TestStep, PerformanceMetrics
from apirun.validation.engine import ValidationEngine
from apirun.utils.performance import PerformanceCollector, Timings


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
    - Detailed performance metrics collection

    Attributes:
        session: Requests session instance
        validation_engine: Validation engine instance
        performance_collector: Performance metrics collector
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
        self.performance_collector = PerformanceCollector()

        # Mount performance tracking adapter
        adapter = self.performance_collector.get_adapter()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

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

        try:
            # Execute request with detailed performance tracking
            response = self.session.request(**request_kwargs)

            # Get detailed timings from performance collector
            request_id = getattr(response, "request_id", None)
            timings: Optional[Timings] = None

            if request_id is not None:
                timings = self.performance_collector.get_timings(request_id)

            # Create performance metrics
            if timings:
                performance = PerformanceMetrics(
                    total_time=timings.total,
                    dns_time=timings.dns,
                    tcp_time=timings.tcp,
                    tls_time=timings.tls,
                    server_time=timings.server,
                    download_time=timings.download,
                    upload_time=timings.upload,
                    size=len(response.content),
                )
            else:
                # Fallback to basic timing if detailed collection failed
                total_time = response.elapsed.total_seconds() * 1000 if hasattr(response, "elapsed") else 0

                performance = PerformanceMetrics(
                    total_time=total_time,
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
                # Create exception with response data attached for debugging
                error = AssertionError(f"Validation failed: {val_result['description']}")
                # Attach response data to exception for Allure reporting
                error.response = response_data
                error.validation_results = validation_results
                raise error

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
        # Build response data with request information
        result = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "cookies": dict(response.cookies),
            "url": response.url,
        }

        # Add request information for debugging
        request_obj = response.request

        # Try to get request information (handle Mock objects in tests)
        try:
            request_headers = dict(request_obj.headers) if hasattr(request_obj.headers, '__iter__') else {}
        except (TypeError, AttributeError):
            request_headers = {}

        result["request"] = {
            "method": getattr(request_obj, 'method', 'UNKNOWN'),
            "url": getattr(request_obj, 'url', ''),
            "headers": request_headers,
        }

        # Add request body if present
        if hasattr(request_obj, 'body') and request_obj.body:
            try:
                # Try to parse as JSON
                import json
                result["request"]["body"] = json.loads(request_obj.body)
            except (json.JSONDecodeError, TypeError, ValueError):
                # If not JSON, store as string
                body_str = request_obj.body
                if isinstance(body_str, bytes):
                    body_str = body_str.decode('utf-8', errors='replace')
                result["request"]["body"] = body_str

        # Add request params if available
        if hasattr(request_obj, 'params') and request_obj.params:
            try:
                result["request"]["params"] = dict(request_obj.params)
            except (TypeError, AttributeError):
                result["request"]["params"] = str(request_obj.params)

        # Try to parse response body
        content_type = response.headers.get("Content-Type", "")

        if "application/json" in content_type:
            try:
                result["body"] = response.json()
            except ValueError:
                result["body"] = response.text
        else:
            result["body"] = response.text

        # Add response time
        if hasattr(response, "elapsed"):
            result["response_time"] = response.elapsed.total_seconds() * 1000

        # Add response size
        if hasattr(response, "content"):
            result["size"] = len(response.content)

        return result
