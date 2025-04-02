import argparse
import json
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from .core.idempotency_checker import IdempotencyChecker
from .utils.report_generator import ReportGenerator
from .models.test_case import TestCase, HTTPMethod

console = Console()

def load_test_cases(file_path: str) -> List[TestCase]:
    """
    Load test cases from a JSON file.
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
        return [TestCase(**case) for case in data]

def save_test_cases(test_cases: List[TestCase], file_path: str):
    """
    Save test cases to a JSON file.
    """
    with open(file_path, 'w') as f:
        json.dump([case.dict() for case in test_cases], f, indent=2)

def display_results(results: List[dict]):
    """
    Display test results in a rich table.
    """
    table = Table(title="Test Results")
    table.add_column("Test Case", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Execution Time", style="yellow")
    table.add_column("Noisy Parameters", style="red")
    table.add_column("Violations", style="red")

    for result in results:
        table.add_row(
            result["test_case"]["name"],
            "✓" if result["success"] else "✗",
            f"{result['execution_time']:.2f}s",
            str(len(result["noisy_parameters_found"])),
            str(len(result["idempotency_violations"]))
        )

    console.print(table)

def main():
    parser = argparse.ArgumentParser(description="Test Suite Idempotency Checker")
    parser.add_argument("--test-cases", type=str, help="Path to test cases JSON file")
    parser.add_argument("--output", type=str, default="allure-results", help="Output directory for reports")
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    parser.add_argument("--json", action="store_true", help="Generate JSON report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Initialize components
    checker = IdempotencyChecker()
    report_generator = ReportGenerator()

    # Load test cases
    if args.test_cases:
        test_cases = load_test_cases(args.test_cases)
    else:
        console.print("[yellow]No test cases file provided. Using example test cases.[/yellow]")
        from tests.test_idempotency import TEST_CASES
        test_cases = TEST_CASES

    # Run tests with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Running tests...", total=len(test_cases))
        
        for test_case in test_cases:
            if args.verbose:
                console.print(f"\n[cyan]Running test: {test_case.name}[/cyan]")
            
            result = checker.check_test_case(test_case)
            report_generator.add_test_result(result)
            
            if args.verbose:
                if result.success:
                    console.print("[green]✓ Test passed[/green]")
                else:
                    console.print("[red]✗ Test failed[/red]")
                    if result.error_message:
                        console.print(f"[red]Error: {result.error_message}[/red]")
                    if result.noisy_parameters_found:
                        console.print("[yellow]Noisy parameters found:[/yellow]")
                        for param in result.noisy_parameters_found:
                            console.print(f"  - {param}")
                    if result.idempotency_violations:
                        console.print("[yellow]Idempotency violations found:[/yellow]")
                        for violation in result.idempotency_violations:
                            console.print(f"  - {violation}")
            
            progress.advance(task)

    # Generate reports
    if args.html:
        console.print("\n[cyan]Generating HTML report...[/cyan]")
        report_generator.generate_html_report(args.output)
        console.print("[green]HTML report generated successfully![/green]")

    if args.json:
        console.print("\n[cyan]Generating JSON report...[/cyan]")
        report = report_generator.generate_json_report()
        with open(f"{args.output}/test_results.json", 'w') as f:
            json.dump(report, f, indent=2)
        console.print("[green]JSON report generated successfully![/green]")

    # Display summary
    console.print("\n[bold cyan]Test Summary:[/bold cyan]")
    display_results([result.dict() for result in report_generator.test_results])

if __name__ == "__main__":
    main() 