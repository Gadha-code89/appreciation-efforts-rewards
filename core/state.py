"""
core/state.py - Shared Device State Manager with 9:00 AM Local Time Rollover & Atomic Persistence
"""

import json
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

from core.policy import evaluate_morning_battery_bonus
from core.telemetry import get_mock_battery_telemetry
from core.logger import logger

STATE_FILE = Path(__file__).parent / "device_state.json"
TEMP_STATE_FILE = Path(__file__).parent / ".device_state.json.tmp"
_state_lock = threading.RLock()


def compute_effective_operating_date(now: datetime = None) -> str:
    """
    Compute effective operating date based on 9:00 AM to 9:00 AM local time cycle.
    Times before 9:00 AM count as part of previous calendar day's operating cycle.
    """
    if now is None:
        now = datetime.now()
    
    effective_time = now - timedelta(hours=9)
    return effective_time.date().isoformat()


def get_default_state(effective_date: str = None) -> Dict[str, Any]:
    """
    Generate default fresh device state.
    """
    if effective_date is None:
        effective_date = compute_effective_operating_date()

    return {
        "effective_date": effective_date,
        "operating_day_start": f"{effective_date}T09:00:00",
        "current_level": 1,
        "current_test_in_level": 1,
        "sessions_today": 0,
        "minutes_banked": 0,
        "unlocked_until": None,
        "morning_battery_bonus_claimed": False,
        "last_battery_check": None,
        "last_completed_quiz": None,
        "history": [],
        "api_status": {
            "openai_api_configured": bool(os.getenv("OPENAI_API_KEY")),
            "resend_api_configured": bool(os.getenv("RESEND_API_KEY"))
        }
    }


def save_state(state: Dict[str, Any]) -> None:
    """
    Atomically write state dict to device_state.json using a temp file + replace.
    """
    with _state_lock:
        state["api_status"] = {
            "openai_api_configured": bool(os.getenv("OPENAI_API_KEY")),
            "resend_api_configured": bool(os.getenv("RESEND_API_KEY"))
        }
        
        try:
            with open(TEMP_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
            os.replace(TEMP_STATE_FILE, STATE_FILE)
        except Exception as e:
            logger.error(f"Error saving device state: {str(e)}")


def load_state() -> Dict[str, Any]:
    """
    Load state from device_state.json, creating default if missing or corrupted.
    Automatically checks and applies 9:00 AM day rollover.
    """
    with _state_lock:
        if not STATE_FILE.exists():
            logger.info("State file does not exist. Creating default state.")
            state = get_default_state()
            state = check_and_apply_9am_rollover(state)
            save_state(state)
            return state

        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception as e:
            logger.error(f"Error loading state file: {str(e)}. Falling back to default.")
            state = get_default_state()

        state = check_and_apply_9am_rollover(state)
        save_state(state)
        return state


# check_and_apply_screentime_expiration removed (no parental lockouts or screen time limits)


def check_and_apply_9am_rollover(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if the current effective 9:00 AM operating date has advanced.
    If a new day started:
      1. Preserve minutes_banked, total_stars, and streak across day boundaries.
      2. Reset sessions_today to 0.
      3. Reset morning_battery_bonus_claimed to False.
      4. Run morning battery check (>50% awards +5 bonus minutes).
      5. PRESERVE current_level (level progress persists across days).
    """
    current_effective_date = compute_effective_operating_date()
    state_effective_date = state.get("effective_date", "")

    if state_effective_date != current_effective_date:
        # Save preserved values
        preserved_level = state.get("current_level", 1)
        preserved_test = state.get("current_test_in_level", 1)
        preserved_minutes = state.get("minutes_banked", 0)
        preserved_stars = state.get("total_stars", 120)
        preserved_streak = state.get("streak", 3)
        history = state.get("history", [])

        # Reset daily variables
        state["effective_date"] = current_effective_date
        state["operating_day_start"] = f"{current_effective_date}T09:00:00"
        state["current_level"] = preserved_level
        state["current_test_in_level"] = preserved_test
        state["sessions_today"] = 0
        state["minutes_banked"] = preserved_minutes
        state["total_stars"] = preserved_stars
        state["streak"] = preserved_streak
        state["unlocked_until"] = None
        state["morning_battery_bonus_claimed"] = False

        # Run Morning Battery Bonus check for the new day
        battery_info = get_mock_battery_telemetry()
        bonus_eval = evaluate_morning_battery_bonus(battery_info.get("charge_percent", 0))

        if bonus_eval["eligible"]:
            state["minutes_banked"] += bonus_eval["bonus_minutes"]
            state["morning_battery_bonus_claimed"] = True

        state["last_battery_check"] = {
            "timestamp": datetime.now().isoformat(),
            "charge_percent": battery_info.get("charge_percent", 0),
            "bonus_awarded": bonus_eval["bonus_minutes"],
            "message": bonus_eval["message"]
        }

    return state
