from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum

class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

class TestCase(BaseModel):
    name: str
    method: HTTPMethod
    url: str
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    expected_status_code: int
    expected_response: Optional[Dict[str, Any]] = None
    noisy_parameters: List[str] = Field(default_factory=list)
    idempotent: bool = True
    html_validation: bool = False
    max_payload_size: int = 10000  # Default max payload size in lines

    class Config:
        arbitrary_types_allowed = True

class TestResult(BaseModel):
    test_case: TestCase
    success: bool
    error_message: Optional[str] = None
    execution_time: float
    response_status_code: Optional[int] = None
    response_body: Optional[Dict[str, Any]] = None
    noisy_parameters_found: List[str] = Field(default_factory=list)
    idempotency_violations: List[str] = Field(default_factory=list) 