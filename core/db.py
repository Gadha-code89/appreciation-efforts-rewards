"""
core/db.py - Supabase Database Driver Client for Multi-Family and Multi-Child Data Persistence.
"""

import os
import uuid
from datetime import datetime, date, timezone, timedelta
import zoneinfo
from typing import Dict, Any, List
from supabase import create_client, Client
from core.logger import logger

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        pass


def get_local_operating_date() -> str:
    """
    Compute current local operating date in America/Denver timezone
    based on 12:00 AM (midnight) operating cycle rollover boundary.
    """
    now_utc = datetime.now(timezone.utc)
    local_tz = zoneinfo.ZoneInfo("America/Denver")
    local_now = now_utc.astimezone(local_tz)
    return local_now.date().isoformat()


def is_db_enabled() -> bool:
    """Check if the database client is successfully initialized."""
    return supabase is not None


def log_action_db(family_id: str, actor_type: str, actor_name: str, action: str, details: str) -> bool:
    """Insert an audit log record into the database."""
    if not is_db_enabled():
        return False
    try:
        data = {
            "family_id": family_id,
            "actor_type": actor_type,
            "actor_name": actor_name,
            "action": action,
            "details": details
        }
        res = supabase.table("audit_logs").insert(data).execute()
        return bool(res.data)
    except Exception as e:
        logger.error(f"Error in log_action_db: {e}")
        return False


# ==================== FAMILY OPERATIONS ====================

def login_family(username: str, password_plain: str) -> Dict[str, Any]:
    """Authenticate family by username and password."""
    if not is_db_enabled():
        return None
    try:
        res = supabase.table("families").select("*").eq("username", username.strip().lower()).execute()
        if res.data:
            family = res.data[0]
            if family["password_hash"] == password_plain.strip():
                log_action_db(family["family_id"], "parent", "Parent", "login", f"Family '{username}' logged in.")
                return family
        return None
    except Exception as e:
        logger.error(f"Error in login_family: {e}")
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
            family = res.data[0]
            log_action_db(family["family_id"], "parent", "Parent", "register", f"Family '{username}' registered successfully.")
            return family
        return None
    except Exception as e:
        logger.error(f"Error in register_family: {e}")
        return None


