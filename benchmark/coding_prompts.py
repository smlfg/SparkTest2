"""
10 Standard Coding Test Prompts

These prompts test different Python coding skills:
- Basic algorithms (FizzBuzz, palindrome, etc.)
- Data structures (lists, dicts)
- String manipulation
- Recursion
- Error handling
- File I/O

WHY THESE PROMPTS?
- Representative of StackOverflow questions
- Range from easy to medium difficulty
- Suitable for 0.5B model capabilities
- Clearly testable (can check for keywords)

USAGE:
    from coding_prompts import CODING_TEST_PROMPTS

    for prompt in CODING_TEST_PROMPTS:
        print(prompt['id'], prompt['difficulty'])
"""

CODING_TEST_PROMPTS = [
    # ========================================
    # CATEGORY: Basic Algorithms
    # ========================================
    {
        "id": "fizzbuzz",
        "prompt": "Schreibe eine Python Funktion die FizzBuzz für Zahlen 1 bis 100 implementiert. Ausgabe: 'Fizz' für Vielfache von 3, 'Buzz' für Vielfache von 5, 'FizzBuzz' für Vielfache von 15.",
        "category": "algorithms",
        "difficulty": "easy",
        "expected_keywords": ["def", "fizzbuzz", "range", "print", "FizzBuzz"],
        "expected_concepts": ["loops", "conditionals", "modulo"],
    },

    {
        "id": "palindrome",
        "prompt": "Implementiere eine Python Funktion is_palindrome(s) die prüft ob ein String ein Palindrom ist. Ignoriere Leerzeichen und Groß-/Kleinschreibung.",
        "category": "strings",
        "difficulty": "easy",
        "expected_keywords": ["def", "palindrome", "return", "lower"],
        "expected_concepts": ["string manipulation", "comparison"],
    },

    {
        "id": "reverse_list",
        "prompt": "Schreibe eine Funktion reverse_list(lst) die eine Liste umdreht ohne die eingebaute reverse() Methode zu nutzen.",
        "category": "data_structures",
        "difficulty": "easy",
        "expected_keywords": ["def", "reverse", "return"],
        "expected_concepts": ["iteration", "indexing"],
    },

    # ========================================
    # CATEGORY: Recursion
    # ========================================
    {
        "id": "factorial",
        "prompt": "Implementiere die Fakultät-Funktion rekursiv. factorial(5) sollte 120 zurückgeben.",
        "category": "recursion",
        "difficulty": "medium",
        "expected_keywords": ["def", "factorial", "return", "if"],
        "expected_concepts": ["recursion", "base case"],
    },

    {
        "id": "fibonacci",
        "prompt": "Schreibe eine rekursive Fibonacci-Funktion. fibonacci(6) sollte 8 zurückgeben (Sequenz: 0,1,1,2,3,5,8).",
        "category": "recursion",
        "difficulty": "medium",
        "expected_keywords": ["def", "fibonacci", "return"],
        "expected_concepts": ["recursion", "multiple recursive calls"],
    },

    # ========================================
    # CATEGORY: Data Structures
    # ========================================
    {
        "id": "merge_dicts",
        "prompt": "Schreibe eine Funktion merge_dicts(dict1, dict2) die zwei Python Dictionaries merged. Bei Konflikten sollen Werte aus dict2 überschreiben.",
        "category": "data_structures",
        "difficulty": "easy",
        "expected_keywords": ["def", "merge", "dict", "return"],
        "expected_concepts": ["dictionary operations", "update"],
    },

    {
        "id": "count_words",
        "prompt": "Implementiere eine Funktion count_words(text) die die Häufigkeit jedes Wortes in einem String zählt und als Dictionary zurückgibt.",
        "category": "strings",
        "difficulty": "medium",
        "expected_keywords": ["def", "count", "split", "dict"],
        "expected_concepts": ["string splitting", "dictionary counting"],
    },

    # ========================================
    # CATEGORY: Pythonic Code
    # ========================================
    {
        "id": "list_comprehension",
        "prompt": "Nutze eine List Comprehension um eine Liste der Quadratzahlen von 1 bis 10 zu erstellen.",
        "category": "pythonic",
        "difficulty": "easy",
        "expected_keywords": ["[", "for", "in", "]", "**2"],
        "expected_concepts": ["list comprehension"],
    },

    # ========================================
    # CATEGORY: Error Handling
    # ========================================
    {
        "id": "safe_divide",
        "prompt": "Schreibe eine Funktion safe_divide(a, b) die zwei Zahlen dividiert und bei Division durch Null eine aussagekräftige Fehlermeldung zurückgibt (nicht wirft).",
        "category": "error_handling",
        "difficulty": "medium",
        "expected_keywords": ["def", "try", "except", "ZeroDivisionError"],
        "expected_concepts": ["exception handling", "defensive programming"],
    },

    # ========================================
    # CATEGORY: File I/O
    # ========================================
    {
        "id": "read_file",
        "prompt": "Schreibe eine Funktion read_lines(filename) die eine Textdatei liest und eine Liste der Zeilen zurückgibt. Nutze 'with' für sicheres File-Handling.",
        "category": "io",
        "difficulty": "medium",
        "expected_keywords": ["def", "open", "with", "readlines", "return"],
        "expected_concepts": ["context manager", "file operations"],
    },
]

# TEACHING: Why use a list of dicts?
# - Easy to iterate: for prompt in CODING_TEST_PROMPTS
# - Easy to filter: [p for p in CODING_TEST_PROMPTS if p["difficulty"] == "easy"]
# - Easy to extend: Just add more dicts
# - Can be passed to async functions

# Validation check (run at import time)
def _validate_prompts():
    """
    TEACHING: Defensive programming

    Check that prompts are well-formed before using them.
    Better to fail at import time than during testing!
    """
    ids_seen = set()

    for i, prompt in enumerate(CODING_TEST_PROMPTS):
        # Check required fields
        required = ["id", "prompt", "category", "difficulty"]
        for field in required:
            assert field in prompt, f"Prompt {i} missing '{field}'"

        # Check unique IDs
        assert prompt["id"] not in ids_seen, f"Duplicate ID: {prompt['id']}"
        ids_seen.add(prompt["id"])

        # Check expected_keywords exists (for validation)
        assert "expected_keywords" in prompt, f"Prompt {prompt['id']} missing 'expected_keywords'"

# Run validation when module is imported
_validate_prompts()

# TEACHING: This print happens when you do: from coding_prompts import CODING_TEST_PROMPTS
# It confirms the module loaded successfully
print(f"✅ Loaded {len(CODING_TEST_PROMPTS)} coding test prompts")
