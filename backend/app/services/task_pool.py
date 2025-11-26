"""
Task Pool - predefined tasks for reliable testing.
All tasks use functions that RETURN results (not in-place modification).
"""
from typing import Dict, List, Any

# Task Pool - Classic Algorithm Problems (all return values!)
TASK_POOL = {
    "two_sum": {
        "title": "Two Sum",
        "description": """Дан массив целых чисел nums и целое число target.

Верните индексы двух чисел таких, что их сумма равна target.

Можно предположить, что каждый вход имеет ровно одно решение, и нельзя использовать один и тот же элемент дважды.

Пример 1:
Вход: nums = [2,7,11,15], target = 9
Выход: [0,1]
Объяснение: nums[0] + nums[1] == 9, возвращаем [0, 1].

Пример 2:
Вход: nums = [3,2,4], target = 6
Выход: [1,2]

Ограничения:
- 2 <= nums.length <= 10^4
- -10^9 <= nums[i] <= 10^9
- Только одно валидное решение

Сигнатура функции:
def twoSum(nums: List[int], target: int) -> List[int]:""",
        "difficulty": "easy",
        "category": "arrays",
        "visible_tests": [
            {"input": "[2,7,11,15], 9", "expected_output": "[0,1]", "description": "Базовый случай"},
            {"input": "[3,2,4], 6", "expected_output": "[1,2]", "description": "Другие индексы"},
            {"input": "[3,3], 6", "expected_output": "[0,1]", "description": "Одинаковые числа"}
        ],
        "hidden_tests": [
            {"input": "[-1,-2,-3,-4,-5], -8", "expected_output": "[2,4]", "description": "Отрицательные числа"},
            {"input": "[1,5,3,7,2], 9", "expected_output": "[1,3]", "description": "Большой массив"}
        ]
    },
    
    "palindrome": {
        "title": "Проверка палиндрома",
        "description": """Целое число является палиндромом, если оно читается одинаково слева направо и справа налево.

Например, 121 является палиндромом, а 123 - нет.

Напишите функцию, которая определяет, является ли целое число палиндромом.

Пример 1:
Вход: x = 121
Выход: True

Пример 2:
Вход: x = -121
Выход: False
Объяснение: Слева направо это -121. Справа налево это 121-. Следовательно, это не палиндром.

Пример 3:
Вход: x = 10
Выход: False

Ограничения:
- -2^31 <= x <= 2^31 - 1

Сигнатура функции:
def isPalindrome(x: int) -> bool:""",
        "difficulty": "easy",
        "category": "math",
        "visible_tests": [
            {"input": "121", "expected_output": "True", "description": "Положительный палиндром"},
            {"input": "-121", "expected_output": "False", "description": "Отрицательное число"},
            {"input": "10", "expected_output": "False", "description": "Не палиндром"}
        ],
        "hidden_tests": [
            {"input": "0", "expected_output": "True", "description": "Ноль"},
            {"input": "12321", "expected_output": "True", "description": "Длинный палиндром"}
        ]
    },
    
    "max_subarray": {
        "title": "Максимальная сумма подмассива",
        "description": """Дан целочисленный массив nums, найдите подмассив с наибольшей суммой и верните его сумму.

Пример 1:
Вход: nums = [-2,1,-3,4,-1,2,1,-5,4]
Выход: 6
Объяснение: Подмассив [4,-1,2,1] имеет наибольшую сумму 6.

Пример 2:
Вход: nums = [1]
Выход: 1

Пример 3:
Вход: nums = [5,4,-1,7,8]
Выход: 23

Ограничения:
- 1 <= nums.length <= 10^5
- -10^4 <= nums[i] <= 10^4

Сигнатура функции:
def maxSubArray(nums: List[int]) -> int:""",
        "difficulty": "medium",
        "category": "dynamic_programming",
        "visible_tests": [
            {"input": "[-2,1,-3,4,-1,2,1,-5,4]", "expected_output": "6", "description": "Смешанные числа"},
            {"input": "[1]", "expected_output": "1", "description": "Один элемент"},
            {"input": "[5,4,-1,7,8]", "expected_output": "23", "description": "Большие числа"}
        ],
        "hidden_tests": [
            {"input": "[-1]", "expected_output": "-1", "description": "Одно отрицательное"},
            {"input": "[-2,-1]", "expected_output": "-1", "description": "Все отрицательные"}
        ]
    },
    
    "binary_search": {
        "title": "Бинарный поиск",
        "description": """Дан отсортированный массив целых чисел nums и целое число target, напишите функцию для поиска target в nums.

Если target существует, верните его индекс. В противном случае верните -1.

Вы должны написать алгоритм со сложностью выполнения O(log n).

Пример 1:
Вход: nums = [-1,0,3,5,9,12], target = 9
Выход: 4
Объяснение: 9 существует в nums и его индекс равен 4

Пример 2:
Вход: nums = [-1,0,3,5,9,12], target = 2
Выход: -1
Объяснение: 2 не существует в nums, поэтому вернуть -1

Ограничения:
- 1 <= nums.length <= 10^4
- -10^4 < nums[i], target < 10^4
- Все целые числа в nums уникальны
- nums отсортирован в возрастающем порядке

Сигнатура функции:
def search(nums: List[int], target: int) -> int:""",
        "difficulty": "easy",
        "category": "binary_search",
        "visible_tests": [
            {"input": "[-1,0,3,5,9,12], 9", "expected_output": "4", "description": "Элемент найден"},
            {"input": "[-1,0,3,5,9,12], 2", "expected_output": "-1", "description": "Элемент не найден"},
            {"input": "[5], 5", "expected_output": "0", "description": "Один элемент"}
        ],
        "hidden_tests": [
            {"input": "[1,2,3,4,5,6,7,8,9,10], 1", "expected_output": "0", "description": "Первый элемент"},
            {"input": "[1,2,3,4,5,6,7,8,9,10], 10", "expected_output": "9", "description": "Последний элемент"}
        ]
    },
    
    "fibonacci": {
        "title": "Число Фибоначчи",
        "description": """Числа Фибоначчи, обычно обозначаемые F(n), образуют последовательность, называемую последовательностью Фибоначчи.
Каждое число является суммой двух предыдущих, начиная с 0 и 1.

F(0) = 0, F(1) = 1
F(n) = F(n - 1) + F(n - 2), для n > 1.

Дано n, вычислите F(n).

Пример 1:
Вход: n = 2
Выход: 1
Объяснение: F(2) = F(1) + F(0) = 1 + 0 = 1.

Пример 2:
Вход: n = 3
Выход: 2
Объяснение: F(3) = F(2) + F(1) = 1 + 1 = 2.

Пример 3:
Вход: n = 4
Выход: 3
Объяснение: F(4) = F(3) + F(2) = 2 + 1 = 3.

Ограничения:
- 0 <= n <= 30

Сигнатура функции:
def fib(n: int) -> int:""",
        "difficulty": "easy",
        "category": "recursion",
        "visible_tests": [
            {"input": "2", "expected_output": "1", "description": "F(2)"},
            {"input": "3", "expected_output": "2", "description": "F(3)"},
            {"input": "4", "expected_output": "3", "description": "F(4)"}
        ],
        "hidden_tests": [
            {"input": "0", "expected_output": "0", "description": "F(0)"},
            {"input": "10", "expected_output": "55", "description": "F(10)"}
        ]
    },
    
    "valid_parentheses": {
        "title": "Валидные скобки",
        "description": """Дана строка s, содержащая только символы '(', ')', '{', '}', '[' и ']', определите, является ли входная строка валидной.

Входная строка валидна, если:
1. Открытые скобки должны быть закрыты теми же типами скобок.
2. Открытые скобки должны быть закрыты в правильном порядке.
3. Каждая закрывающая скобка имеет соответствующую открытую скобку того же типа.

Пример 1:
Вход: s = "()"
Выход: True

Пример 2:
Вход: s = "()[]{}"
Выход: True

Пример 3:
Вход: s = "(]"
Выход: False

Ограничения:
- 1 <= s.length <= 10^4
- s состоит только из скобок '()[]{}'

Сигнатура функции:
def isValid(s: str) -> bool:""",
        "difficulty": "easy",
        "category": "stack",
        "visible_tests": [
            {"input": "'()'", "expected_output": "True", "description": "Простые скобки"},
            {"input": "'()[]{}'", "expected_output": "True", "description": "Все типы"},
            {"input": "'(]'", "expected_output": "False", "description": "Неверная пара"}
        ],
        "hidden_tests": [
            {"input": "'([])'", "expected_output": "True", "description": "Вложенные"},
            {"input": "'([)]'", "expected_output": "False", "description": "Неправильный порядок"}
        ]
    },
    
    "contains_duplicate": {
        "title": "Содержит дубликат",
        "description": """Дан массив целых чисел nums, верните true, если какое-либо значение появляется в массиве как минимум дважды.
Верните false, если каждый элемент уникален.

Пример 1:
Вход: nums = [1,2,3,1]
Выход: True

Пример 2:
Вход: nums = [1,2,3,4]
Выход: False

Пример 3:
Вход: nums = [1,1,1,3,3,4,3,2,4,2]
Выход: True

Ограничения:
- 1 <= nums.length <= 10^5
- -10^9 <= nums[i] <= 10^9

Сигнатура функции:
def containsDuplicate(nums: List[int]) -> bool:""",
        "difficulty": "easy",
        "category": "arrays",
        "visible_tests": [
            {"input": "[1,2,3,1]", "expected_output": "True", "description": "Есть дубликат"},
            {"input": "[1,2,3,4]", "expected_output": "False", "description": "Все уникальны"},
            {"input": "[1,1,1,3,3,4,3,2,4,2]", "expected_output": "True", "description": "Много дубликатов"}
        ],
        "hidden_tests": [
            {"input": "[1]", "expected_output": "False", "description": "Один элемент"},
            {"input": "[1,1]", "expected_output": "True", "description": "Два одинаковых"}
        ]
    },
    
    "fizzbuzz": {
        "title": "FizzBuzz",
        "description": """Дано целое число n, верните массив строк answer (с индексацией от 1), где:

- answer[i] == "FizzBuzz" если i делится на 3 и на 5.
- answer[i] == "Fizz" если i делится на 3.
- answer[i] == "Buzz" если i делится на 5.
- answer[i] == i (в виде строки) в остальных случаях.

Пример 1:
Вход: n = 3
Выход: ["1","2","Fizz"]

Пример 2:
Вход: n = 5
Выход: ["1","2","Fizz","4","Buzz"]

Пример 3:
Вход: n = 15
Выход: ["1","2","Fizz","4","Buzz","Fizz","7","8","Fizz","Buzz","11","Fizz","13","14","FizzBuzz"]

Ограничения:
- 1 <= n <= 10^4

Сигнатура функции:
def fizzBuzz(n: int) -> List[str]:""",
        "difficulty": "easy",
        "category": "arrays",
        "visible_tests": [
            {"input": "3", "expected_output": "['1','2','Fizz']", "description": "До 3"},
            {"input": "5", "expected_output": "['1','2','Fizz','4','Buzz']", "description": "До 5"}
        ],
        "hidden_tests": [
            {"input": "1", "expected_output": "['1']", "description": "Минимум"},
            {"input": "15", "expected_output": "['1','2','Fizz','4','Buzz','Fizz','7','8','Fizz','Buzz','11','Fizz','13','14','FizzBuzz']", "description": "До 15"}
        ]
    }
}

