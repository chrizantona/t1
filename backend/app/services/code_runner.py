"""
Code execution service.
Runs candidate code in isolated environment.
"""
import subprocess
import json
import time
import ast
from typing import Dict, List, Any


def run_code(
    code: str,
    language: str,
    visible_tests: List[Dict[str, Any]],
    hidden_tests: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Run code against test cases.
    """
    result = {
        "passed_visible": 0,
        "total_visible": len(visible_tests),
        "passed_hidden": 0,
        "total_hidden": len(hidden_tests),
        "execution_time_ms": None,
        "error_message": None,
        "visible_test_details": []
    }
    
    try:
        start_time = time.time()
        
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
            result["error_message"] = "JavaScript execution coming soon"
        else:
            result["error_message"] = f"Language {language} not yet supported"
        
        execution_time = (time.time() - start_time) * 1000
        result["execution_time_ms"] = round(execution_time, 2)
        
    except SyntaxError as e:
        result["error_message"] = f"Syntax Error: {str(e)}"
    except Exception as e:
        result["error_message"] = f"Runtime Error: {str(e)}"
    
    return result


def create_execution_env():
    """Create safe execution environment with all needed imports."""
    # Import typing for annotations
    import typing
    
    env = {
        "__builtins__": __builtins__,
        # Typing support
        "List": typing.List,
        "Dict": typing.Dict,
        "Set": typing.Set,
        "Tuple": typing.Tuple,
        "Optional": typing.Optional,
        "Any": typing.Any,
        "Union": typing.Union,
        # Built-in types (for runtime)
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "sorted": sorted,
        "reversed": reversed,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "all": all,
        "any": any,
        "print": print,
    }
    return env


def run_single_python_test_detailed(code: str, test: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a single Python test with detailed results.
    """
    result = {
        "passed": False,
        "actual": None,
        "error": None
    }
    
    try:
        local_vars = {}
        global_vars = create_execution_env()
        
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
        
        args, kwargs = parse_test_input(test_input)
        
        # Run the function
        actual = solution_func(*args, **kwargs)
        result["actual"] = actual
        
        # Parse expected
        expected_val = parse_expected(expected)
        
        # Compare
        result["passed"] = compare_results(actual, expected_val)
        
        print(f"🧪 Test: input={test_input}, expected={expected_val}, actual={actual}, passed={result['passed']}")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ Test FAILED with exception: {e}")
    
    return result


def run_single_python_test(code: str, test: Dict[str, Any]) -> bool:
    """
    Run a single Python test.
    Returns True if test passed, False otherwise.
    """
    try:
        local_vars = {}
        global_vars = create_execution_env()
        
        # Execute the code
        exec(code, global_vars, local_vars)
        
        # Find the solution function
        solution_func = None
        for name, obj in local_vars.items():
            if callable(obj) and not name.startswith('_'):
                solution_func = obj
                break
        
        if not solution_func:
            print(f"⚠️ No solution function found")
            return False
        
        # Parse test input
        test_input = test.get("input")
        expected = test.get("expected_output") or test.get("expected")
        
        args, kwargs = parse_test_input(test_input)
        
        # Run the function
        actual = solution_func(*args, **kwargs)
        
        # Parse expected
        expected_val = parse_expected(expected)
        
        # Compare
        passed = compare_results(actual, expected_val)
        
        if passed:
            print(f"✅ Hidden test PASSED")
        else:
            print(f"❌ Hidden test FAILED: expected={expected_val}, actual={actual}")
        
        return passed
        
    except Exception as e:
        print(f"❌ Hidden test exception: {e}")
        return False


def parse_test_input(test_input):
    """Parse test input into args and kwargs."""
    args = []
    kwargs = {}
    
    if test_input is None:
        return args, kwargs
    
    if isinstance(test_input, str):
        test_input = test_input.strip()
        
        try:
            # Try to parse as Python call arguments
            fake_call = f"func({test_input})"
            tree = ast.parse(fake_call)
            call_node = tree.body[0].value
            
            # Extract args
            for arg in call_node.args:
                try:
                    args.append(ast.literal_eval(arg))
                except:
                    # If literal_eval fails, try compile+eval
                    code = compile(ast.Expression(arg), '<string>', 'eval')
                    args.append(eval(code))
            
            # Extract kwargs
            for kw in call_node.keywords:
                try:
                    kwargs[kw.arg] = ast.literal_eval(kw.value)
                except:
                    code = compile(ast.Expression(kw.value), '<string>', 'eval')
                    kwargs[kw.arg] = eval(code)
                    
        except:
            # Fallback: try simple literal eval
            try:
                val = ast.literal_eval(test_input)
                if isinstance(val, (list, tuple)):
                    args = list(val)
                else:
                    args = [val]
            except:
                args = [test_input]
    else:
        # Already parsed
        if isinstance(test_input, (list, tuple)):
            args = list(test_input)
        elif isinstance(test_input, dict):
            kwargs = test_input
        else:
            args = [test_input]
    
    return args, kwargs


def parse_expected(expected):
    """Parse expected value."""
    if expected is None:
        return None
    
    if isinstance(expected, str):
        try:
            return ast.literal_eval(expected)
        except:
            return expected
    
    return expected


def compare_results(actual, expected):
    """Compare actual result with expected."""
    # Direct comparison
    if actual == expected:
        return True
    
    # Try string comparison
    if str(actual) == str(expected):
        return True
    
    # For lists, try sorted comparison (for problems where order doesn't matter)
    if isinstance(actual, list) and isinstance(expected, list):
        if len(actual) == len(expected):
            # Try direct comparison first
            if actual == expected:
                return True
            # Don't sort - order usually matters
    
    return False
