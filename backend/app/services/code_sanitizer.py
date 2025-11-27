"""
Code Sanitizer Service - Protection against prompt injection and malicious code.
Sanitizes user code before sending to LLM or executing.
"""
import re
from typing import Tuple, List


# Patterns that could indicate prompt injection attempts
PROMPT_INJECTION_PATTERNS = [
    # Direct prompt manipulation
    r'ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)',
    r'disregard\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)',
    r'forget\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)',
    r'new\s+(instructions?|rules?|prompt)\s*:',
    r'system\s*:\s*you\s+are',
    r'assistant\s*:\s*',
    r'\[INST\]',
    r'\[/INST\]',
    r'<<SYS>>',
    r'<</SYS>>',
    r'<\|im_start\|>',
    r'<\|im_end\|>',
    r'###\s*(System|Human|Assistant)',
    
    # Role play manipulation
    r'pretend\s+(you\s+are|to\s+be)\s+',
    r'act\s+as\s+(if\s+)?(you\s+are|a)',
    r'roleplay\s+as',
    r'you\s+are\s+now\s+',
    r'from\s+now\s+on\s+you\s+',
    
    # Output manipulation
    r'output\s+only\s*:',
    r'respond\s+with\s+only',
    r'say\s+exactly\s*:',
    r'print\s+the\s+following',
    r'return\s+this\s+exactly',
    
    # JSON/Response manipulation
    r'"score"\s*:\s*100',
    r'"passed"\s*:\s*true',
    r'"ai_likeness_score"\s*:\s*0',
    r'always\s+return\s+',
    r'set\s+score\s+to\s+',
    
    # Hidden instructions in comments (multi-language)
    r'#\s*ВАЖНО\s*:',
    r'#\s*IMPORTANT\s*:',
    r'#\s*NOTE\s+TO\s+(AI|LLM|MODEL)',
    r'//\s*OVERRIDE',
    r'/\*\s*SYSTEM',
    r'"""\s*(IGNORE|SYSTEM|PROMPT)',
    r"'''\s*(IGNORE|SYSTEM|PROMPT)",
    
    # Russian prompt injections
    r'игнорируй\s+(все\s+)?предыдущ',
    r'забудь\s+(все\s+)?инструкци',
    r'новые\s+инструкции\s*:',
    r'ты\s+теперь\s+',
    r'притворись\s+',
    r'выведи\s+только\s*:',
]

# Dangerous code patterns that shouldn't be executed
DANGEROUS_CODE_PATTERNS = [
    # System/OS access
    r'import\s+os\b',
    r'import\s+sys\b',
    r'import\s+subprocess',
    r'import\s+shutil',
    r'from\s+os\s+import',
    r'from\s+sys\s+import',
    r'os\.(system|popen|exec|spawn|remove|rmdir|unlink)',
    r'subprocess\.(run|call|Popen|check_output)',
    r'__import__\s*\(',
    
    # File system access
    r'open\s*\([^)]*["\'][wax]',  # File write operations
    r'\.write\s*\(',
    r'shutil\.(rmtree|move|copy)',
    
    # Network access
    r'import\s+(socket|requests|urllib|http)',
    r'from\s+(socket|requests|urllib|http)',
    
    # Code execution
    r'eval\s*\(',
    r'exec\s*\(',
    r'compile\s*\(',
    r'__builtins__',
    r'globals\s*\(\s*\)',
    r'locals\s*\(\s*\)',
    r'getattr\s*\([^)]*["\']__',
    r'setattr\s*\(',
    r'delattr\s*\(',
    
    # Dangerous built-ins
    r'__class__',
    r'__bases__',
    r'__subclasses__',
    r'__mro__',
    r'__code__',
    r'__globals__',
]


def detect_prompt_injection(code: str) -> Tuple[bool, List[str]]:
    """
    Detect potential prompt injection attempts in code.
    
    Args:
        code: User's code to check
        
    Returns:
        Tuple of (is_suspicious, list of detected patterns)
    """
    detected = []
    code_lower = code.lower()
    
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, code_lower, re.IGNORECASE):
            detected.append(pattern)
    
    return len(detected) > 0, detected