def get_task_by_difficulty(difficulty: str) -> Dict[str, Any]:
    """Get a random task by difficulty level."""
    import random
    
    matching_tasks = {
        key: task for key, task in TASK_POOL.items()
        if task["difficulty"] == difficulty
    }
    
    if not matching_tasks:
        matching_tasks = TASK_POOL
    
    task_key = random.choice(list(matching_tasks.keys()))
    return matching_tasks[task_key]


def get_task_sequence(level: str, count: int = 3) -> List[Dict[str, Any]]:
    """
    Get a sequence of tasks for a given level.
    
    Args:
        level: intern, junior, middle, senior
        count: number of tasks to return
    
    Returns:
        List of tasks with appropriate difficulty
    """
    level_mapping = {
        "intern": ["easy", "easy", "easy"],
        "junior": ["easy", "easy", "medium"],
        "junior+": ["easy", "medium", "medium"],
        "middle": ["medium", "medium", "medium"],
        "middle+": ["medium", "medium", "hard"],
        "senior": ["medium", "hard", "hard"]
    }
    
    difficulties = level_mapping.get(level, ["easy", "medium", "hard"])[:count]
    
    tasks = []
    used_keys = set()
    
    for difficulty in difficulties:
        matching = {
            key: task for key, task in TASK_POOL.items()
            if task["difficulty"] == difficulty and key not in used_keys
        }
        
        if matching:
            import random
            task_key = random.choice(list(matching.keys()))
            tasks.append(matching[task_key])
            used_keys.add(task_key)
        else:
            tasks.append(get_task_by_difficulty(difficulty))
    
    return tasks