def update_parent_pin(family_id: str, new_pin: str) -> bool:
    """Update parent PIN configuration."""
    if not is_db_enabled():
        return False
    try:
        res = supabase.table("families").update({"parent_pin": new_pin.strip()}).eq("family_id", family_id).execute()
        if res.data:
            log_action_db(family_id, "parent", "Parent", "update_pin", "Updated parent configuration settings PIN.")
            return True
        return False
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
        # Check if child with the same name already exists in this family to prevent duplicates
        existing = supabase.table("children").select("child_id").eq("family_id", family_id).eq("name", name.strip()).execute()
        if existing.data:
            res_child = supabase.table("children").select("*").eq("child_id", existing.data[0]["child_id"]).execute()
            return res_child.data[0] if res_child.data else None

        child_data = {
            "family_id": family_id,
            "name": name.strip(),
            "grade_level": int(grade_level),
            "current_level": int(start_level),
            "current_test_in_level": 1,
            "streak": 0,
            "total_stars": 0,
            "consecutive_rest_days": 0,
            "last_login_date": get_local_operating_date()
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
        log_action_db(family_id, "parent", "Parent", "register_child", f"Registered child profile '{name}' (Grade {grade_level}, Math Level {start_level}).")
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
        child = get_child_by_id(child_id)
        if not child:
            return False

        data = {
            "grade_level": int(grade_level),
            "current_level": int(math_level)
        }
        res = supabase.table("children").update(data).eq("child_id", child_id).execute()
        if res.data:
            log_action_db(child["family_id"], "parent", "Parent", "update_settings", f"Updated child '{child['name']}' settings (Grade {grade_level}, Math Level {math_level}).")
            return True
        return False
    except Exception:
        return False


def save_child_stats(child_id: str, stars: int, streak: int, test_in_level: int = None) -> bool:
    """Override streak and stars values."""
    if not is_db_enabled():
        return False
    try:
        child = get_child_by_id(child_id)
        if not child:
            return False

        data = {
            "total_stars": int(stars),
            "streak": int(streak)
        }
        if test_in_level is not None:
            data["current_test_in_level"] = int(test_in_level)
        res = supabase.table("children").update(data).eq("child_id", child_id).execute()
        if res.data:
            log_action_db(child["family_id"], "parent", "Parent", "override_stats", f"Overrode stars and streak values for child '{child['name']}' (Stars: {stars}, Streak: {streak}).")
            return True
        return False
    except Exception:
        return False


# ==================== DAILY MISSION OPERATIONS ====================

def get_daily_missions(child_id: str) -> List[Dict[str, Any]]:
    """Retrieve list of today's checklist missions."""
    if not is_db_enabled():
        return []
    try:
        res = supabase.table("daily_missions").select("*").eq("child_id", child_id).execute()
        missions = res.data or []
        for m in missions:
            m_title = m.get("title", "")
            if "Math Mission" in m_title or "math_mission" in m_title:
                m["id"] = "math_mission"
            elif "Read" in m_title or "reading" in m_title:
                m["id"] = "reading"
            else:
                m["id"] = m["mission_id"]
        return missions
    except Exception:
        return []


def add_daily_mission(child_id: str, title: str, why: str, category: str) -> Dict[str, Any]:
    """Create a new daily checklist mission."""
    if not is_db_enabled():
        return None
    try:
        child = get_child_by_id(child_id)
        if not child:
            return None

        data = {
            "child_id": child_id,
            "title": title.strip(),
            "why": why.strip(),
            "category": category,
            "status": "Not reported"
        }
        res = supabase.table("daily_missions").insert(data).execute()
        if res.data:
            log_action_db(child["family_id"], "parent", "Parent", "add_mission", f"Added daily checklist task '{title}' for child '{child['name']}'.")
            m = res.data[0]
            m["id"] = m["mission_id"]
            return m
        return None
    except Exception as e:
        logger.error(f"Error in add_daily_mission: {e}")
        return None


def delete_daily_mission(mission_id: str) -> bool:
    """Remove a checklist mission."""
    if not is_db_enabled():
        return False
    try:
        res_m = supabase.table("daily_missions").select("child_id, title").eq("mission_id", mission_id).execute()
        if not res_m.data:
            return False
            
        child_id = res_m.data[0]["child_id"]
        title = res_m.data[0]["title"]
        child = get_child_by_id(child_id)

        res = supabase.table("daily_missions").delete().eq("mission_id", mission_id).execute()
        if res.data and child:
            log_action_db(child["family_id"], "parent", "Parent", "delete_mission", f"Deleted daily checklist task '{title}' for child '{child['name']}'.")
            return True
        return False
    except Exception as e:
        logger.error(f"Error in delete_daily_mission: {e}")
        return False


def complete_mission_db(mission_id: str, math_attempts: List[int] = None) -> bool:
    """Update mission status to Pending Confirmation."""
    if not is_db_enabled():
        return False
    try:
        res_m = supabase.table("daily_missions").select("child_id, title").eq("mission_id", mission_id).execute()
        if not res_m.data:
            return False

        child_id = res_m.data[0]["child_id"]
        title = res_m.data[0]["title"]
        child = get_child_by_id(child_id)

        data = {"status": "Pending Confirmation"}
        if math_attempts is not None:
            data["math_attempts"] = math_attempts
            
        res = supabase.table("daily_missions").update(data).eq("mission_id", mission_id).execute()
        if res.data and child:
            log_action_db(child["family_id"], "child", child["name"], "complete_mission", f"Completed daily mission '{title}' (Pending confirmation).")
            return True
        return False
    except Exception:
        return False


def confirm_mission_db(mission_id: str, praise: str, child_id: str) -> bool:
    """Approve completed checklist mission and increment total stars count."""
    if not is_db_enabled():
        return False
    try:
        res_m = supabase.table("daily_missions").select("title").eq("mission_id", mission_id).execute()
        title = res_m.data[0]["title"] if res_m.data else "Task"

        res_m_up = supabase.table("daily_missions").update({
            "status": "Completed",
            "praise": praise.strip()
        }).eq("mission_id", mission_id).execute()
        
        if not res_m_up.data:
            return False

        child = get_child_by_id(child_id)
        if child:
            new_stars = child.get("total_stars", 0) + 1
            supabase.table("children").update({"total_stars": new_stars}).eq("child_id", child_id).execute()
            log_action_db(child["family_id"], "parent", "Parent", "confirm_mission", f"Confirmed daily mission '{title}' for child '{child['name']}' (praise: '{praise}'). Awarded +1 Star.")
        return True
    except Exception:
        return False


def reset_mission_status_db(mission_id: str) -> bool:
    """Reset checklist mission back to Not reported."""
    if not is_db_enabled():
        return False
    try:
        res_m = supabase.table("daily_missions").select("child_id, title").eq("mission_id", mission_id).execute()
        if not res_m.data:
            return False

        child_id = res_m.data[0]["child_id"]
        title = res_m.data[0]["title"]
        child = get_child_by_id(child_id)

        res = supabase.table("daily_missions").update({
            "status": "Not reported",
            "praise": ""
        }).eq("mission_id", mission_id).execute()
        if res.data and child:
            log_action_db(child["family_id"], "parent", "Parent", "reject_mission", f"Flagged daily mission '{title}' as needs more work for child '{child['name']}'.")
            return True
        return False
    except Exception:
        return False


# ==================== READING LOG OPERATIONS ====================

def get_reading_logs(child_id: str) -> List[Dict[str, Any]]:
    """Retrieve logged books list."""
    if not is_db_enabled():
        return []
    try:
        res = supabase.table("reading_logs").select("*").eq("child_id", child_id).order("logged_date", desc=True).execute()
        books = res.data or []
        for b in books:
            b["id"] = b["book_id"]
            # Convert date representation from logged_date
            b["date"] = str(b.get("logged_date", date.today().isoformat()))
        return books
    except Exception:
        return []


def log_book_db(child_id: str, title: str, author: str, status: str) -> Dict[str, Any]:
    """Record a book entry on the bookshelf."""
    if not is_db_enabled():
        return None
    try:
        child = get_child_by_id(child_id)
        if not child:
            return None

        # Check if book is already logged for this child to prevent duplicates
        existing = supabase.table("reading_logs").select("*").eq("child_id", child_id).eq("title", title.strip()).eq("author", author.strip() if author else "").execute()
        if existing.data:
            b = existing.data[0]
            b["id"] = b["book_id"]
            b["date"] = str(b.get("logged_date", date.today().isoformat()))
            return b

        data = {
            "child_id": child_id,
            "title": title.strip(),
            "author": author.strip() if author else "",
            "status": status,
            "logged_date": date.today().isoformat()
        }
        res = supabase.table("reading_logs").insert(data).execute()
        if res.data:
            log_action_db(child["family_id"], "child", child["name"], "log_book", f"Logged book '{title}' by '{author}' ({status}).")
            b = res.data[0]
            b["id"] = b["book_id"]
            b["date"] = str(b.get("logged_date", date.today().isoformat()))
            return b
        return None
    except Exception:
        return None


def update_book_status_db(book_id: str, status: str, praise: str, child_id: str) -> bool:
    """Parent confirms book completion and awards extra star."""
    if not is_db_enabled():
        return False
    try:
        res_b = supabase.table("reading_logs").select("title").eq("book_id", book_id).execute()
        title = res_b.data[0]["title"] if res_b.data else "Book"

        res_b_up = supabase.table("reading_logs").update({
            "status": status,
            "praise": praise.strip()
        }).eq("book_id", book_id).execute()

        if not res_b_up.data:
            return False

        child = get_child_by_id(child_id)
        if child:
            if status == "Completed":
                new_stars = child.get("total_stars", 0) + 1
                supabase.table("children").update({"total_stars": new_stars}).eq("child_id", child_id).execute()
            log_action_db(child["family_id"], "parent" if status == "Completed" else "child", "Parent" if status == "Completed" else child["name"], "update_book", f"Updated book '{title}' status to '{status}'. Praise: '{praise}'.")
        return True
    except Exception:
        return False


# ==================== REWARDS & CONFIG OPERATIONS ====================

def save_rewards_config(child_id: str, tomorrow_reward: str) -> bool:
    """Save tomorrow's play reward configurations."""
    if not is_db_enabled():
        return False
    try:
        child = get_child_by_id(child_id)
        if not child:
            return False

        res = supabase.table("children").update({"tomorrow_reward": tomorrow_reward.strip()}).eq("child_id", child_id).execute()
        if res.data:
            log_action_db(child["family_id"], "parent", "Parent", "save_reward", f"Configured tomorrow's reward for child '{child['name']}': '{tomorrow_reward}'.")
            return True
        return False
    except Exception as e:
        logger.error(f"Error in save_rewards_config: {e}")
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
        child = get_child_by_id(child_id)
        if not child:
            return False

        # Check if the child already has this badge to prevent duplicates
        existing = supabase.table("child_badges").select("badge_catalog_id").eq("child_id", child_id).eq("badge_catalog_id", badge_catalog_id).execute()
        if existing.data:
            return True

        res = supabase.table("child_badges").insert({
            "child_id": child_id,
            "badge_catalog_id": badge_catalog_id
        }).execute()
        if res.data:
            log_action_db(child["family_id"], "child", child["name"], "unlock_badge", f"Unlocked badge '{badge_catalog_id}'!")
            return True
        return False
    except Exception:
        return False


# ==================== ROLLOVER & STREAK CYCLE ====================

def apply_rollover_db(child_id: str, gap_days: int) -> bool:
    """Apply the daily operating rollover to the child DB state."""
    if not is_db_enabled():
        return False
    try:
        child = get_child_by_id(child_id)
        if not child:
            return False

        missions = get_daily_missions(child_id)

        effective_date_str = child.get("last_login_date")
        if not effective_date_str:
            effective_date_str = get_local_operating_date()

        # Calculate stars earned dynamically:
        # 1. Standard checklist missions completed (1 star each, excluding Math)
        standard_stars = sum(1 for m in missions if m.get("status") == "Completed" and m.get("id") != "math_mission")

        # 2. Math quizzes completed on this operating day
        math_stars = 0
        try:
            res_math = supabase.table("math_attempts_log").select("score").eq("child_id", child_id).like("end_time", f"{effective_date_str}%").execute()
            for attempt in (res_math.data or []):
                score = attempt.get("score")
                if score is not None:
                    if score == 10:
                        math_stars += 5
                    elif score >= 8:
                        math_stars += 3
                    elif score >= 5:
                        math_stars += 2
                    else:
                        math_stars += 1
        except Exception as e:
            logger.error(f"Error calculating math stars in rollover: {e}")

        # 3. Books logged/approved on this operating day
        book_stars = 0
        books_completed = []
        books_in_progress = []
        try:
            res_books = supabase.table("reading_logs").select("title, status").eq("child_id", child_id).eq("logged_date", effective_date_str).execute()
            for b in (res_books.data or []):
                status_clean = b.get("status", "")
                if "Completed" in status_clean:
                    books_completed.append(b["title"])
                else:
                    books_in_progress.append(b["title"])
            # Count only completed books for extra stars
            book_stars = len(books_completed)
        except Exception as e:
            logger.error(f"Error calculating book stars in rollover: {e}")

        stars_today = standard_stars + math_stars + book_stars

        # Generate list of completed achievements today
        completed_today = [m["title"] for m in missions if m.get("status") == "Completed"]
        for title in books_completed:
            completed_today.append(f"📖 Finished Book: {title}")
        for title in books_in_progress:
            completed_today.append(f"📖 Started Book: {title}")

        # 1. Update Journey Log (defensive write inside isolated try-except)
        try:
            # Check if journey log already exists for this child and date to prevent duplicate inserts
            res_check = supabase.table("journey_history").select("journey_id").eq("child_id", child_id).eq("date", effective_date_str).execute()
            if not res_check.data and completed_today:
                supabase.table("journey_history").insert({
                    "child_id": child_id,
                    "date": effective_date_str,
                    "completed_missions": completed_today,
                    "stars_earned": stars_today
                }).execute()
        except Exception as e:
            logger.error(f"Failed to write to journey_history in apply_rollover_db: {e}")

        # 1b. Archive detailed daily missions to mission_history table (defensive write inside isolated try-except)
        try:
            res_m_check = supabase.table("mission_history").select("history_id").eq("child_id", child_id).eq("date", effective_date_str).execute()
            if not res_m_check.data:
                for m in missions:
                    m_title = m.get("title", "")
                    if "Math Mission" in m_title or "math_mission" in m_title:
                        comp_source = "math_auto_complete"
                        m_stars = math_stars
                    elif "Read" in m_title or "reading" in m_title:
                        comp_source = "reading_auto_trigger"
                        m_stars = 1 if m["status"] == "Completed" else 0
                    else:
                        comp_source = "child"
                        m_stars = 1 if m["status"] == "Completed" else 0

                    history_payload = {
                        "mission_id": m["mission_id"],
                        "child_id": child_id,
                        "date": effective_date_str,
                        "title": m["title"],
                        "category": m["category"],
                        "why": m.get("why"),
                        "status": m["status"],
                        "math_attempts": m.get("math_attempts") or [],
                        "stars_earned": m_stars,
                        "parent_confirmed": m["status"] == "Completed",
                        "completion_source": comp_source
                    }
                    supabase.table("mission_history").insert(history_payload).execute()
        except Exception as e:
            logger.error(f"Failed to write to mission_history in apply_rollover_db: {e}")

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
            "last_login_date": get_local_operating_date()
        }).eq("child_id", child_id).execute()

        # Reset daily missions status back to Not reported
        for m in missions:
            supabase.table("daily_missions").update({
                "status": "Not reported",
                "praise": "",
                "math_attempts": []
            }).eq("mission_id", m["mission_id"]).execute()

        # Log rollover action
        log_action_db(child["family_id"], "system", "Rollover System", "rollover", f"Completed daily rollover cycle for child '{child['name']}'. Streak: {new_streak}, Stars Today: {stars_today}.")
        return True
    except Exception:
        return False


