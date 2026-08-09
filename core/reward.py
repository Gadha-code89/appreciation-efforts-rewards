"""
core/reward.py - Banked Minutes & Screen Time State Mutation Engine
"""

from datetime import datetime, timedelta
from typing import Dict, Any
from core.state import load_state, save_state
from core.logger import logger


def apply_reward(earned_minutes: int, quiz_result: Dict[str, Any], is_practice: bool = False) -> Dict[str, Any]:
    """
    Apply earned reward minutes from a quiz session to state.
    Updates banked minutes, increments session count, and logs to history.
    """
    state = load_state()

    if is_practice:
        earned_minutes = 0

    state["sessions_today"] = state.get("sessions_today", 0) + 1
    state["minutes_banked"] = state.get("minutes_banked", 0) + earned_minutes

    # Core Gamification: Initialize and award stars on passing
    state["total_stars"] = state.get("total_stars", 120)
    state["streak"] = state.get("streak", 3)
    
    stars_earned = 0
    passed = quiz_result.get("passed", False) or (quiz_result.get("score", 0) == quiz_result.get("total", 10))
    if passed:
        stars_earned = 0 if is_practice else 20
        state["total_stars"] += stars_earned

    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": quiz_result.get("level", state["current_level"]),
        "test_in_level": quiz_result.get("test_in_level", state.get("current_test_in_level", 1)),
        "correct": quiz_result.get("score", 0),
        "total": quiz_result.get("total", 10),
        "minutes_earned": earned_minutes,
        "session_number": state["sessions_today"],
        "is_practice": is_practice,
        "stars_earned": stars_earned
    }

    state.setdefault("history", []).append(history_entry)
    state["last_completed_quiz"] = quiz_result

    # Update progression state only if this is NOT a practice session
    if not is_practice:
        if quiz_result.get("level_up_occurred"):
            state["current_level"] = quiz_result.get("new_level", state["current_level"] + 1)
            state["current_test_in_level"] = 1
        else:
            state["current_test_in_level"] = quiz_result.get("new_test_in_level", state.get("current_test_in_level", 1))

    save_state(state)

    return {
        "success": True,
        "earned_minutes": earned_minutes,
        "total_minutes_banked": state["minutes_banked"],
        "current_level": state["current_level"],
        "current_test_in_level": state.get("current_test_in_level", 1),
        "session_number": state["sessions_today"],
        "stars_earned": stars_earned,
        "total_stars": state["total_stars"],
        "streak": state["streak"]
    }


# activate_screen_time function deleted (no lock/unlock parental controls)
