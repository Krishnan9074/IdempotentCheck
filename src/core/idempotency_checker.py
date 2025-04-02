import time
from typing import Dict, List, Optional
import requests
from ..models.test_case import TestCase, TestResult, HTTPMethod
from .parameter_analyzer import ParameterAnalyzer
from .html_validator import HTMLValidator

class IdempotencyChecker:
    def __init__(self):
        self.parameter_analyzer = ParameterAnalyzer()
        self.html_validator = HTMLValidator()
        self.session = requests.Session()

    def check_test_case(self, test_case: TestCase) -> TestResult:
        """
        Check a test case for idempotency issues.
        Returns a TestResult object with the findings.
        """
        start_time = time.time()
        result = TestResult(
            test_case=test_case,
            success=True,
            execution_time=0,
            noisy_parameters_found=[],
            idempotency_violations=[]
        )

        try:
            # Analyze parameters for noise
            noisy_params = self.parameter_analyzer.analyze_parameters(test_case)
            result.noisy_parameters_found = noisy_params

            # Execute the test case multiple times
            responses = self._execute_multiple_times(test_case)
            
            # Check for idempotency violations
            violations = self._check_idempotency_violations(responses)
            result.idempotency_violations = violations

            # Validate HTML if needed
            if test_case.html_validation:
                html_issues = self._validate_html_responses(responses)
                result.idempotency_violations.extend(html_issues)

            # Set final success status
            result.success = len(violations) == 0 and len(noisy_params) == 0

        except Exception as e:
            result.success = False
            result.error_message = str(e)

        finally:
            result.execution_time = time.time() - start_time

        return result

    def _execute_multiple_times(self, test_case: TestCase, num_executions: int = 3) -> List[Dict]:
        """
        Execute a test case multiple times and return the responses.
        """
        responses = []
        
        for _ in range(num_executions):
            response = self._execute_request(test_case)
            responses.append({
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            })
            time.sleep(0.1)  # Small delay between requests

        return responses

    def _execute_request(self, test_case: TestCase) -> requests.Response:
        """
        Execute a single request for a test case.
        """
        method = test_case.method.value
        url = test_case.url
        headers = test_case.headers
        body = test_case.body

        response = self.session.request(
            method=method,
            url=url,
            headers=headers,
            json=body if method in [HTTPMethod.POST.value, HTTPMethod.PUT.value, HTTPMethod.PATCH.value] else None
        )

        return response

    def _check_idempotency_violations(self, responses: List[Dict]) -> List[str]:
        """
        Check for idempotency violations by comparing multiple responses.
        """
        violations = []
        
        if not responses:
            return violations

        # Compare status codes
        status_codes = [r['status_code'] for r in responses]
        if len(set(status_codes)) > 1:
            violations.append(f"Inconsistent status codes: {status_codes}")

        # Compare response bodies
        bodies = [r['body'] for r in responses]
        if len(set(str(b) for b in bodies)) > 1:
            violations.append("Inconsistent response bodies")

        # Compare headers (excluding known dynamic headers)
        dynamic_headers = {'date', 'last-modified', 'etag', 'x-request-id'}
        headers = [set((k, v) for k, v in r['headers'].items() if k.lower() not in dynamic_headers) 
                  for r in responses]
        if len(set(tuple(h) for h in headers)) > 1:
            violations.append("Inconsistent headers")

        return violations

    def _validate_html_responses(self, responses: List[Dict]) -> List[str]:
        """
        Validate HTML responses for stability issues.
        """
        issues = []
        
        for i, response in enumerate(responses):
            if isinstance(response['body'], str):
                validation_result = self.html_validator.validate_html(response['body'], response['test_case'])
                if not validation_result['success']:
                    issues.extend([f"HTML validation issue in response {i}: {issue}" 
                                 for issue in validation_result['issues']])

        return issues

    def sanitize_test_case(self, test_case: TestCase) -> TestCase:
        """
        Create a sanitized version of the test case by removing or normalizing noisy parameters.
        """
        sanitized = test_case.copy()
        
        # Remove noisy headers
        sanitized.headers = {
            k: v for k, v in test_case.headers.items()
            if not any(pattern in k.lower() for pattern in ['timestamp', 'token', 'id', 'random'])
        }
        
        # Sanitize body if it's a dictionary
        if isinstance(test_case.body, dict):
            sanitized.body = self._sanitize_dict(test_case.body)
        
        return sanitized

    def _sanitize_dict(self, data: Dict) -> Dict:
        """
        Recursively sanitize a dictionary by removing or normalizing noisy parameters.
        """
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_dict(item) if isinstance(item, dict) else item 
                                for item in value]
            else:
                sanitized[key] = value
                
        return sanitized 