def detect_dangerous_code(code: str) -> Tuple[bool, List[str]]:
    """
    Detect potentially dangerous code patterns.
    
    Args:
        code: User's code to check
        
    Returns:
        Tuple of (is_dangerous, list of detected patterns)
    """
    detected = []
    
    for pattern in DANGEROUS_CODE_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            detected.append(pattern)
    
    return len(detected) > 0, detected


def sanitize_code_for_llm(code: str) -> Tuple[str, dict]:
    """
    Sanitize code before sending to LLM.
    Removes or escapes potentially dangerous content.
    
    Args:
        code: User's code
        
    Returns:
        Tuple of (sanitized_code, report_dict)
    """
    report = {
        "original_length": len(code),
        "prompt_injection_detected": False,
        "dangerous_code_detected": False,
        "modifications": [],
        "warnings": [],
        "is_safe": True
    }
    
    # Check for prompt injection
    is_suspicious, injection_patterns = detect_prompt_injection(code)
    if is_suspicious:
        report["prompt_injection_detected"] = True
        report["warnings"].append(f"Обнаружены подозрительные паттерны: {len(injection_patterns)} шт.")
        report["is_safe"] = False
    
    # Check for dangerous code
    is_dangerous, dangerous_patterns = detect_dangerous_code(code)
    if is_dangerous:
        report["dangerous_code_detected"] = True
        report["warnings"].append(f"Обнаружен потенциально опасный код: {len(dangerous_patterns)} шт.")
    
    # Sanitize the code
    sanitized = code
    
    # Escape special LLM tokens/markers that could confuse the model
    llm_tokens = [
        ('```', '` ` `'),
        ('"""', '" " "'),
        ("'''", "' ' '"),
        ('<|', '< |'),
        ('|>', '| >'),
        ('<<', '< <'),
        ('>>', '> >'),
        ('[INST]', '[I N S T]'),
        ('[/INST]', '[/ I N S T]'),
    ]
    
    for token, replacement in llm_tokens:
        if token in sanitized:
            count = sanitized.count(token)
            sanitized = sanitized.replace(token, replacement)
            report["modifications"].append(f"Заменено '{token}' -> '{replacement}' ({count} раз)")
    
    # Wrap code in clear delimiters for LLM context
    wrapped_code = f"[CODE_START]\n{sanitized}\n[CODE_END]"
    
    report["sanitized_length"] = len(wrapped_code)
    
    return wrapped_code, report


def extract_code_from_wrapped(wrapped_code: str) -> str:
    """
    Extract original code from wrapped format.
    
    Args:
        wrapped_code: Code wrapped with [CODE_START]/[CODE_END]
        
    Returns:
        Original code without wrappers
    """
    if "[CODE_START]" in wrapped_code and "[CODE_END]" in wrapped_code:
        start = wrapped_code.find("[CODE_START]") + len("[CODE_START]")
        end = wrapped_code.find("[CODE_END]")
        return wrapped_code[start:end].strip()
    return wrapped_code


def get_security_summary(code: str) -> dict:
    """
    Get a comprehensive security summary for the code.
    
    Args:
        code: User's code
        
    Returns:
        Security summary dict
    """
    injection_detected, injection_patterns = detect_prompt_injection(code)
    dangerous_detected, dangerous_patterns = detect_dangerous_code(code)
    
    risk_level = "low"
    if injection_detected:
        risk_level = "high"
    elif dangerous_detected:
        risk_level = "medium"
    
    return {
        "risk_level": risk_level,
        "prompt_injection": {
            "detected": injection_detected,
            "count": len(injection_patterns)
        },
        "dangerous_code": {
            "detected": dangerous_detected,
            "count": len(dangerous_patterns)
        },
        "recommendation": _get_recommendation(risk_level, injection_detected, dangerous_detected)
    }


def _get_recommendation(risk_level: str, injection: bool, dangerous: bool) -> str:
    """Get recommendation based on risk assessment."""
    if injection:
        return "ЗАБЛОКИРОВАТЬ: Обнаружена попытка манипуляции LLM. Код не должен отправляться на проверку."
    elif dangerous:
        return "ВНИМАНИЕ: Код содержит потенциально опасные операции. Выполнение должно быть в изолированной среде."
    else:
        return "ОК: Код прошёл базовую проверку безопасности."





