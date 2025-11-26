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
        Dict with test results including detailed visible test results
    """
    # For MVP, we'll simulate code execution
    # In production, this would use docker exec or similar
    
    result = {
        "passed_visible": 0,
        "total_visible": len(visible_tests),
        "passed_hidden": 0,
        "total_hidden": len(hidden_tests),
        "execution_time_ms": None,
        "error_message": None,
        "visible_test_details": []  # Detailed results for visible tests
    }
    
    try:
        start_time = time.time()
        
        # Execute code against tests
        if language == "python":
            # Test visible cases with detailed results
            for i, test in enumerate(visible_tests):
                test_result = run_single_python_test_detailed(code, test)
                test_result["index"] = i + 1
                test_result["input"] = test.get("input")
                test_result["expected"] = test.get("expected_output") or test.get("expected")
                test_result["description"] = test.get("description", "")
                result["visible_test_details"].append(test_result)
                if test_result["passed"]:
                    result["passed_visible"] += 1
            
            # Test hidden cases (no details exposed)
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


def run_single_python_test_detailed(code: str, test: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a single Python test case and return detailed results.
    
    Args:
        code: Python code to test
        test: Test case with input and expected_output
    
    Returns:
        Dict with passed status, actual output, and error if any
    """
    result = {
        "passed": False,
        "actual": None,
        "error": None
    }
    
    try:
        # Create a safe execution environment with common imports
        local_vars = {}
        global_vars = {
            "__builtins__": __builtins__,
            "List": list,
            "Dict": dict,
            "Set": set,
            "Tuple": tuple,
            "Optional": lambda x: x,
        }
        
        # Execute the code
        exec(code, global_vars, local_vars)
        
        # Find the solution function
        solution_func = None
        for name, obj in local_vars.items():
            if callable(obj) and not name.startswith('_'):
                solution_func = obj
                break
        
        if not solution_func:
            result["error"] = "Функция решения не найдена"
            return result
        
        # Parse test input
        test_input = test.get("input")
        expected = test.get("expected_output") or test.get("expected")
        
        # Handle different input formats
        import ast
        
        args = []
        kwargs = {}
        
        if isinstance(test_input, str):
            test_input = test_input.strip()
            try:
                fake_call = f"func({test_input})"
                tree = ast.parse(fake_call)
                call_node = tree.body[0].value
                args = [ast.literal_eval(arg) for arg in call_node.args]
                kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in call_node.keywords}
            except:
                try:
                    test_input = ast.literal_eval(test_input)
                    if isinstance(test_input, (list, tuple)):
                        args = list(test_input)
                    else:
                        args = [test_input]
                except:
                    args = [test_input]
        else:
            if isinstance(test_input, (list, tuple)):
                args = list(test_input)
            elif isinstance(test_input, dict):
                kwargs = test_input
            else:
                args = [test_input]
        
        # Run the function
        if kwargs:
            actual = solution_func(*args, **kwargs)
        else:
            actual = solution_func(*args)
        
        result["actual"] = actual
        
        # Parse expected output
        if isinstance(expected, str):
            try:
                expected = ast.literal_eval(expected)
            except:
                pass
        
        # Compare result
        result["passed"] = actual == expected
        
    except Exception as e:
        result["error"] = str(e)
    
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
        # Create a safe execution environment with common imports
        local_vars = {}
        global_vars = {
            "__builtins__": __builtins__,
            "List": list,
            "Dict": dict,
            "Set": set,
            "Tuple": tuple,
            "Optional": lambda x: x,
        }
        
        # Execute the code
        exec(code, global_vars, local_vars)
        
        # Find the solution function
        solution_func = None
        for name, obj in local_vars.items():
            if callable(obj) and not name.startswith('_'):
                solution_func = obj
                break
        
        if not solution_func:
            print(f"⚠️ No solution function found in code")
            return False
        
        # Parse test input
        test_input = test.get("input")
        expected = test.get("expected_output") or test.get("expected")
        
        print(f"🧪 Testing: input={test_input}, expected={expected}")
        
        # Handle different input formats
        import ast
        import re
        
        args = []
        kwargs = {}
        
        if isinstance(test_input, str):
            # Parse string like "[2,7,11,15], target=9" or "[3,2,4], 6"
            test_input = test_input.strip()
            
            # Try to parse as Python call arguments
            try:
                # Create a fake function call and parse it
                fake_call = f"func({test_input})"
                tree = ast.parse(fake_call)
                call_node = tree.body[0].value
                
                # Extract args and kwargs
                args = [ast.literal_eval(arg) for arg in call_node.args]
                kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in call_node.keywords}
            except:
                # Fallback: try simple literal eval
                try:
                    test_input = ast.literal_eval(test_input)
                    if isinstance(test_input, (list, tuple)):
                        args = list(test_input)
                    else:
                        args = [test_input]
                except:
                    args = [test_input]
        else:
            # Already parsed (list/dict)
            if isinstance(test_input, (list, tuple)):
                args = list(test_input)
            elif isinstance(test_input, dict):
                kwargs = test_input
            else:
                args = [test_input]
        
        # Run the function
        if kwargs:
            result = solution_func(*args, **kwargs)
        else:
            result = solution_func(*args)
        
        # Parse expected output
        if isinstance(expected, str):
            try:
                import ast
                expected = ast.literal_eval(expected)
            except:
                pass
        
        # Compare result
        passed = result == expected
        if passed:
            print(f"✅ Test PASSED: result={result}")
        else:
            print(f"❌ Test FAILED: result={result}, expected={expected}")
        
        return passed
        
    except Exception as e:
        # Test failed
        print(f"❌ Test FAILED with exception: {e}")
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


