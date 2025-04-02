import allure
from typing import List, Dict, Any
from datetime import datetime
from ..models.test_case import TestCase, TestResult

class ReportGenerator:
    def __init__(self):
        self.start_time = datetime.now()
        self.test_results: List[TestResult] = []

    def add_test_result(self, result: TestResult):
        """
        Add a test result to the report.
        """
        self.test_results.append(result)

    def generate_report(self):
        """
        Generate an Allure report with test results.
        """
        with allure.step("Test Suite Summary"):
            self._add_summary()

        for result in self.test_results:
            with allure.step(f"Test Case: {result.test_case.name}"):
                self._add_test_case_details(result)

    def _add_summary(self):
        """
        Add summary information to the report.
        """
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - successful_tests
        execution_time = sum(r.execution_time for r in self.test_results)

        allure.attach(
            f"""
            Test Suite Summary
            ================
            Total Tests: {total_tests}
            Successful: {successful_tests}
            Failed: {failed_tests}
            Total Execution Time: {execution_time:.2f} seconds
            Start Time: {self.start_time}
            End Time: {datetime.now()}
            """,
            name="Summary",
            attachment_type=allure.attachment_type.TEXT
        )

    def _add_test_case_details(self, result: TestResult):
        """
        Add detailed information about a test case to the report.
        """
        # Test case details
        allure.attach(
            f"""
            Test Case Details
            ================
            Name: {result.test_case.name}
            Method: {result.test_case.method}
            URL: {result.test_case.url}
            Expected Status Code: {result.test_case.expected_status_code}
            Execution Time: {result.execution_time:.2f} seconds
            Success: {result.success}
            """,
            name="Test Case Details",
            attachment_type=allure.attachment_type.TEXT
        )

        # Headers
        if result.test_case.headers:
            allure.attach(
                str(result.test_case.headers),
                name="Request Headers",
                attachment_type=allure.attachment_type.JSON
            )

        # Request body
        if result.test_case.body:
            allure.attach(
                str(result.test_case.body),
                name="Request Body",
                attachment_type=allure.attachment_type.JSON
            )

        # Noisy parameters
        if result.noisy_parameters_found:
            allure.attach(
                "\n".join(result.noisy_parameters_found),
                name="Noisy Parameters Found",
                attachment_type=allure.attachment_type.TEXT
            )

        # Idempotency violations
        if result.idempotency_violations:
            allure.attach(
                "\n".join(result.idempotency_violations),
                name="Idempotency Violations",
                attachment_type=allure.attachment_type.TEXT
            )

        # Error message if any
        if result.error_message:
            allure.attach(
                result.error_message,
                name="Error Message",
                attachment_type=allure.attachment_type.TEXT
            )

        # Add test status
        if result.success:
            allure.step("Test passed", status=allure.status.PASSED)
        else:
            allure.step("Test failed", status=allure.status.FAILED)

    def generate_html_report(self, output_dir: str = "allure-results"):
        """
        Generate an HTML report using Allure.
        """
        import os
        import subprocess

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Generate Allure report
        subprocess.run(["allure", "generate", output_dir, "-o", "allure-report", "--clean"])
        subprocess.run(["allure", "open", "allure-report"])

    def generate_json_report(self, output_file: str = "test_results.json") -> Dict[str, Any]:
        """
        Generate a JSON report of test results.
        """
        report = {
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_tests": len(self.test_results),
            "successful_tests": sum(1 for r in self.test_results if r.success),
            "failed_tests": sum(1 for r in self.test_results if not r.success),
            "total_execution_time": sum(r.execution_time for r in self.test_results),
            "test_results": [
                {
                    "name": r.test_case.name,
                    "method": r.test_case.method,
                    "url": r.test_case.url,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "noisy_parameters": r.noisy_parameters_found,
                    "idempotency_violations": r.idempotency_violations,
                    "error_message": r.error_message
                }
                for r in self.test_results
            ]
        }

        return report 