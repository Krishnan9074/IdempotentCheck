from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import re
from ..models.test_case import TestCase

class HTMLValidator:
    # Patterns for dynamic content that should be ignored
    DYNAMIC_PATTERNS = {
        'timestamp': r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
        'id': r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        'random': r'[a-zA-Z0-9]{32}',
        'csrf': r'csrf_token',
        'session': r'session_id',
    }

    def __init__(self):
        self.ignored_attributes = {
            'id', 'class', 'data-*', 'aria-*', 'style',
            'src', 'href', 'alt', 'title', 'datetime'
        }

    def validate_html(self, html_content: str, test_case: TestCase) -> Dict[str, List[str]]:
        """
        Validate HTML content for stability and idempotency.
        Returns a dictionary with validation results and issues found.
        """
        if not html_content:
            return {'success': True, 'issues': []}

        soup = BeautifulSoup(html_content, 'html.parser')
        issues = []

        # Check for dynamic content
        issues.extend(self._check_dynamic_content(soup))

        # Check for unstable attributes
        issues.extend(self._check_unstable_attributes(soup))

        # Check for unstable structure
        issues.extend(self._check_unstable_structure(soup))

        # Check for unstable text content
        issues.extend(self._check_unstable_text(soup))

        return {
            'success': len(issues) == 0,
            'issues': issues
        }

    def _check_dynamic_content(self, soup: BeautifulSoup) -> List[str]:
        """Check for dynamic content that might cause instability."""
        issues = []
        
        # Check text content
        for text in soup.stripped_strings:
            for pattern_name, pattern in self.DYNAMIC_PATTERNS.items():
                if re.search(pattern, text):
                    issues.append(f"Dynamic content found: {pattern_name} in text: {text[:50]}...")
                    break

        # Check attributes
        for tag in soup.find_all(True):
            for attr_name, attr_value in tag.attrs.items():
                if isinstance(attr_value, str):
                    for pattern_name, pattern in self.DYNAMIC_PATTERNS.items():
                        if re.search(pattern, attr_value):
                            issues.append(
                                f"Dynamic content found: {pattern_name} in attribute {attr_name} "
                                f"of tag {tag.name}: {attr_value[:50]}..."
                            )
                            break

        return issues

    def _check_unstable_attributes(self, soup: BeautifulSoup) -> List[str]:
        """Check for attributes that might cause instability."""
        issues = []
        
        for tag in soup.find_all(True):
            for attr_name, attr_value in tag.attrs.items():
                # Check for dynamic class names
                if attr_name == 'class' and isinstance(attr_value, list):
                    for class_name in attr_value:
                        if any(pattern in class_name for pattern in ['dynamic', 'random', 'temp']):
                            issues.append(f"Unstable class name found: {class_name}")

                # Check for dynamic IDs
                if attr_name == 'id' and isinstance(attr_value, str):
                    if re.match(r'.*[0-9]+$', attr_value):
                        issues.append(f"Unstable ID found: {attr_value}")

        return issues

    def _check_unstable_structure(self, soup: BeautifulSoup) -> List[str]:
        """Check for structural elements that might cause instability."""
        issues = []
        
        # Check for dynamic table structures
        for table in soup.find_all('table'):
            if not table.find('thead') or not table.find('tbody'):
                issues.append("Table missing thead or tbody elements")

        # Check for dynamic form structures
        for form in soup.find_all('form'):
            if not form.find('input', {'type': 'hidden', 'name': 'csrf_token'}):
                issues.append("Form missing CSRF token")

        return issues

    def _check_unstable_text(self, soup: BeautifulSoup) -> List[str]:
        """Check for text content that might cause instability."""
        issues = []
        
        # Check for dynamic text content
        for text in soup.stripped_strings:
            # Check for timestamps
            if re.match(r'\d{1,2}:\d{2}:\d{2}', text):
                issues.append(f"Timestamp found in text: {text}")

            # Check for dynamic numbers
            if re.match(r'^\d+$', text):
                issues.append(f"Dynamic number found in text: {text}")

        return issues

    def sanitize_html(self, html_content: str) -> str:
        """
        Sanitize HTML content by removing or normalizing dynamic elements.
        Returns the sanitized HTML content.
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove dynamic attributes
        for tag in soup.find_all(True):
            for attr in list(tag.attrs.keys()):
                if attr in self.ignored_attributes:
                    del tag[attr]

        # Normalize dynamic content
        for text in soup.stripped_strings:
            for pattern_name, pattern in self.DYNAMIC_PATTERNS.items():
                if re.search(pattern, text):
                    # Replace dynamic content with placeholders
                    new_text = re.sub(pattern, f'[{pattern_name}]', text)
                    text.replace_with(new_text)

        return str(soup) 