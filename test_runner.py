"""
Test execution engine for running and validating tests.
"""
import subprocess
import os
import re
from typing import Dict, Any, Optional, List
from database import Database


class TestRunner:
    """
    Executes tests and parses results.
    Supports pytest and unittest.
    """
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initialize test runner.
        
        Args:
            db: Optional database instance for saving results
        """
        self.db = db
    
    def execute_pytest(
        self, 
        project_directory: str,
        test_file: Optional[str] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Execute pytest in project directory.
        
        Args:
            project_directory: Directory containing tests
            test_file: Specific test file to run (optional)
            timeout: Timeout in seconds
            
        Returns:
            Dict with execution results
        """
        try:
            # Build pytest command
            cmd = ['pytest', '-v', '--tb=short']
            
            if test_file:
                cmd.append(test_file)
            
            # Execute pytest
            result = subprocess.run(
                cmd,
                cwd=project_directory,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = result.stdout + "\n" + result.stderr
            
            # Parse results
            test_results = self.parse_pytest_output(output)
            test_results['full_output'] = output
            test_results['returncode'] = result.returncode
            test_results['passed'] = result.returncode == 0
            
            return test_results
            
        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'total': 0,
                'passed_count': 0,
                'failed_count': 0,
                'error': 'Tests timed out',
                'full_output': '',
                'returncode': -1
            }
        except FileNotFoundError:
            return {
                'passed': False,
                'total': 0,
                'passed_count': 0,
                'failed_count': 0,
                'error': 'pytest not found - install with: pip install pytest',
                'full_output': '',
                'returncode': -1
            }
        except Exception as e:
            return {
                'passed': False,
                'total': 0,
                'passed_count': 0,
                'failed_count': 0,
                'error': str(e),
                'full_output': '',
                'returncode': -1
            }
    
    def execute_unittest(
        self,
        project_directory: str,
        test_module: Optional[str] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Execute unittest in project directory.
        
        Args:
            project_directory: Directory containing tests
            test_module: Specific test module (optional)
            timeout: Timeout in seconds
            
        Returns:
            Dict with execution results
        """
        try:
            # Build unittest command
            cmd = ['python', '-m', 'unittest']
            
            if test_module:
                cmd.append(test_module)
            else:
                cmd.append('discover')
            
            cmd.extend(['-v'])
            
            # Execute unittest
            result = subprocess.run(
                cmd,
                cwd=project_directory,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = result.stdout + "\n" + result.stderr
            
            # Parse results
            test_results = self.parse_unittest_output(output)
            test_results['full_output'] = output
            test_results['returncode'] = result.returncode
            test_results['passed'] = result.returncode == 0
            
            return test_results
            
        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'total': 0,
                'passed_count': 0,
                'failed_count': 0,
                'error': 'Tests timed out',
                'full_output': '',
                'returncode': -1
            }
        except Exception as e:
            return {
                'passed': False,
                'total': 0,
                'passed_count': 0,
                'failed_count': 0,
                'error': str(e),
                'full_output': '',
                'returncode': -1
            }
    
    def parse_pytest_output(self, output: str) -> Dict[str, Any]:
        """
        Parse pytest output to extract results.
        
        Args:
            output: pytest output text
            
        Returns:
            Dict with parsed results
        """
        results = {
            'total': 0,
            'passed_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'error_count': 0,
            'failed_tests': [],
            'warnings': []
        }
        
        # Look for summary line like "5 passed, 2 failed in 1.23s"
        summary_pattern = r'(\d+)\s+passed'
        passed_match = re.search(summary_pattern, output)
        if passed_match:
            results['passed_count'] = int(passed_match.group(1))
        
        failed_pattern = r'(\d+)\s+failed'
        failed_match = re.search(failed_pattern, output)
        if failed_match:
            results['failed_count'] = int(failed_match.group(1))
        
        skipped_pattern = r'(\d+)\s+skipped'
        skipped_match = re.search(skipped_pattern, output)
        if skipped_match:
            results['skipped_count'] = int(skipped_match.group(1))
        
        error_pattern = r'(\d+)\s+error'
        error_match = re.search(error_pattern, output)
        if error_match:
            results['error_count'] = int(error_match.group(1))
        
        results['total'] = (results['passed_count'] + results['failed_count'] + 
                           results['skipped_count'] + results['error_count'])
        
        # Extract failed test names
        failed_test_pattern = r'FAILED\s+([^\s]+)'
        results['failed_tests'] = re.findall(failed_test_pattern, output)
        
        # Extract warnings
        warning_pattern = r'(WARNING|warning):\s*([^\n]+)'
        results['warnings'] = re.findall(warning_pattern, output)
        
        return results
    
    def parse_unittest_output(self, output: str) -> Dict[str, Any]:
        """
        Parse unittest output to extract results.
        
        Args:
            output: unittest output text
            
        Returns:
            Dict with parsed results
        """
        results = {
            'total': 0,
            'passed_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'error_count': 0,
            'failed_tests': [],
            'warnings': []
        }
        
        # Look for summary like "Ran 10 tests in 0.001s"
        ran_pattern = r'Ran\s+(\d+)\s+test'
        ran_match = re.search(ran_pattern, output)
        if ran_match:
            results['total'] = int(ran_match.group(1))
        
        # Look for failures
        failure_pattern = r'failures=(\d+)'
        failure_match = re.search(failure_pattern, output)
        if failure_match:
            results['failed_count'] = int(failure_match.group(1))
        
        # Look for errors
        error_pattern = r'errors=(\d+)'
        error_match = re.search(error_pattern, output)
        if error_match:
            results['error_count'] = int(error_match.group(1))
        
        # Calculate passed
        results['passed_count'] = (results['total'] - results['failed_count'] - 
                                   results['error_count'])
        
        # Extract failed test names
        failed_test_pattern = r'FAIL:\s+([^\n]+)'
        results['failed_tests'] = re.findall(failed_test_pattern, output)
        
        return results
    
    def execute_and_save(
        self,
        task_id: int,
        project_directory: str,
        test_file: Optional[str] = None,
        test_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute tests and save results to database.
        
        Args:
            task_id: Task ID for database
            project_directory: Project directory
            test_file: Test file to run
            test_code: Test code content (for reference)
            
        Returns:
            Test execution results
        """
        # Execute tests
        results = self.execute_pytest(project_directory, test_file)
        
        # Save to database if available
        if self.db:
            self.db.save_test_execution(
                task_id=task_id,
                test_code=test_code or '',
                execution_output=results.get('full_output', ''),
                passed=results.get('passed', False),
                validation_notes=None  # Will be filled by orchestration brain
            )
        
        return results
    
    def format_results_summary(self, results: Dict[str, Any]) -> str:
        """
        Format test results into human-readable summary.
        
        Args:
            results: Test results dict
            
        Returns:
            Formatted summary string
        """
        if results.get('error'):
            return f"❌ Test Execution Error: {results['error']}"
        
        total = results.get('total', 0)
        passed = results.get('passed_count', 0)
        failed = results.get('failed_count', 0)
        
        summary = f"📊 Test Results: {passed}/{total} passed"
        
        if failed > 0:
            summary += f", {failed} failed ❌"
            if results.get('failed_tests'):
                summary += "\n\nFailed tests:"
                for test in results['failed_tests'][:5]:  # Show first 5
                    summary += f"\n  • {test}"
        else:
            summary += " ✅"
        
        if results.get('skipped_count', 0) > 0:
            summary += f"\n⏭️  {results['skipped_count']} skipped"
        
        if results.get('warnings'):
            summary += f"\n⚠️  {len(results['warnings'])} warnings"
        
        return summary
    
    def check_test_files_exist(self, project_directory: str) -> List[str]:
        """
        Check for existing test files in project.
        
        Args:
            project_directory: Project directory
            
        Returns:
            List of test file paths
        """
        test_files = []
        
        if not os.path.exists(project_directory):
            return test_files
        
        # Common test file patterns
        patterns = ['test_*.py', '*_test.py', 'test*.py']
        
        for root, dirs, files in os.walk(project_directory):
            # Skip common non-test directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', 'env', 'node_modules']]
            
            for file in files:
                if file.startswith('test') and file.endswith('.py'):
                    test_files.append(os.path.join(root, file))
        
        return test_files


