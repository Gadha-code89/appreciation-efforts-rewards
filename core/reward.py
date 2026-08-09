"""
core/reward.py - Reward and Confirmation Logic for daily growth missions
"""

from typing import Dict, Any
from core.badges import evaluate_badges


def complete_mission(mission_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mark a mission as "Pending Confirmation" by the parent.
    """
    for m in state.get("daily_missions", []):
        if m["id"] == mission_id:
            m["status"] = "Pending Confirmation"
            break
    return state


def confirm_mission(mission_id: str, praise_message: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Confirm a mission (Parent action).
    Changes status to "Completed", sets praise message, and awards 1 star.
    """
    for m in state.get("daily_missions", []):
        if m["id"] == mission_id:
            if m["status"] != "Completed":
                m["status"] = "Completed"
                m["praise"] = praise_message.strip() if praise_message else "Excellent effort! ❤️"
                state["total_stars"] = state.get("total_stars", 0) + 1
                state = evaluate_badges(state)
            break
    return state
