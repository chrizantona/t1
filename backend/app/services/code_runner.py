"""
Code execution service.
Runs candidate code in isolated environment.
"""
import subprocess
import json
import time
from typing import Dict, List, Any


def run_code(
    code: str,
    language: str,
    visible_tests: List[Dict[str, Any]],
    hidden_tests: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Run code against test cases.
    
    For MVP, this is a simplified version.
    In production, would use Docker containers for isolation.
    
    Args:
        code: Code to execute
        language: Programming language
        visible_tests: Visible test cases
        hidden_tests: Hidden test cases
    
    Returns:
        Dict with test results
    """
    # For MVP, we'll simulate code execution
    # In production, this would use docker exec or similar
    
    result = {
        "passed_visible": 0,
        "total_visible": len(visible_tests),
        "passed_hidden": 0,
        "total_hidden": len(hidden_tests),
        "execution_time_ms": None,
        "error_message": None
    }
    
    try:
        start_time = time.time()
        
        # Execute code against tests
        if language == "python":
            # Test visible cases
            for test in visible_tests:
                if run_single_python_test(code, test):
                    result["passed_visible"] += 1
            
            # Test hidden cases
            for test in hidden_tests:
                if run_single_python_test(code, test):
                    result["passed_hidden"] += 1
            
        elif language in ["javascript", "js"]:
            # JavaScript simulation
            result["error_message"] = "JavaScript execution coming soon"
            
        else:
            # Other languages - not yet supported
            result["error_message"] = f"Language {language} not yet supported"
        
        execution_time = (time.time() - start_time) * 1000
        result["execution_time_ms"] = round(execution_time, 2)
        
    except SyntaxError as e:
        result["error_message"] = f"Syntax Error: {str(e)}"
    except Exception as e:
        result["error_message"] = f"Runtime Error: {str(e)}"
    
    return result


def run_single_python_test(code: str, test: Dict[str, Any]) -> bool:
    """
    Run a single Python test case.
    
    Args:
        code: Python code to test
        test: Test case with input and expected_output
    
    Returns:
        True if test passed, False otherwise
    """
    try:
        # Create a safe execution environment
        local_vars = {}
        global_vars = {"__builtins__": __builtins__}
        
        # Execute the code
        exec(code, global_vars, local_vars)
        
        # Find the solution function
        solution_func = None
        for name, obj in local_vars.items():
            if callable(obj) and not name.startswith('_'):
                solution_func = obj
                break
        
        if not solution_func:
            return False
        
        # Parse test input
        test_input = test.get("input")
        expected = test.get("expected_output")
        
        # Handle different input formats
        if isinstance(test_input, str):
            # Try to parse as Python literal
            try:
                import ast
                test_input = ast.literal_eval(test_input)
            except:
                pass
        
        # Run the function
        if isinstance(test_input, (list, tuple)):
            result = solution_func(*test_input)
        elif isinstance(test_input, dict):
            result = solution_func(**test_input)
        else:
            result = solution_func(test_input)
        
        # Parse expected output
        if isinstance(expected, str):
            try:
                import ast
                expected = ast.literal_eval(expected)
            except:
                pass
        
        # Compare result
        return result == expected
        
    except Exception as e:
        # Test failed
        return False


def run_ai_generated_tests(
    code: str,
    language: str,
    ai_tests: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Run code against AI-generated edge case tests.
    Part of AI Bug Hunter feature.
    
    Args:
        code: Code to test
        language: Programming language
        ai_tests: AI-generated test cases
    
    Returns:
        Test results
    """
    return run_code(code, language, visible_tests=ai_tests, hidden_tests=[])

