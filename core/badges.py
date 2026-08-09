"""
core/badges.py - Badge definitions and evaluation logic
"""

from typing import Dict, Any

BADGE_CATALOG = {
    "first_step": {
        "id": "first_step",
        "name": "🌱 First Step",
        "desc": "Completed your first mission."
    },
    "on_fire": {
        "id": "on_fire",
        "name": "🔥 On Fire",
        "desc": "Achieved a 3-day streak!"
    },
    "never_give_up": {
        "id": "never_give_up",
        "name": "💪 Never Give Up",
        "desc": "Completed a math quiz after initially answering incorrectly."
    },
    "brain_builder": {
        "id": "brain_builder",
        "name": "🧠 Brain Builder",
        "desc": "Completed 10 learning missions."
    },
    "helpful_hero": {
        "id": "helpful_hero",
        "name": "❤️ Helpful Hero",
        "desc": "Completed 10 helpful missions."
    },
    "growing_star": {
        "id": "growing_star",
        "name": "🌟 Growing Star",
        "desc": "Earned 50 total stars!"
    }
}


def evaluate_badges(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scan state history and stats to unlock any new badges.
    """
    unlocked_badge_ids = set(state.setdefault("badges", []))
    new_unlocks = []

    # 1. First Step: at least one journey entry
    journey = state.get("journey", [])
    if len(journey) >= 1 and "first_step" not in unlocked_badge_ids:
        new_unlocks.append("first_step")

    # 2. On Fire: 3-day streak or higher
    streak = state.get("streak", 0)
    if streak >= 3 and "on_fire" not in unlocked_badge_ids:
        new_unlocks.append("on_fire")

    # 3. Never Give Up: check if they have retried a math mission
    if state.get("never_give_up_triggered", False) and "never_give_up" not in unlocked_badge_ids:
        new_unlocks.append("never_give_up")

    # Count learning and helpful missions completed from journey
    total_learning = 0
    total_helpful = 0
    
    # We can also count today's completed missions
    all_completed_titles = []
    for entry in journey:
        all_completed_titles.extend(entry.get("completed_missions", []))
    
    # Add today's completed missions
    for m in state.get("daily_missions", []):
        if m.get("status") == "Completed":
            all_completed_titles.append(m.get("title", ""))

    for title in all_completed_titles:
        # Check categories based on emoji or keywords
        if any(keyword in title for keyword in ["Read", "Homework", "Math", "📚", "✏️", "🗺️"]):
            total_learning += 1
        if any(keyword in title for keyword in ["Tidy", "Room", "Help", "🧹", "❤️"]):
            total_helpful += 1

    # 4. Brain Builder: 10 learning missions
    if total_learning >= 10 and "brain_builder" not in unlocked_badge_ids:
        new_unlocks.append("brain_builder")

    # 5. Helpful Hero: 10 helpful missions
    if total_helpful >= 10 and "helpful_hero" not in unlocked_badge_ids:
        new_unlocks.append("helpful_hero")

    # 6. Growing Star: 50 total stars
    total_stars = state.get("total_stars", 0)
    if total_stars >= 50 and "growing_star" not in unlocked_badge_ids:
        new_unlocks.append("growing_star")

    # Save to state
    for b_id in new_unlocks:
        state["badges"].append(b_id)
        # Store newly unlocked badge ID in session state for show overlay
        state.setdefault("newly_unlocked_badges_session", []).append(b_id)

    return state