# ==================== MATH ATTEMPTS LOGGING ====================

def start_math_attempt_db(child_id: str, level: int) -> str:
    """Initialize a math attempt log record and return the UUID."""
    if not is_db_enabled():
        return ""
    try:
        # Check if there is already an active attempt (status = 'started') for this child at this level
        # to prevent duplicate start attempts on double-click
        existing = supabase.table("math_attempts_log").select("attempt_id").eq("child_id", child_id).eq("level", level).eq("status", "started").execute()
        if existing.data:
            return existing.data[0]["attempt_id"]

        # Calculate attempt number in python for safety
        res_attempts = supabase.table("math_attempts_log").select("attempt_id").eq("child_id", child_id).eq("level", level).execute()
        attempt_num = len(res_attempts.data or []) + 1

        data = {
            "child_id": child_id,
            "level": level,
            "attempt_number": attempt_num,
            "status": "started",
            "start_time": datetime.now(timezone.utc).isoformat()
        }
        res_insert = supabase.table("math_attempts_log").insert(data).execute()
        if res_insert.data:
            return res_insert.data[0]["attempt_id"]
        return ""
    except Exception as e:
        logger.error(f"Error in start_math_attempt_db: {e}")
        return ""


def complete_math_attempt_db(attempt_id: str, score: int) -> bool:
    """Mark a math attempt as completed with score and end time."""
    if not is_db_enabled() or not attempt_id:
        return False
    try:
        data = {
            "status": "completed" if score == 10 else "low score",
            "score": score,
            "end_time": datetime.now(timezone.utc).isoformat()
        }
        res = supabase.table("math_attempts_log").update(data).eq("attempt_id", attempt_id).execute()
        return bool(res.data)
    except Exception as e:
        logger.error(f"Error in complete_math_attempt_db: {e}")
        return False


