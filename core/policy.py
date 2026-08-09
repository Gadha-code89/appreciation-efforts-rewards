"""
core/policy.py - Policy Rules (Morning Battery Bonus & Gating)
"""

from typing import Dict, Any

MORNING_BATTERY_THRESHOLD = 50  # Must be strictly > 50% charge before 9 AM
MORNING_BONUS_MINUTES = 5       # One-time bonus minutes awarded in the morning


def evaluate_morning_battery_bonus(charge_percent: int) -> Dict[str, Any]:
    """
    Evaluate morning battery bonus.
    If charge is strictly > 50%, awards +5 bonus minutes once for starting the day charged.
    """
    if charge_percent > MORNING_BATTERY_THRESHOLD:
        return {
            "eligible": True,
            "bonus_minutes": MORNING_BONUS_MINUTES,
            "charge_percent": charge_percent,
            "message": f"Battery is {charge_percent}% (> 50%). Morning bonus of +{MORNING_BONUS_MINUTES} minutes awarded!"
        }
    
    return {
        "eligible": False,
        "bonus_minutes": 0,
        "charge_percent": charge_percent,
        "message": f"Battery is {charge_percent}% (needs to be > 50% for morning bonus)."
    }
