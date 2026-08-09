"""
core/levels.py - Modularized Difficulty Levels & Progression Engine
"""

from typing import Dict, Any, Tuple

# Level registry mapping level numbers to grade focus, description, and problem parameters
LEVEL_CATALOG: Dict[int, Dict[str, Any]] = {
    1: {
        "level": 1,
        "name": "Level 1: Basic Addition & Subtraction (Grade 3)",
        "grade_focus": "Grade 3",
        "description": "Addition and subtraction of numbers up to 50 (no carrying or borrowing).",
        "topics": ["addition", "subtraction"],
        "max_number": 50,
    },
    2: {
        "level": 2,
        "name": "Level 2: Carrying & Borrowing (Grade 3)",
        "grade_focus": "Grade 3",
        "description": "Addition and subtraction of numbers up to 100 with carrying and borrowing.",
        "topics": ["addition_carrying", "subtraction_borrowing"],
        "max_number": 100,
    },
    3: {
        "level": 3,
        "name": "Level 3: Multiplication Tables 1–12 (Grade 4)",
        "grade_focus": "Grade 4",
        "description": "Multiplication tables from 1x1 up to 12x12.",
        "topics": ["multiplication"],
        "max_number": 12,
    },
    4: {
        "level": 4,
        "name": "Level 4: Division & Mixed Operations (Grade 4–5)",
        "grade_focus": "Grade 4-5",
        "description": "Whole-number division with exact quotients, plus mixed addition/multiplication.",
        "topics": ["division", "mixed_arithmetic"],
        "max_number": 100,
    },
    5: {
        "level": 5,
        "name": "Level 5: Multi-Step & Advanced Arithmetic (Grade 5)",
        "grade_focus": "Grade 5",
        "description": "Multi-step arithmetic operations and mental math logic.",
        "topics": ["multi_step"],
        "max_number": 200,
    },
}


def get_level_info(level: int) -> Dict[str, Any]:
    """
    Retrieve level details from catalog. If level exceeds max defined level,
    returns Level 5 configuration scaled up.
    """
    if level in LEVEL_CATALOG:
        return LEVEL_CATALOG[level]
    
    # Cap / scale for higher levels beyond 5
    return {
        "level": level,
        "name": f"Level {level}: Master Challenge (Grade 5+)",
        "grade_focus": "Grade 5+",
        "description": "Advanced multi-step arithmetic challenge.",
        "topics": ["multi_step", "mixed_arithmetic"],
        "max_number": 100 * level,
    }


def evaluate_level_up(score: int, total: int, current_level: int, current_test: int) -> Tuple[bool, int, int]:
    """
    Evaluate level and sub-test progression.
    Rules:
    - Must score 10/10 (score == total) to pass a test.
    - Passing test index 4 advances the level and resets the test index to 1.
    - Passing test index 1, 2, or 3 increments the test index and stays on current level.
    - Less than 10/10 keeps both level and test index unchanged.
    
    Returns: (level_up_occurred: bool, new_level: int, new_test: int)
    """
    if total > 0 and score == total:
        if current_test >= 4:
            return True, current_level + 1, 1
        else:
            return False, current_level, current_test + 1
    return False, current_level, current_test
