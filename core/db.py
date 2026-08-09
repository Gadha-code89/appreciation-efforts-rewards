"""
core/db.py - Supabase Database Driver Client for Multi-Family and Multi-Child Data Persistence.
"""

import os
import uuid
from datetime import datetime, date
from typing import Dict, Any, List
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        pass


def is_db_enabled() -> bool:
    """Check if the database client is successfully initialized."""
    return supabase is not None


# ==================== FAMILY OPERATIONS ====================

def login_family(username: str, password_plain: str) -> Dict[str, Any]:
    """Authenticate family by username and password."""
    if not is_db_enabled():
        return None
    try:
        res = supabase.table("families").select("*").eq("username", username.strip().lower()).execute()
        if res.data:
            family = res.data[0]
            # Simple password check
            if family["password_hash"] == password_plain.strip():
                return family
        return None
    except Exception:
        return None


def register_family(username: str, password_plain: str, parent_pin: str) -> Dict[str, Any]:
    """Register a new family with a custom parent settings PIN."""
    if not is_db_enabled():
        return None
    try:
        data = {
            "username": username.strip().lower(),
            "password_hash": password_plain.strip(),
            "parent_pin": parent_pin.strip()
        }
        res = supabase.table("families").insert(data).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception:
        return None


def update_parent_pin(family_id: str, new_pin: str) -> bool:
    """Update parent PIN configuration."""
    if not is_db_enabled():
        return False
    try:
        res = supabase.table("families").update({"parent_pin": new_pin.strip()}).eq("family_id", family_id).execute()
        return bool(res.data)
    except Exception:
        return False


# ==================== CHILD OPERATIONS ====================

def get_children(family_id: str) -> List[Dict[str, Any]]:
    """Retrieve list of all child profiles registered to a family."""
    if not is_db_enabled():
        return []
    try:
        res = supabase.table("children").select("*").eq("family_id", family_id).order("created_at").execute()
        return res.data or []
    except Exception:
        return []


def register_child(family_id: str, name: str, grade_level: int, start_level: int) -> Dict[str, Any]:
    """Register a new child under a family and initialize their default missions."""
    if not is_db_enabled():
        return None
    try:
        child_data = {
            "family_id": family_id,
            "name": name.strip(),
            "grade_level": int(grade_level),
            "current_level": int(start_level),
            "current_test_in_level": 1,
            "streak": 0,
            "total_stars": 0,
            "consecutive_rest_days": 0,
            "last_login_date": date.today().isoformat()
        }
        res = supabase.table("children").insert(child_data).execute()
        if not res.data:
            return None
        
        child = res.data[0]
        child_id = child["child_id"]

        # Insert 5 Default Missions
        default_missions = [
            {
                "child_id": child_id,
                "title": "❤️ Daily prayer",
                "why": "💡 Manifest positivity",
                "category": "helpful",
                "status": "Not reported"
            },
            {
                "child_id": child_id,
                "title": "🧹 Tidy your room",
                "why": "💡 Responsibility is key!",
                "category": "helpful",
                "status": "Not reported"
            },
            {
                "child_id": child_id,
                "title": "📚 Read for 20 minutes",
                "why": "💡 Grow your reading power!",
                "category": "learning",
                "status": "Not reported"
            },
            {
                "child_id": child_id,
                "title": "✏️ Finish your homework",
                "why": "💡 Keep your brain sharp!",
                "category": "learning",
                "status": "Not reported"
            },
            {
                "child_id": child_id,
                "title": "🗺️ Complete Math Mission",
                "why": "💡 Grow your math muscles!",
                "category": "learning",
                "status": "Not reported"
            }
        ]
        supabase.table("daily_missions").insert(default_missions).execute()
        return child
    except Exception:
        return None


def get_child_by_id(child_id: str) -> Dict[str, Any]:
    """Fetch child details by ID."""
    if not is_db_enabled():
        return None
    try:
        res = supabase.table("children").select("*").eq("child_id", child_id).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception:
        return None


def update_child_settings(child_id: str, grade_level: int, math_level: int) -> bool:
    """Update child's active level settings from Parent dashboard."""
    if not is_db_enabled():
        return False
    try:
        data = {
            "grade_level": int(grade_level),
            "current_level": int(math_level)
        }
        res = supabase.table("children").update(data).eq("child_id", child_id).execute()
        return bool(res.data)
    except Exception:
        return False