def run_edge_case_tests(
    code: str,
    language: str,
    edge_case_tests: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Run code against enhanced edge case tests with expected outputs.
    Part of AI Bug Hunter Enhanced feature.
    
    Args:
        code: Code to test
        language: Programming language
        edge_case_tests: List of edge case tests with input, expected_output, category
    
    Returns:
        Detailed test results
    """
    from .code_sanitizer import detect_dangerous_code
    
    # Security check before execution
    is_dangerous, patterns = detect_dangerous_code(code)
    if is_dangerous:
        return {
            "executed": False,
            "security_blocked": True,
            "reason": "Обнаружен потенциально опасный код",
            "dangerous_patterns": len(patterns),
            "results": []
        }
    
    results = {
        "executed": True,
        "security_blocked": False,
        "total_tests": len(edge_case_tests),
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "results": []
    }
    
    for i, test in enumerate(edge_case_tests):
        test_result = {
            "test_index": i,
            "input": test.get("input"),
            "expected": test.get("expected_output") or test.get("expected"),
            "category": test.get("category", "unknown"),
            "description": test.get("description", ""),
            "status": "pending",
            "actual_output": None,
            "error": None
        }
        
        # Convert to format expected by run_single_python_test
        formatted_test = {
            "input": test.get("input"),
            "expected_output": test.get("expected_output") or test.get("expected")
        }
        
        if language == "python":
            try:
                passed = run_single_python_test(code, formatted_test)
                if passed:
                    test_result["status"] = "passed"
                    results["passed"] += 1
                else:
                    test_result["status"] = "failed"
                    results["failed"] += 1
            except Exception as e:
                test_result["status"] = "error"
                test_result["error"] = str(e)
                results["errors"] += 1
        else:
            test_result["status"] = "skipped"
            test_result["error"] = f"Language {language} not supported"
        
        results["results"].append(test_result)
    
    return results


def validate_code_safety(code: str) -> Dict[str, Any]:
    """
    Validate code safety before any processing.
    
    Args:
        code: Code to validate
        
    Returns:
        Safety validation result
    """
    from .code_sanitizer import get_security_summary
    return get_security_summary(code)

