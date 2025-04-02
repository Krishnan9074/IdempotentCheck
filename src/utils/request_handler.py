import requests
from typing import Dict, Optional, Any
from ..models.test_case import TestCase, HTTPMethod

class RequestHandler:
    def __init__(self):
        self.session = requests.Session()
        self.timeout = 30  # Default timeout in seconds

    def execute_request(self, test_case: TestCase) -> requests.Response:
        """
        Execute a request based on the test case configuration.
        """
        method = test_case.method.value
        url = test_case.url
        headers = test_case.headers
        body = test_case.body

        # Add default headers if not present
        if 'Content-Type' not in headers and method in [HTTPMethod.POST.value, HTTPMethod.PUT.value, HTTPMethod.PATCH.value]:
            headers['Content-Type'] = 'application/json'

        # Prepare request data
        data = None
        if method in [HTTPMethod.POST.value, HTTPMethod.PUT.value, HTTPMethod.PATCH.value]:
            if isinstance(body, dict):
                data = body
            else:
                data = {'data': body}

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise RequestError(f"Request failed: {str(e)}")

    def validate_response(self, response: requests.Response, test_case: TestCase) -> Dict[str, Any]:
        """
        Validate the response against the test case expectations.
        """
        validation_result = {
            'success': True,
            'errors': []
        }

        # Check status code
        if response.status_code != test_case.expected_status_code:
            validation_result['success'] = False
            validation_result['errors'].append(
                f"Status code mismatch. Expected: {test_case.expected_status_code}, "
                f"Got: {response.status_code}"
            )

        # Check response body if expected response is provided
        if test_case.expected_response:
            try:
                response_data = response.json()
                if response_data != test_case.expected_response:
                    validation_result['success'] = False
                    validation_result['errors'].append(
                        "Response body mismatch with expected response"
                    )
            except ValueError:
                validation_result['success'] = False
                validation_result['errors'].append(
                    "Response is not valid JSON"
                )

        return validation_result

    def set_timeout(self, timeout: int):
        """
        Set the request timeout in seconds.
        """
        self.timeout = timeout

    def set_headers(self, headers: Dict[str, str]):
        """
        Set default headers for all requests.
        """
        self.session.headers.update(headers)

    def clear_headers(self):
        """
        Clear all default headers.
        """
        self.session.headers.clear()

class RequestError(Exception):
    """Custom exception for request-related errors."""
    pass 