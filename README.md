# TestSuite Idempotency Checker

A tool to analyze test suites for idempotency violations and noisy parameters.

## Features

- Identifies noisy parameters in test cases
- Validates CRUD operations for idempotency
- Generates detailed HTML reports
- Supports multiple test frameworks
- Provides actionable insights for test improvement

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/idemcheck.git
cd idemcheck
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Allure command-line tool:
```bash
# On macOS
brew install allure

# On Windows (using Scoop)
scoop install allure

# On Linux
sudo apt-add-repository ppa:qameta/allure
sudo apt-get update
sudo apt-get install allure
```

## Usage

### Basic Usage

Run the idempotency checker on your test suite:

```bash
idemcheck run --test-dir path/to/tests
```

### Command Options

1. Run Command:
```bash
idemcheck run [OPTIONS]
```
Options:
- `--test-dir`: Directory containing test files (required)
- `--output-dir`: Directory for output files (default: "reports")
- `--framework`: Test framework to use (default: "pytest")
- `--verbose`: Enable verbose output
- `--no-report`: Skip report generation

2. Generate Report:
```bash
idemcheck report [OPTIONS]
```
Options:
- `--input-dir`: Directory containing test results (default: "reports")
- `--output-dir`: Directory for generated report (default: "reports")
- `--format`: Report format (default: "html")

3. Analyze Parameters:
```bash
idemcheck analyze [OPTIONS]
```
Options:
- `--test-dir`: Directory containing test files (required)
- `--output-file`: Output file for analysis results (default: "parameter_analysis.json")
- `--threshold`: Noise threshold (default: 0.1)

### Examples

1. Run tests and generate report:
```bash
idemcheck run --test-dir tests/ --output-dir reports/
```

2. Generate HTML report from existing results:
```bash
idemcheck report --input-dir reports/ --output-dir reports/
```

3. Analyze test parameters:
```bash
idemcheck analyze --test-dir tests/ --output-file analysis.json
```

## Output

The tool generates several types of output:

1. Test Results:
   - JSON file containing test execution results
   - Includes noisy parameters and idempotency violations

2. HTML Report:
   - Interactive report with test statistics
   - Visualizations of parameter analysis
   - Detailed violation information

3. Parameter Analysis:
   - JSON file with parameter statistics
   - Noise scores for each parameter
   - Recommendations for improvement

## Configuration

Create a `config.yaml` file in your project root:

```yaml
framework: pytest
output_dir: reports
threshold: 0.1
```
# Sample ss:
