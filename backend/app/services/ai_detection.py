"""
AI Code Detection Service.

Detects if candidate's code looks AI-generated:
1. Compare with reference solutions via bge-m3 embeddings
2. LLM-based style analysis (CLASSIFY_AI_LIKE intent)
3. Aggregate into cheat_signals
"""
import json
import re
from typing import Dict, Any, List, Optional
import numpy as np

from .scibox_client import scibox_client
from .llm_protocol import classify_ai_like
from ..core.config import settings


# Reference solutions for comparison (simplified versions)
REFERENCE_SOLUTIONS = {
    "two_sum": """
def twoSum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
""",
    "palindrome": """
def isPalindrome(x):
    if x < 0:
        return False
    return str(x) == str(x)[::-1]
""",
    "max_subarray": """
def maxSubArray(nums):
    max_sum = current_sum = nums[0]
    for num in nums[1:]:
        current_sum = max(num, current_sum + num)
        max_sum = max(max_sum, current_sum)
    return max_sum
""",
    "binary_search": """
def search(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
""",
    "fibonacci": """
def fib(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
""",
    "valid_parentheses": """
def isValid(s):
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    for char in s:
        if char in mapping:
            if not stack or stack.pop() != mapping[char]:
                return False
        else:
            stack.append(char)
    return not stack
""",
    "contains_duplicate": """
def containsDuplicate(nums):
    return len(nums) != len(set(nums))
""",
    "fizzbuzz": """
def fizzBuzz(n):
    result = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            result.append("FizzBuzz")
        elif i % 3 == 0:
            result.append("Fizz")
        elif i % 5 == 0:
            result.append("Buzz")
        else:
            result.append(str(i))
    return result
"""
}


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a = np.array(vec1)
    b = np.array(vec2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


async def get_embedding(text: str) -> List[float]:
    """Get embedding for text using bge-m3 model."""
    try:
        return await scibox_client.get_embedding(text)
    except Exception as e:
        print(f"Embedding error: {e}")
        return []


async def calculate_code_similarity(
    candidate_code: str,
    task_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate similarity between candidate's code and reference solutions.
    Uses bge-m3 embeddings.
    
    Args:
        candidate_code: Candidate's submitted code
        task_key: Optional task key to compare with specific reference
        
    Returns:
        {
            "max_similarity": 0.0..1.0,
            "matched_reference": "task_key" or None,
            "all_similarities": {task_key: similarity, ...}
        }
    """
    if not candidate_code or len(candidate_code.strip()) < 10:
        return {
            "max_similarity": 0.0,
            "matched_reference": None,
            "all_similarities": {}
        }
    
    # Get embedding for candidate code
    candidate_embedding = await get_embedding(candidate_code)
    
    if not candidate_embedding:
        return {
            "max_similarity": 0.0,
            "matched_reference": None,
            "all_similarities": {},
            "error": "Failed to get embedding"
        }
    
    # Compare with references
    similarities = {}
    max_similarity = 0.0
    matched_reference = None
    
    # If task_key specified, only compare with that reference
    references_to_check = {task_key: REFERENCE_SOLUTIONS[task_key]} if task_key and task_key in REFERENCE_SOLUTIONS else REFERENCE_SOLUTIONS
    
    for ref_key, ref_code in references_to_check.items():
        ref_embedding = await get_embedding(ref_code)
        
        if ref_embedding:
            similarity = cosine_similarity(candidate_embedding, ref_embedding)
            similarities[ref_key] = similarity
            
            if similarity > max_similarity:
                max_similarity = similarity
                matched_reference = ref_key
    
    return {
        "max_similarity": max_similarity,
        "matched_reference": matched_reference,
        "all_similarities": similarities
    }


async def detect_ai_generated_code(code: str) -> Dict[str, Any]:
    """
    Use LLM to detect if code looks AI-generated.
    
    Returns:
        {
            "ai_style_score": 0.0..1.0,
            "signals": ["..."],
            "explanation": "..."
        }
    """
    result = await classify_ai_like(code)
    
    # Ensure we have required fields
    if "error" in result:
        return {
            "ai_style_score": 0.0,
            "signals": [],
            "explanation": result.get("error", "Analysis failed")
        }
    
    return {
        "ai_style_score": result.get("ai_style_score", 0.0),
        "signals": result.get("signals", []),
        "explanation": result.get("explanation", "")
    }


async def full_ai_detection(
    candidate_code: str,
    task_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Full AI detection pipeline:
    1. Calculate code similarity with references
    2. LLM-based AI style detection
    3. Combine results
    
    Args:
        candidate_code: Candidate's submitted code
        task_key: Optional task key for targeted comparison
        
    Returns:
        {
            "code_similarity_score": 0.0..1.0,
            "ai_style_score": 0.0..1.0,
            "combined_risk": 0.0..1.0,
            "risk_level": "low|medium|high",
            "signals": [...],
            "details": {...}
        }
    """
    # Run both checks in parallel (conceptually)
    similarity_result = await calculate_code_similarity(candidate_code, task_key)
    ai_style_result = await detect_ai_generated_code(candidate_code)
    
    # Extract scores
    code_similarity = similarity_result.get("max_similarity", 0.0)
    ai_style_score = ai_style_result.get("ai_style_score", 0.0)
    
    # Combined risk calculation
    # Weight: 40% similarity, 60% AI style
    combined_risk = 0.4 * code_similarity + 0.6 * ai_style_score
    
    # Determine risk level
    if combined_risk >= 0.7:
        risk_level = "high"
    elif combined_risk >= 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    # Combine signals
    signals = ai_style_result.get("signals", [])
    if code_similarity > 0.8:
        signals.append(f"Высокое сходство с эталонным решением ({similarity_result.get('matched_reference')})")
    
    return {
        "code_similarity_score": code_similarity,
        "ai_style_score": ai_style_score,
        "combined_risk": combined_risk,
        "risk_level": risk_level,
        "signals": signals,
        "details": {
            "similarity": similarity_result,
            "ai_style": ai_style_result
        }
    }


def update_cheat_signals(
    current_signals: Dict[str, Any],
    ai_detection_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update interview's cheat_signals with AI detection results.
    
    Args:
        current_signals: Current cheat_signals dict from Interview
        ai_detection_result: Result from full_ai_detection
        
    Returns:
        Updated cheat_signals dict
    """
    if current_signals is None:
        current_signals = {
            "copy_paste_count": 0,
            "devtools_opened": False,
            "focus_lost_count": 0,
            "ai_style_score": 0.0,
            "code_similarity_score": 0.0
        }
    
    # Update with new detection results
    current_signals["ai_style_score"] = max(
        current_signals.get("ai_style_score", 0.0),
        ai_detection_result.get("ai_style_score", 0.0)
    )
    current_signals["code_similarity_score"] = max(
        current_signals.get("code_similarity_score", 0.0),
        ai_detection_result.get("code_similarity_score", 0.0)
    )
    
    return current_signals



# пидормот