def save_child_stats(child_id: str, stars: int, streak: int, test_in_level: int = None) -> bool:
    """Override streak and stars values."""
    if not is_db_enabled():
        return False
    try:
        data = {
            "total_stars": int(stars),
            "streak": int(streak)
        }
        if test_in_level is not None:
            data["current_test_in_level"] = int(test_in_level)
        res = supabase.table("children").update(data).eq("child_id", child_id).execute()
        return bool(res.data)
    except Exception:
        return False


# ==================== DAILY MISSION OPERATIONS ====================

def get_daily_missions(child_id: str) -> List[Dict[str, Any]]:
    """Retrieve list of today's checklist missions."""
    if not is_db_enabled():
        return []
    try:
        res = supabase.table("daily_missions").select("*").eq("child_id", child_id).execute()
        return res.data or []
    except Exception:
        return []


def add_daily_mission(child_id: str, title: str, why: str, category: str) -> Dict[str, Any]:
    """Create a new daily checklist mission."""
    if not is_db_enabled():
        return None
    try:
        data = {
            "child_id": child_id,
            "title": title.strip(),
            "why": why.strip(),
            "category": category,
            "status": "Not reported"
        }
        res = supabase.table("daily_missions").insert(data).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception:
        return None


def delete_daily_mission(mission_id: str) -> bool:
    """Remove a checklist mission."""
    if not is_db_enabled():
        return False
    try:
        res = supabase.table("daily_missions").delete().eq("mission_id", mission_id).execute()
        return bool(res.data)
    except Exception:
        return False


def complete_mission_db(mission_id: str, math_attempts: List[int] = None) -> bool:
    """Update mission status to Pending Confirmation."""
    if not is_db_enabled():
        return False
    try:
        data = {"status": "Pending Confirmation"}
        if math_attempts is not None:
            data["math_attempts"] = math_attempts
        res = supabase.table("daily_missions").update(data).eq("mission_id", mission_id).execute()
        return bool(res.data)
    except Exception:
        return False


def confirm_mission_db(mission_id: str, praise: str, child_id: str) -> bool:
    """Approve completed checklist mission and increment total stars count."""
    if not is_db_enabled():
        return False
    try:
        # Update mission status to Completed
        res_m = supabase.table("daily_missions").update({
            "status": "Completed",
            "praise": praise.strip()
        }).eq("mission_id", mission_id).execute()
        
        if not res_m.data:
            return False

        # Fetch and increment total_stars
        child = get_child_by_id(child_id)
        if child:
            new_stars = child.get("total_stars", 0) + 1
            supabase.table("children").update({"total_stars": new_stars}).eq("child_id", child_id).execute()
        return True
    except Exception:
        return False


def reset_mission_status_db(mission_id: str) -> bool:
    """Reset checklist mission back to Not reported."""
    if not is_db_enabled():
        return False
    try:
        res = supabase.table("daily_missions").update({
            "status": "Not reported",
            "praise": ""
        }).eq("mission_id", mission_id).execute()
        return bool(res.data)
    except Exception:
        return False


# ==================== READING LOG OPERATIONS ====================

def get_reading_logs(child_id: str) -> List[Dict[str, Any]]:
    """Retrieve logged books list."""
    if not is_db_enabled():
        return []
    try:
        res = supabase.table("reading_logs").select("*").eq("child_id", child_id).order("logged_date", desc=True).execute()
        return res.data or []
    except Exception:
        return []


def log_book_db(child_id: str, title: str, author: str, status: str) -> Dict[str, Any]:
    """Record a book entry on the bookshelf."""
    if not is_db_enabled():
        return None
    try:
        data = {
            "child_id": child_id,
            "title": title.strip(),
            "author": author.strip() if author else "",
            "status": status,
            "logged_date": date.today().isoformat()
        }
        res = supabase.table("reading_logs").insert(data).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception:
        return None


