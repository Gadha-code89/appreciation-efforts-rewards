"""
core/scoring.py - Diminishing-Returns Scoring Formula
"""

from typing import Dict, Any

BASE_RATE_PER_CORRECT = 3.0   # Minutes per correct answer on 1st session of the day
SESSION_DECAY = 0.6           # Decay multiplier per subsequent session
FLOOR_RATE_PER_CORRECT = 0.5  # Minimum rate per correct answer
ACCURACY_THRESHOLD = 0.60     # Must achieve >= 60% accuracy (e.g. 6/10) to earn minutes


def compute_minutes(num_correct: int, num_questions: int, session_number: int, is_practice: bool = False, level: int = 1) -> Dict[str, Any]:
    """
    Compute earned minutes for a completed quiz session.
    Requires strict 10/10 (100%) to earn minutes.
    
    :param num_correct: Number of correct answers (e.g., 10)
    :param num_questions: Total questions in quiz (e.g., 10)
    :param session_number: 1-indexed session count for today
    :param is_practice: Whether this is a practice session
    :param level: The level of the quiz (Level 1 gives 2 mins, Level 2 gives 4, Level 3 gives 8, etc.)
    :return: dict with earned minutes, session number, accuracy, and applied rate
    """
    if num_questions <= 0:
        return {"minutes": 0, "session_number": session_number, "accuracy": 0.0, "rate": 0.0}

    accuracy = num_correct / num_questions
    perfect = (num_correct == num_questions)

    # Below 100% -> 0 minutes
    if not perfect:
        return {
            "minutes": 0,
            "session_number": session_number,
            "accuracy": round(accuracy, 2),
            "rate": 0.0,
            "reason": f"Scored {num_correct}/{num_questions}. A strict 10/10 (100%) is required to earn minutes."
        }

    # Perfect score! Linear reward: 5 * level minutes
    minutes = 5 * level
    rate = minutes / num_questions

    return {
        "minutes": minutes,
        "session_number": session_number,
        "accuracy": 1.0,
        "rate": round(rate, 2),
        "reason": f"Perfect score ({num_correct}/{num_questions})! Earned {minutes} minutes."
    }
