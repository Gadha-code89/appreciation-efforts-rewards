"""
core/state.py - Shared Device State Manager with 9:00 AM Local Time Rollover & Atomic Persistence
"""

import json
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

from core.badges import evaluate_badges
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
        
        "total_stars": 0,
        "streak": 0,
        "consecutive_rest_days": 0,
        
        "parent_pin": "1234",
        "yesterday_reward_praise": "",
        "tomorrow_reward": "",
        
        "badges": [],
        "daily_missions": [
            {
                "id": "tidy_room",
                "title": "🧹 Tidy your room",
                "why": "💡 Responsibility is key!",
                "status": "Not reported",
                "praise": "",
                "category": "helpful"
            },
            {
                "id": "reading",
                "title": "📚 Read for 20 minutes",
                "why": "💡 Grow your reading power!",
                "status": "Not reported",
                "praise": "",
                "category": "learning"
            },
            {
                "id": "homework",
                "title": "✏️ Finish your homework",
                "why": "💡 Keep your brain sharp!",
                "status": "Not reported",
                "praise": "",
                "category": "learning"
            },
            {
                "id": "math_mission",
                "title": "🗺️ Complete Math Mission",
                "why": "💡 Grow your math muscles!",
                "status": "Not reported",
                "praise": "",
                "category": "learning",
                "math_attempts": []
            }
        ],
        "journey": [],
        "reading_log": [],
        
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


def check_and_apply_9am_rollover(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if the current effective 9:00 AM operating date has advanced.
    If a new day started:
      1. Move completed daily missions to the journey log.
      2. Manage streak:
         - If >=1 mission completed: Streak incremented, consecutive_rest_days set to 0.
         - If 0 missions completed: Streak is protected on day 1 (consecutive_rest_days = 1).
           If they fail to complete anything on day 2, streak resets to 0.
      3. Shift tomorrow_reward into yesterday_reward_praise.
      4. Reset daily variables & status to "Not reported".
    """
    current_effective_date = compute_effective_operating_date()
    state_effective_date = state.get("effective_date", "")

    if state_effective_date != current_effective_date:
        completed_today = [
            m["title"]
            for m in state.get("daily_missions", [])
            if m.get("status") == "Completed"
        ]
        
        stars_today = len(completed_today)

        # 1. Update Journey Log
        if completed_today:
            journey_entry = {
                "date": state_effective_date,
                "completed_missions": completed_today,
                "stars_earned": stars_today
            }
            state.setdefault("journey", []).append(journey_entry)
            
            # 2. Update Streak (completed tasks)
            state["streak"] = state.get("streak", 0) + 1
            state["consecutive_rest_days"] = 0
            
            # Evaluate new badges
            state = evaluate_badges(state)
        else:
            # Rest day!
            state["consecutive_rest_days"] = state.get("consecutive_rest_days", 0) + 1
            if state["consecutive_rest_days"] >= 2:
                state["streak"] = 0

        # 3. Shift Tomorrow's Reward to Yesterday's Praise
        tomorrow_reward = state.get("tomorrow_reward", "").strip()
        if tomorrow_reward:
            state["yesterday_reward_praise"] = f"Yesterday you earned {tomorrow_reward}! ❤️"
        else:
            state["yesterday_reward_praise"] = ""

        # 4. Reset Daily State
        state["tomorrow_reward"] = ""
        state["effective_date"] = current_effective_date
        state["operating_day_start"] = f"{current_effective_date}T09:00:00"
        
        # Reset daily missions status
        for m in state.get("daily_missions", []):
            m["status"] = "Not reported"
            m["praise"] = ""
            if "math_attempts" in m:
                m["math_attempts"] = []

    return state
