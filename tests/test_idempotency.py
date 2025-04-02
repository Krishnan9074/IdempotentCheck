import pytest
import allure
from src.models.test_case import TestCase, HTTPMethod
from src.core.idempotency_checker import IdempotencyChecker
from src.utils.report_generator import ReportGenerator

# Example test cases
TEST_CASES = [
    TestCase(
        name="Get User Profile",
        method=HTTPMethod.GET,
        url="https://api.example.com/users/1",
        headers={
            "Authorization": "Bearer test-token",
            "X-Request-ID": "123e4567-e89b-12d3-a456-426614174000"
        },
        expected_status_code=200,
        expected_response={
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com"
        }
    ),
    TestCase(
        name="Create User",
        method=HTTPMethod.POST,
        url="https://api.example.com/users",
        headers={
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json"
        },
        body={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "created_at": "2024-01-01T00:00:00Z"
        },
        expected_status_code=201,
        expected_response={
            "id": 2,
            "name": "Jane Doe",
            "email": "jane@example.com"
        }
    ),
    TestCase(
        name="Update User",
        method=HTTPMethod.PUT,
        url="https://api.example.com/users/1",
        headers={
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json"
        },
        body={
            "name": "John Updated",
            "updated_at": "2024-01-02T00:00:00Z"
        },
        expected_status_code=200,
        expected_response={
            "id": 1,
            "name": "John Updated",
            "email": "john@example.com"
        }
    )
]

@pytest.fixture
def idempotency_checker():
    return IdempotencyChecker()

@pytest.fixture
def report_generator():
    return ReportGenerator()

@allure.feature("Idempotency Testing")
@allure.story("Test Case Validation")
class TestIdempotency:
    @pytest.mark.parametrize("test_case", TEST_CASES)
    def test_idempotency(self, test_case, idempotency_checker, report_generator):
        """
        Test the idempotency of a test case.
        """
        with allure.step(f"Testing {test_case.name}"):
            # Check idempotency
            result = idempotency_checker.check_test_case(test_case)
            
            # Add result to report
            report_generator.add_test_result(result)
            
            # Assert test success
            assert result.success, f"Test failed: {result.error_message}"
            
            # Assert no noisy parameters
            assert not result.noisy_parameters_found, \
                f"Found noisy parameters: {result.noisy_parameters_found}"
            
            # Assert no idempotency violations
            assert not result.idempotency_violations, \
                f"Found idempotency violations: {result.idempotency_violations}"

    def test_html_validation(self, idempotency_checker, report_generator):
        """
        Test HTML validation for a test case.
        """
        html_test_case = TestCase(
            name="Get HTML Page",
            method=HTTPMethod.GET,
            url="https://example.com",
            headers={},
            expected_status_code=200,
            html_validation=True
        )
        
        result = idempotency_checker.check_test_case(html_test_case)
        report_generator.add_test_result(result)
        
        assert result.success, f"HTML validation failed: {result.error_message}"

    def test_large_payload(self, idempotency_checker, report_generator):
        """
        Test handling of large payloads.
        """
        # Create a large payload
        large_payload = {
            "data": ["item" + str(i) for i in range(10000)]
        }
        
        large_test_case = TestCase(
            name="Large Payload Test",
            method=HTTPMethod.POST,
            url="https://api.example.com/bulk",
            headers={
                "Content-Type": "application/json"
            },
            body=large_payload,
            expected_status_code=200,
            max_payload_size=10000
        )
        
        result = idempotency_checker.check_test_case(large_test_case)
        report_generator.add_test_result(result)
        
        assert result.success, f"Large payload test failed: {result.error_message}"

    def test_noisy_parameters(self, idempotency_checker, report_generator):
        """
        Test detection of noisy parameters.
        """
        noisy_test_case = TestCase(
            name="Noisy Parameters Test",
            method=HTTPMethod.POST,
            url="https://api.example.com/data",
            headers={
                "X-Timestamp": "2024-01-01T00:00:00Z",
                "X-Random-ID": "abc123"
            },
            body={
                "timestamp": "2024-01-01T00:00:00Z",
                "random_value": "xyz789",
                "data": {
                    "created_at": "2024-01-01T00:00:00Z",
                    "session_id": "session123"
                }
            },
            expected_status_code=200
        )
        
        result = idempotency_checker.check_test_case(noisy_test_case)
        report_generator.add_test_result(result)
        
        # Verify noisy parameters are detected
        assert result.noisy_parameters_found, "Noisy parameters should be detected"
        
        # Verify specific noisy parameters
        noisy_params = set(result.noisy_parameters_found)
        expected_noisy = {
            "header:X-Timestamp",
            "header:X-Random-ID",
            "timestamp",
            "random_value",
            "data.created_at",
            "data.session_id"
        }
        assert noisy_params.intersection(expected_noisy), \
            f"Expected noisy parameters not found. Found: {noisy_params}"

    def test_crud_operations(self, idempotency_checker, report_generator):
        """
        Test CRUD operations for idempotency.
        """
        # Create resource
        create_case = TestCase(
            name="Create Resource",
            method=HTTPMethod.POST,
            url="https://api.example.com/resources",
            headers={"Content-Type": "application/json"},
            body={"name": "Test Resource"},
            expected_status_code=201
        )
        
        create_result = idempotency_checker.check_test_case(create_case)
        report_generator.add_test_result(create_result)
        assert create_result.success, "Create operation failed"
        
        # Read resource
        read_case = TestCase(
            name="Read Resource",
            method=HTTPMethod.GET,
            url="https://api.example.com/resources/1",
            headers={},
            expected_status_code=200
        )
        
        read_result = idempotency_checker.check_test_case(read_case)
        report_generator.add_test_result(read_result)
        assert read_result.success, "Read operation failed"
        
        # Update resource
        update_case = TestCase(
            name="Update Resource",
            method=HTTPMethod.PUT,
            url="https://api.example.com/resources/1",
            headers={"Content-Type": "application/json"},
            body={"name": "Updated Resource"},
            expected_status_code=200
        )
        
        update_result = idempotency_checker.check_test_case(update_case)
        report_generator.add_test_result(update_result)
        assert update_result.success, "Update operation failed"
        
        # Delete resource
        delete_case = TestCase(
            name="Delete Resource",
            method=HTTPMethod.DELETE,
            url="https://api.example.com/resources/1",
            headers={},
            expected_status_code=204
        )
        
        delete_result = idempotency_checker.check_test_case(delete_case)
        report_generator.add_test_result(delete_result)
        assert delete_result.success, "Delete operation failed" 