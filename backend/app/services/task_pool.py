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
    },
    
    # HARD TASKS
    "longest_substring": {
        "title": "Longest Substring Without Repeating",
        "description": """Найдите длину самой длинной подстроки без повторяющихся символов.

Пример 1:
Вход: s = "abcabcbb"
Выход: 3
Объяснение: Ответ - "abc", длина 3.

Пример 2:
Вход: s = "bbbbb"
Выход: 1
Объяснение: Ответ - "b", длина 1.

Пример 3:
Вход: s = "pwwkew"
Выход: 3
Объяснение: Ответ - "wke", длина 3.

Ограничения:
- 0 <= s.length <= 5 * 10^4
- s состоит из английских букв, цифр, символов и пробелов

Сигнатура функции:
def lengthOfLongestSubstring(s: str) -> int:""",
        "difficulty": "hard",
        "category": "sliding_window",
        "visible_tests": [
            {"input": "'abcabcbb'", "expected_output": "3", "description": "Базовый случай"},
            {"input": "'bbbbb'", "expected_output": "1", "description": "Все одинаковые"},
            {"input": "'pwwkew'", "expected_output": "3", "description": "Повтор в середине"}
        ],
        "hidden_tests": [
            {"input": "''", "expected_output": "0", "description": "Пустая строка"},
            {"input": "' '", "expected_output": "1", "description": "Пробел"},
            {"input": "'dvdf'", "expected_output": "3", "description": "Сложный случай"}
        ]
    },
    "merge_intervals": {
        "title": "Merge Intervals",
        "description": """Дан массив интервалов, объедините все пересекающиеся интервалы и верните массив непересекающихся интервалов.

Пример 1:
Вход: intervals = [[1,3],[2,6],[8,10],[15,18]]
Выход: [[1,6],[8,10],[15,18]]
Объяснение: Интервалы [1,3] и [2,6] пересекаются, объединяем в [1,6].

Пример 2:
Вход: intervals = [[1,4],[4,5]]
Выход: [[1,5]]
Объяснение: Интервалы [1,4] и [4,5] касаются, объединяем.

Ограничения:
- 1 <= intervals.length <= 10^4
- intervals[i].length == 2
- 0 <= start <= end <= 10^4

Сигнатура функции:
def merge(intervals: List[List[int]]) -> List[List[int]]:""",
        "difficulty": "hard",
        "category": "arrays",
        "visible_tests": [
            {"input": "[[1,3],[2,6],[8,10],[15,18]]", "expected_output": "[[1,6],[8,10],[15,18]]", "description": "Базовый случай"},
            {"input": "[[1,4],[4,5]]", "expected_output": "[[1,5]]", "description": "Касающиеся интервалы"}
        ],
        "hidden_tests": [
            {"input": "[[1,4],[0,4]]", "expected_output": "[[0,4]]", "description": "Полное перекрытие"},
            {"input": "[[1,4],[2,3]]", "expected_output": "[[1,4]]", "description": "Вложенный интервал"}
        ]
    },
    "lru_cache": {
        "title": "LRU Cache Design",
        "description": """Реализуйте структуру данных LRU (Least Recently Used) Cache с операциями get и put.

get(key) - получить значение ключа или -1 если не найден.
put(key, value) - добавить или обновить значение. Если кэш переполнен, удалить наименее используемый элемент.

Все операции должны выполняться за O(1).

Пример:
cache = LRUCache(2)
cache.put(1, 1)
cache.put(2, 2)
cache.get(1)      # вернёт 1
cache.put(3, 3)   # вытеснит ключ 2
cache.get(2)      # вернёт -1 (не найден)
cache.put(4, 4)   # вытеснит ключ 1
cache.get(1)      # вернёт -1
cache.get(3)      # вернёт 3
cache.get(4)      # вернёт 4

Сигнатура функции:
def lruCacheOps(capacity: int, operations: List[List]) -> List[int]:

operations - список операций: ["get", key] или ["put", key, value]
Вернуть список результатов get операций.""",
        "difficulty": "hard",
        "category": "design",
        "visible_tests": [
            {"input": "2, [['put',1,1],['put',2,2],['get',1],['put',3,3],['get',2]]", "expected_output": "[1,-1]", "description": "Базовый LRU"}
        ],
        "hidden_tests": [
            {"input": "1, [['put',1,1],['put',2,2],['get',1],['get',2]]", "expected_output": "[-1,2]", "description": "Вместимость 1"},
            {"input": "2, [['get',1],['put',1,1],['get',1]]", "expected_output": "[-1,1]", "description": "Get пустого"}
        ]
    },
    
    # ========== ML / DATA SCIENCE TASKS ==========
    
    "normalize_data": {
        "title": "Нормализация данных",
        "description": """Реализуйте функцию нормализации данных (Min-Max Scaling).

Формула: x_norm = (x - min) / (max - min)

Функция должна принять список чисел и вернуть нормализованный список, где все значения будут в диапазоне [0, 1].

Пример 1:
Вход: data = [1, 2, 3, 4, 5]
Выход: [0.0, 0.25, 0.5, 0.75, 1.0]

Пример 2:
Вход: data = [10, 20, 30]
Выход: [0.0, 0.5, 1.0]

Пример 3:
Вход: data = [5, 5, 5]
Выход: [0.0, 0.0, 0.0]  # Все одинаковые - возвращаем нули

Ограничения:
- 1 <= len(data) <= 10^4
- -10^6 <= data[i] <= 10^6

Сигнатура функции:
def normalize(data: List[float]) -> List[float]:""",
        "difficulty": "easy",
        "category": "ml",
        "visible_tests": [
            {"input": "[1, 2, 3, 4, 5]", "expected_output": "[0.0, 0.25, 0.5, 0.75, 1.0]", "description": "Базовый случай"},
            {"input": "[10, 20, 30]", "expected_output": "[0.0, 0.5, 1.0]", "description": "Три числа"},
            {"input": "[5, 5, 5]", "expected_output": "[0.0, 0.0, 0.0]", "description": "Все одинаковые"}
        ],
        "hidden_tests": [
            {"input": "[0, 100]", "expected_output": "[0.0, 1.0]", "description": "Два числа"},
            {"input": "[-10, 0, 10]", "expected_output": "[0.0, 0.5, 1.0]", "description": "Отрицательные"}
        ]
    },
    
    "calculate_accuracy": {
        "title": "Метрика Accuracy",
        "description": """Реализуйте функцию расчёта метрики Accuracy для задачи классификации.

Accuracy = (количество правильных предсказаний) / (общее количество предсказаний)

Функция принимает два списка одинаковой длины:
- y_true: истинные метки классов
- y_pred: предсказанные метки классов

Пример 1:
Вход: y_true = [1, 0, 1, 1, 0], y_pred = [1, 0, 0, 1, 0]
Выход: 0.8
Объяснение: 4 из 5 предсказаний верны

Пример 2:
Вход: y_true = [1, 1, 1], y_pred = [0, 0, 0]
Выход: 0.0

Ограничения:
- 1 <= len(y_true) == len(y_pred) <= 10^4
- Метки - целые числа

Сигнатура функции:
def accuracy(y_true: List[int], y_pred: List[int]) -> float:""",
        "difficulty": "easy",
        "category": "ml",
        "visible_tests": [
            {"input": "[1, 0, 1, 1, 0], [1, 0, 0, 1, 0]", "expected_output": "0.8", "description": "80% accuracy"},
            {"input": "[1, 1, 1], [0, 0, 0]", "expected_output": "0.0", "description": "Все неверно"},
            {"input": "[0, 1, 0, 1], [0, 1, 0, 1]", "expected_output": "1.0", "description": "Все верно"}
        ],
        "hidden_tests": [
            {"input": "[1], [1]", "expected_output": "1.0", "description": "Один элемент"},
            {"input": "[0, 0, 1, 1], [1, 0, 1, 0]", "expected_output": "0.5", "description": "50%"}
        ]
    },
    
    "confusion_matrix": {
        "title": "Confusion Matrix",
        "description": """Реализуйте функцию построения матрицы ошибок (Confusion Matrix) для бинарной классификации.

Матрица ошибок 2x2:
[[TN, FP],
 [FN, TP]]

Где:
- TN (True Negative): предсказано 0, истина 0
- FP (False Positive): предсказано 1, истина 0
- FN (False Negative): предсказано 0, истина 1
- TP (True Positive): предсказано 1, истина 1

Пример:
Вход: y_true = [0, 0, 1, 1], y_pred = [0, 1, 0, 1]
Выход: [[1, 1], [1, 1]]
Объяснение: TN=1, FP=1, FN=1, TP=1

Сигнатура функции:
def confusion_matrix(y_true: List[int], y_pred: List[int]) -> List[List[int]]:""",
        "difficulty": "medium",
        "category": "ml",
        "visible_tests": [
            {"input": "[0, 0, 1, 1], [0, 1, 0, 1]", "expected_output": "[[1, 1], [1, 1]]", "description": "Базовый случай"},
            {"input": "[0, 0, 0], [0, 0, 0]", "expected_output": "[[3, 0], [0, 0]]", "description": "Все TN"},
            {"input": "[1, 1, 1], [1, 1, 1]", "expected_output": "[[0, 0], [0, 3]]", "description": "Все TP"}
        ],
        "hidden_tests": [
            {"input": "[0, 1], [1, 0]", "expected_output": "[[0, 1], [1, 0]]", "description": "Все ошибки"},
            {"input": "[0, 0, 1, 1, 0, 1], [0, 0, 1, 1, 1, 0]", "expected_output": "[[2, 1], [1, 2]]", "description": "Смешанный"}
        ]
    },
    
    "softmax": {
        "title": "Softmax функция",
        "description": """Реализуйте функцию Softmax - преобразование вектора в вероятностное распределение.

Формула: softmax(x_i) = exp(x_i) / sum(exp(x_j) for all j)

Результат - вектор той же длины, где сумма всех элементов равна 1.

Для численной стабильности вычтите максимум из всех элементов перед экспонентой:
x_stable = x - max(x)
softmax(x_i) = exp(x_stable_i) / sum(exp(x_stable_j))

Пример 1:
Вход: x = [1.0, 2.0, 3.0]
Выход: [0.09, 0.24, 0.67] (примерно)

Пример 2:
Вход: x = [0.0, 0.0]
Выход: [0.5, 0.5]

Округлите результат до 2 знаков после запятой.

Сигнатура функции:
def softmax(x: List[float]) -> List[float]:""",
        "difficulty": "medium",
        "category": "ml",
        "visible_tests": [
            {"input": "[0.0, 0.0]", "expected_output": "[0.5, 0.5]", "description": "Равные значения"},
            {"input": "[1.0, 0.0]", "expected_output": "[0.73, 0.27]", "description": "Разные значения"},
            {"input": "[1.0, 2.0, 3.0]", "expected_output": "[0.09, 0.24, 0.67]", "description": "Три значения"}
        ],
        "hidden_tests": [
            {"input": "[100.0, 100.0]", "expected_output": "[0.5, 0.5]", "description": "Большие числа"},
            {"input": "[-1.0, 0.0, 1.0]", "expected_output": "[0.09, 0.24, 0.67]", "description": "Отрицательные"}
        ]
    },
    
    "knn_predict": {
        "title": "K-Nearest Neighbors",
        "description": """Реализуйте простой алгоритм K-ближайших соседей (KNN) для классификации.

Дано:
- X_train: список точек обучающей выборки [[x1, y1], [x2, y2], ...]
- y_train: метки классов для обучающей выборки
- point: точка для классификации [x, y]
- k: количество соседей

Алгоритм:
1. Вычислить евклидово расстояние от point до каждой точки в X_train
2. Найти k ближайших соседей
3. Вернуть наиболее частую метку среди k соседей

Пример:
X_train = [[0, 0], [1, 1], [2, 2], [10, 10]]
y_train = [0, 0, 0, 1]
point = [1, 0]
k = 3
Выход: 0 (3 ближайших соседа имеют метку 0)

Сигнатура функции:
def knn_predict(X_train: List[List[float]], y_train: List[int], point: List[float], k: int) -> int:""",
        "difficulty": "medium",
        "category": "ml",
        "visible_tests": [
            {"input": "[[0, 0], [1, 1], [2, 2], [10, 10]], [0, 0, 0, 1], [1, 0], 3", "expected_output": "0", "description": "Базовый KNN"},
            {"input": "[[0, 0], [10, 10]], [0, 1], [9, 9], 1", "expected_output": "1", "description": "k=1"},
            {"input": "[[0, 0], [0, 1], [1, 0], [1, 1]], [0, 0, 1, 1], [0.5, 0.5], 4", "expected_output": "0", "description": "Центр"}
        ],
        "hidden_tests": [
            {"input": "[[0, 0], [1, 1]], [0, 1], [0.4, 0.4], 1", "expected_output": "0", "description": "Ближе к 0"},
            {"input": "[[0, 0], [1, 1], [2, 2]], [0, 1, 0], [1.1, 1.1], 2", "expected_output": "0", "description": "Tie-break"}
        ]
    },
    
    "gradient_descent_step": {
        "title": "Шаг градиентного спуска",
        "description": """Реализуйте один шаг градиентного спуска для линейной регрессии.

Дано:
- X: матрица признаков (список списков)
- y: вектор целевых значений
- weights: текущие веса модели
- learning_rate: скорость обучения

Формулы:
- Предсказание: y_pred = X @ weights
- Градиент: gradient = (2/n) * X.T @ (y_pred - y)
- Обновление: weights_new = weights - learning_rate * gradient

Верните обновлённые веса, округлённые до 4 знаков.

Пример:
X = [[1, 1], [1, 2], [1, 3]]
y = [1, 2, 3]
weights = [0, 0]
learning_rate = 0.1
Выход: [0.4, 0.9333] (примерно)

Сигнатура функции:
def gradient_step(X: List[List[float]], y: List[float], weights: List[float], lr: float) -> List[float]:""",
        "difficulty": "hard",
        "category": "ml",
        "visible_tests": [
            {"input": "[[1, 1], [1, 2], [1, 3]], [1, 2, 3], [0, 0], 0.1", "expected_output": "[0.4, 0.9333]", "description": "Базовый шаг"},
            {"input": "[[1, 0], [1, 1]], [0, 1], [0, 0], 0.5", "expected_output": "[0.25, 0.5]", "description": "Простой случай"}
        ],
        "hidden_tests": [
            {"input": "[[1, 1]], [2], [0, 0], 1.0", "expected_output": "[2.0, 2.0]", "description": "Один пример"},
            {"input": "[[1, 2], [1, 4]], [3, 5], [1, 1], 0.1", "expected_output": "[1.0, 1.0]", "description": "Уже оптимум"}
        ]
    },
    
    # ========== PANDAS / DATA TASKS ==========
    
    "filter_outliers": {
        "title": "Фильтрация выбросов",
        "description": """Реализуйте функцию фильтрации выбросов методом IQR (Interquartile Range).

Алгоритм:
1. Вычислить Q1 (25-й перцентиль) и Q3 (75-й перцентиль)
2. IQR = Q3 - Q1
3. Нижняя граница = Q1 - 1.5 * IQR
4. Верхняя граница = Q3 + 1.5 * IQR
5. Вернуть только значения в пределах границ

Пример:
Вход: data = [1, 2, 3, 4, 5, 100]
Выход: [1, 2, 3, 4, 5]  # 100 - выброс

Для расчёта перцентилей используйте линейную интерполяцию.

Сигнатура функции:
def filter_outliers(data: List[float]) -> List[float]:""",
        "difficulty": "medium",
        "category": "data_science",
        "visible_tests": [
            {"input": "[1, 2, 3, 4, 5, 100]", "expected_output": "[1, 2, 3, 4, 5]", "description": "Один выброс"},
            {"input": "[1, 2, 3, 4, 5]", "expected_output": "[1, 2, 3, 4, 5]", "description": "Без выбросов"},
            {"input": "[-100, 1, 2, 3, 4, 5]", "expected_output": "[1, 2, 3, 4, 5]", "description": "Отрицательный выброс"}
        ],
        "hidden_tests": [
            {"input": "[1, 1, 1, 1, 1]", "expected_output": "[1, 1, 1, 1, 1]", "description": "Все одинаковые"},
            {"input": "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 50]", "expected_output": "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]", "description": "Длинный список"}
        ]
    },
    
    "moving_average": {
        "title": "Скользящее среднее",
        "description": """Реализуйте функцию расчёта скользящего среднего (Moving Average).

Для каждой позиции i вычислите среднее window_size элементов, заканчивающихся на i.
Для первых (window_size - 1) элементов используйте доступные данные.

Пример:
Вход: data = [1, 2, 3, 4, 5], window_size = 3
Выход: [1.0, 1.5, 2.0, 3.0, 4.0]

Объяснение:
- i=0: avg([1]) = 1.0
- i=1: avg([1, 2]) = 1.5
- i=2: avg([1, 2, 3]) = 2.0
- i=3: avg([2, 3, 4]) = 3.0
- i=4: avg([3, 4, 5]) = 4.0

Округлите до 2 знаков после запятой.

Сигнатура функции:
def moving_average(data: List[float], window_size: int) -> List[float]:""",
        "difficulty": "easy",
        "category": "data_science",
        "visible_tests": [
            {"input": "[1, 2, 3, 4, 5], 3", "expected_output": "[1.0, 1.5, 2.0, 3.0, 4.0]", "description": "Базовый случай"},
            {"input": "[10, 20, 30], 2", "expected_output": "[10.0, 15.0, 25.0]", "description": "Окно 2"},
            {"input": "[1, 1, 1, 1], 4", "expected_output": "[1.0, 1.0, 1.0, 1.0]", "description": "Все одинаковые"}
        ],
        "hidden_tests": [
            {"input": "[5], 3", "expected_output": "[5.0]", "description": "Один элемент"},
            {"input": "[1, 2, 3, 4, 5, 6], 1", "expected_output": "[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]", "description": "Окно 1"}
        ]
    }
}