# ==================== BADGE EVALUATION ====================

def evaluate_badges_db(child_id: str) -> List[str]:
    """
    Scan child's database stats, streak, history, and books to unlock new badges.
    Returns the list of newly unlocked badge IDs.
    """
    if not is_db_enabled():
        return []
    try:
        child = get_child_by_id(child_id)
        if not child:
            return []

        # Get currently unlocked badges
        unlocked = set(get_child_badges(child_id))
        new_unlocks = []

        # 1. First Step: at least 1 entry in journey_history
        journey = get_journey_history(child_id)
        if len(journey) >= 1 and "first_step" not in unlocked:
            new_unlocks.append("first_step")

        # 2. On Fire: 3-day streak
        streak = child.get("streak", 0)
        if streak >= 3 and "on_fire" not in unlocked:
            new_unlocks.append("on_fire")

        # 3. Brain Builder & Helpful Hero (10 learning/helpful missions in journey_history)
        total_learning = 0
        total_helpful = 0
        for j in journey:
            completed_missions = j.get("completed_missions") or []
            for title in completed_missions:
                t_lower = title.lower()
                if any(keyword in t_lower for keyword in ["math", "quiz", "homework", "read", "learning", "✏️", "📚", "🗺️"]):
                    total_learning += 1
                if any(keyword in t_lower for keyword in ["tidy", "room", "help", "clean", "🧹", "❤️"]):
                    total_helpful += 1

        if total_learning >= 10 and "brain_builder" not in unlocked:
            new_unlocks.append("brain_builder")
        if total_helpful >= 10 and "helpful_hero" not in unlocked:
            new_unlocks.append("helpful_hero")

        # 4. Growing Star: 50 total stars
        total_stars = child.get("total_stars", 0)
        if total_stars >= 50 and "growing_star" not in unlocked:
            new_unlocks.append("growing_star")

        # Unlock all new badges in DB
        for badge_id in new_unlocks:
            unlock_badge_db(child_id, badge_id)

        return new_unlocks
    except Exception as e:
        logger.error(f"Error in evaluate_badges_db: {e}")
        return []



