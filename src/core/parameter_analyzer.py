from typing import Dict, List, Any
import re
from datetime import datetime
from ..models.test_case import TestCase

class ParameterAnalyzer:
    # Common patterns for noisy parameters
    NOISY_PATTERNS = {
        'timestamp': r'(?i)(timestamp|time|date|created_at|updated_at)',
        'token': r'(?i)(token|auth|bearer|jwt)',
        'id': r'(?i)(id|uuid|guid)',
        'random': r'(?i)(random|rand|nonce)',
        'hash': r'(?i)(hash|md5|sha|digest)',
        'session': r'(?i)(session|sid)',
        'cache': r'(?i)(cache|etag)',
    }

    @staticmethod
    def is_timestamp(value: Any) -> bool:
        """Check if a value is a timestamp or datetime."""
        if isinstance(value, (int, float)):
            # Check if it's a Unix timestamp
            try:
                datetime.fromtimestamp(value)
                return True
            except (ValueError, TypeError):
                return False
        elif isinstance(value, str):
            # Check common datetime formats
            datetime_formats = [
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d'
            ]
            for fmt in datetime_formats:
                try:
                    datetime.strptime(value, fmt)
                    return True
                except ValueError:
                    continue
        return False

    @staticmethod
    def is_token(value: Any) -> bool:
        """Check if a value looks like a token."""
        if not isinstance(value, str):
            return False
        # Check for JWT-like structure (three parts separated by dots)
        if re.match(r'^[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$', value):
            return True
        # Check for other common token patterns
        return bool(re.match(r'^[A-Za-z0-9-_=]+$', value))

    def analyze_parameters(self, test_case: TestCase) -> List[str]:
        """Analyze test case parameters to identify noisy ones."""
        noisy_params = []

        # Analyze headers
        for header_name, header_value in test_case.headers.items():
            if self._is_noisy_header(header_name, header_value):
                noisy_params.append(f"header:{header_name}")

        # Analyze body
        if test_case.body:
            noisy_params.extend(self._analyze_dict(test_case.body))

        return noisy_params

    def _is_noisy_header(self, header_name: str, header_value: str) -> bool:
        """Check if a header is likely to be noisy."""
        noisy_headers = {
            'Authorization', 'X-Request-ID', 'X-Correlation-ID',
            'X-Timestamp', 'X-Request-Time', 'X-Response-Time',
            'ETag', 'Last-Modified', 'If-Modified-Since',
            'If-None-Match', 'Cache-Control'
        }
        return header_name in noisy_headers

    def _analyze_dict(self, data: Dict[str, Any], path: str = '') -> List[str]:
        """Recursively analyze dictionary values for noisy parameters."""
        noisy_params = []
        
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            # Check key name against patterns
            for pattern_name, pattern in self.NOISY_PATTERNS.items():
                if re.search(pattern, key):
                    noisy_params.append(current_path)
                    break
            
            # Check value types
            if isinstance(value, dict):
                noisy_params.extend(self._analyze_dict(value, current_path))
            elif isinstance(value, list):
                noisy_params.extend(self._analyze_list(value, current_path))
            elif self.is_timestamp(value):
                noisy_params.append(current_path)
            elif self.is_token(value):
                noisy_params.append(current_path)
        
        return noisy_params

    def _analyze_list(self, data: List[Any], path: str) -> List[str]:
        """Analyze list values for noisy parameters."""
        noisy_params = []
        
        for i, value in enumerate(data):
            current_path = f"{path}[{i}]"
            
            if isinstance(value, dict):
                noisy_params.extend(self._analyze_dict(value, current_path))
            elif isinstance(value, list):
                noisy_params.extend(self._analyze_list(value, current_path))
            elif self.is_timestamp(value):
                noisy_params.append(current_path)
            elif self.is_token(value):
                noisy_params.append(current_path)
        
        return noisy_params 