def update_book_status_db(book_id: str, status: str, praise: str, child_id: str) -> bool:
    """Parent confirms book completion and awards extra star."""
    if not is_db_enabled():
        return False
    try:
        res_b = supabase.table("reading_logs").update({
            "status": status,
            "praise": praise.strip()
        }).eq("book_id", book_id).execute()

        if not res_b.data:
            return False

        # Award an extra star if marked Completed by parent
        if status == "Completed":
            child = get_child_by_id(child_id)
            if child:
                new_stars = child.get("total_stars", 0) + 1
                supabase.table("children").update({"total_stars": new_stars}).eq("child_id", child_id).execute()
        return True
    except Exception:
        return False


# ==================== REWARDS & CONFIG OPERATIONS ====================

def save_rewards_config(child_id: str, tomorrow_reward: str) -> bool:
    """Save tomorrow's play reward configurations."""
    if not is_db_enabled():
        return False
    try:
        res = supabase.table("children").update({"tomorrow_reward": tomorrow_reward.strip()}).eq("child_id", child_id).execute()
        return bool(res.data)
    except Exception:
        return False


# ==================== JOURNEY OPERATIONS ====================

def get_journey_history(child_id: str) -> List[Dict[str, Any]]:
    """Retrieve accomplishments logs archive."""
    if not is_db_enabled():
        return []
    try:
        res = supabase.table("journey_history").select("*").eq("child_id", child_id).order("date").execute()
        return res.data or []
    except Exception:
        return []


# ==================== BADGE OPERATIONS ====================

def get_child_badges(child_id: str) -> List[str]:
    """Retrieve unlocked badges catalog IDs."""
    if not is_db_enabled():
        return []
    try:
        res = supabase.table("child_badges").select("badge_catalog_id").eq("child_id", child_id).execute()
        return [row["badge_catalog_id"] for row in res.data] if res.data else []
    except Exception:
        return []


def unlock_badge_db(child_id: str, badge_catalog_id: str) -> bool:
    """Insert unlocked badge."""
    if not is_db_enabled():
        return False
    try:
        res = supabase.table("child_badges").insert({
            "child_id": child_id,
            "badge_catalog_id": badge_catalog_id
        }).execute()
        return bool(res.data)
    except Exception:
        return False


# ==================== ROLLOVER & STREAK CYCLE ====================

def apply_rollover_db(child_id: str, gap_days: int) -> bool:
    """Apply the daily 9:00 AM operating rollover to the child DB state."""
    if not is_db_enabled():
        return False
    try:
        child = get_child_by_id(child_id)
        if not child:
            return False

        missions = get_daily_missions(child_id)
        completed_today = [m["title"] for m in missions if m.get("status") == "Completed"]
        stars_today = len(completed_today)

        # 1. Update Journey Log
        effective_date_str = child.get("last_login_date")
        if not effective_date_str:
            effective_date_str = date.today().isoformat()

        if completed_today:
            supabase.table("journey_history").insert({
                "child_id": child_id,
                "date": effective_date_str,
                "completed_missions": completed_today,
                "stars_earned": stars_today
            }).execute()

        # 2. Update Streak & Rest Days
        new_streak = child.get("streak", 0)
        new_rest_days = child.get("consecutive_rest_days", 0)

        if gap_days == 1:
            if completed_today:
                new_streak += 1
                new_rest_days = 0
            else:
                new_rest_days += 1
                if new_rest_days >= 2:
                    new_streak = 0
        elif gap_days >= 2:
            new_streak = 0
            new_rest_days = gap_days

        # 3. Shift tomorrow_reward into yesterday_reward_praise
        tomorrow_reward = child.get("tomorrow_reward", "").strip()
        yesterday_praise = ""
        if tomorrow_reward:
            yesterday_praise = f"Yesterday you earned {tomorrow_reward}! ❤️"

        # Update Child record
        supabase.table("children").update({
            "streak": new_streak,
            "consecutive_rest_days": new_rest_days,
            "tomorrow_reward": "",
            "yesterday_reward_praise": yesterday_praise,
            "last_login_date": date.today().isoformat()
        }).eq("child_id", child_id).execute()

        # Reset daily missions status back to Not reported
        for m in missions:
            supabase.table("daily_missions").update({
                "status": "Not reported",
                "praise": "",
                "math_attempts": []
            }).eq("mission_id", m["mission_id"]).execute()

        return True
    except Exception:
        return False