def get_task_by_difficulty(difficulty: str, task_order: int = 1) -> Dict[str, Any]:
    """
    Get a task by difficulty level.
    Uses task_order to get different tasks for sequential requests.
    """
    actual_difficulty = difficulty
    
    matching_tasks = [
        task for key, task in TASK_POOL.items()
        if task["difficulty"] == actual_difficulty
    ]
    
    if not matching_tasks:
        matching_tasks = list(TASK_POOL.values())
    
    # Use task_order to pick different tasks
    idx = (task_order - 1) % len(matching_tasks)
    return matching_tasks[idx]


def get_task_sequence(level: str, count: int = 3, direction: str = "backend") -> List[Dict[str, Any]]:
    """
    Get a sequence of tasks for a given level and direction.
    
    Structure:
    - Task 1: Algorithm (easy/medium based on level)
    - Task 2: Algorithm (medium/hard based on level)  
    - Task 3: Specialization task (ML/Data/Frontend based on direction)
    
    Args:
        level: intern, junior, middle, senior
        count: number of tasks to return
        direction: ml, data-science, backend, frontend, etc.
    
    Returns:
        List of tasks with appropriate difficulty
    """
    import random
    
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
    
    # First 2 tasks: algorithms
    for i, difficulty in enumerate(difficulties[:2]):
        matching = {
            key: task for key, task in TASK_POOL.items()
            if task["difficulty"] == difficulty 
            and key not in used_keys
            and task.get("category") not in ["ml", "data_science", "pandas"]  # Exclude specialization
        }
        
        if matching:
            task_key = random.choice(list(matching.keys()))
            tasks.append(matching[task_key])
            used_keys.add(task_key)
        else:
            tasks.append(get_task_by_difficulty(difficulty))
    
    # Task 3: Specialization based on direction
    if count >= 3:
        spec_difficulty = difficulties[2] if len(difficulties) > 2 else "medium"
        spec_task = get_specialization_task(direction, spec_difficulty, used_keys)
        if spec_task:
            tasks.append(spec_task)
        else:
            # Fallback to regular algorithm task
            matching = {
                key: task for key, task in TASK_POOL.items()
                if task["difficulty"] == spec_difficulty and key not in used_keys
            }
            if matching:
                task_key = random.choice(list(matching.keys()))
                tasks.append(matching[task_key])
            else:
                tasks.append(get_task_by_difficulty(spec_difficulty))
    
    return tasks


def get_specialization_task(direction: str, difficulty: str, used_keys: set) -> Dict[str, Any]:
    """
    Get a specialization task based on direction.
    """
    import random
    
    # Map directions to categories
    direction_categories = {
        "ml": ["ml", "data_science", "pandas"],
        "data-science": ["ml", "data_science", "pandas"],
        "data": ["data_science", "pandas", "sql"],
        "backend": ["design", "algorithms"],
        "frontend": ["frontend", "algorithms"],
        "devops": ["design", "algorithms"],
    }
    
    categories = direction_categories.get(direction, ["algorithms"])
    
    # Find matching tasks
    matching = {
        key: task for key, task in TASK_POOL.items()
        if task.get("category") in categories
        and key not in used_keys
        and task["difficulty"] == difficulty
    }
    
    # If no exact match, try any difficulty
    if not matching:
        matching = {
            key: task for key, task in TASK_POOL.items()
            if task.get("category") in categories
            and key not in used_keys
        }
    
    if matching:
        task_key = random.choice(list(matching.keys()))
        return matching[task_key]
    
    return None
