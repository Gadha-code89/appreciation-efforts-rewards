"""
agents_app/controller_agent.py - Policy Enforcement, Scoring, and Level Decision Agent
"""

from typing import Dict, Any
from core.levels import evaluate_level_up, get_level_info
from core.scoring import compute_minutes
from core.reward import apply_reward
from core.state import load_state


def process_quiz_submission(score: int, total: int, current_level: int, is_practice: bool = False) -> Dict[str, Any]:
    """
    Process quiz result through deterministic Controller decision logic.
    
    1. Evaluates 4-tests level-up criteria (if not practice).
    2. Computes earned minutes using flat 5/15 scoring rules.
    3. Updates banked minutes and state.
    
    Returns structured result dict.
    """
    state = load_state()
    session_num = state.get("sessions_today", 0) + 1
    current_test = state.get("current_test_in_level", 1)

    # 1. Evaluate level progression / test progression
    if is_practice:
        level_up_occurred = False
        new_level = current_level
        new_test_in_level = current_test
    else:
        level_up_occurred, new_level, new_test_in_level = evaluate_level_up(
            score, total, current_level, current_test
        )

    scoring_result = compute_minutes(
        num_correct=score,
        num_questions=total,
        session_number=session_num,
        is_practice=is_practice,
        level=current_level
    )
    earned_minutes = scoring_result["minutes"]

    # 3. Construct session summary
    quiz_summary = {
        "level": current_level,
        "test_in_level": current_test,
        "score": score,
        "total": total,
        "passed": score == total,  # 100% strict accuracy
        "level_up_occurred": level_up_occurred,
        "new_level": new_level,
        "new_test_in_level": new_test_in_level,
        "minutes_earned": earned_minutes,
        "rate": scoring_result["rate"],
        "reason": scoring_result["reason"],
        "is_practice": is_practice
    }

    # 4. Mutate state via reward engine
    reward_result = apply_reward(earned_minutes, quiz_summary, is_practice=is_practice)

    level_info = get_level_info(new_level if level_up_occurred else current_level)

    return {
        "score": score,
        "total": total,
        "earned_minutes": earned_minutes,
        "total_minutes_banked": reward_result["total_minutes_banked"],
        "previous_level": current_level,
        "current_level": reward_result["current_level"],
        "current_test_in_level": reward_result["current_test_in_level"],
        "level_up_occurred": level_up_occurred,
        "new_level_info": level_info,
        "scoring_reason": scoring_result["reason"],
        "session_number": session_num,
        "is_practice": is_practice,
        "stars_earned": reward_result.get("stars_earned", 0),
        "total_stars": reward_result.get("total_stars", 120),
        "streak": reward_result.get("streak", 3)
    }
