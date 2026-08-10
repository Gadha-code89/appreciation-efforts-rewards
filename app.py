"""
app.py - My Little Wins Streamlit Web Interface for iPad/Web Browsers
# Hot-reload force touch: v1.0.6
"""

import streamlit as st
import json
import random
import os
import base64
from datetime import datetime, timedelta, date
from dotenv import load_dotenv

load_dotenv()

from core.logger import logger
from core.state import load_state, save_state, check_and_apply_9am_rollover
from core.scoring import generate_new_quiz, grade_quiz
from core.reward import complete_mission, confirm_mission
from core.badges import BADGE_CATALOG, evaluate_badges
from core.levels import get_level_info, evaluate_level_up
from agents_app.reporting_agent import run_daily_reporting_agent

# DB module
import core.db as db

st.set_page_config(
    page_title="My Little Wins",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize Session State Variables
if "family_id" not in st.session_state:
    st.session_state.family_id = None

if "family_username" not in st.session_state:
    st.session_state.family_username = None

if "parent_pin" not in st.session_state:
    st.session_state.parent_pin = "1234"

if "user_role" not in st.session_state:
    st.session_state.user_role = None  # None, "child", "parent"

if "child_id" not in st.session_state:
    st.session_state.child_id = None

if "child_name" not in st.session_state:
    st.session_state.child_name = "Child"

if "selected_mission_id" not in st.session_state:
    st.session_state.selected_mission_id = None

if "current_math_quiz" not in st.session_state:
    st.session_state.current_math_quiz = None

if "math_answers" not in st.session_state:
    st.session_state.math_answers = {}

if "math_mission_stage" not in st.session_state:
    st.session_state.math_mission_stage = "not_started"  # not_started, quiz, retry, result

if "last_math_score" not in st.session_state:
    st.session_state.last_math_score = None

if "last_math_attempts" not in st.session_state:
    st.session_state.last_math_attempts = []

if "active_math_attempt_id" not in st.session_state:
    st.session_state.active_math_attempt_id = None



# Styling (Typo.love & Nudot aesthetics)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka+One&family=Outfit:wght@400;600;800&display=swap');

    [data-testid="column"], 
    [data-testid="stVerticalBlock"], 
    .element-container {
        overflow: visible !important;
    }

    .stApp {
        background-color: #FFFDF9 !important;
        color: #334155 !important;
        font-family: 'Outfit', sans-serif !important;
    }

    h1, h2, h3, .main-title {
        font-family: 'Fredoka One', cursive, sans-serif !important;
    }

    .main-title {
        font-size: 3rem !important;
        color: #EC4899 !important;
        text-align: center;
        text-shadow: 2px 2px 0px rgba(0, 0, 0, 0.08);
        margin-bottom: 5px;
        margin-top: -10px;
    }

    .subtitle {
        font-size: 1.1rem;
        color: #64748B;
        text-align: center;
        font-weight: 800;
        margin-bottom: 25px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Unified Glass Cards */
    .card {
        background-color: #FFFFFF !important;
        border: 4px solid #FFE4E6 !important;
        border-radius: 24px !important;
        padding: 22px !important;
        margin-bottom: 15px !important;
        box-shadow: 0px 8px 0px rgba(0, 0, 0, 0.03) !important;
    }

    .question-card {
        background-color: #FFFFFF !important;
        border: 4px solid #FFE4E6 !important;
        border-radius: 28px 14px 28px 14px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0px 6px 0px rgba(0,0,0,0.03);
    }

    /* Symmetrical text inputs to match cards */
    div[data-testid="stForm"] div[data-testid="stTextInput"] input {
        background-color: #FFFFFF !important;
        color: #334155 !important;
        border: 4px solid #FFE4E6 !important;
        border-radius: 28px 14px 28px 14px !important;
        padding: 10px 18px !important;
        font-family: 'Fredoka One', sans-serif !important;
        font-size: 1.3rem !important;
        box-shadow: 0px 6px 0px rgba(0,0,0,0.03) !important;
        height: 58px !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stForm"] div[data-testid="stTextInput"] input:focus {
        border-color: #EC4899 !important;
    }
    div[data-testid="stForm"] div[data-testid="stTextInput"] {
        margin-bottom: 15px !important;
    }

    /* Buttons */
    .stButton>button {
        font-family: 'Fredoka One', sans-serif !important;
        border-radius: 20px !important;
        border: 3px solid #FFE4E6 !important;
        box-shadow: 0px 4px 0px rgba(0, 0, 0, 0.05) !important;
        font-size: 1.10rem !important;
        padding: 10px 20px !important;
    }

    .stButton>button:hover {
        border-color: #EC4899 !important;
    }

    /* Dark Mode Overrides */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background-color: #0F172A !important;
            color: #E2E8F0 !important;
        }
        .card, .question-card {
            background-color: #1E293B !important;
            border-color: #334155 !important;
        }
        div[data-testid="stForm"] div[data-testid="stTextInput"] input {
            background-color: #1E293B !important;
            border-color: #334155 !important;
            color: #FFFFFF !important;
        }
        .stButton>button {
            border-color: #334155 !important;
        }
    }

    /* Hide Streamlit Community Cloud headers, menus, and footers */
    header[data-testid="stHeader"], 
    header, 
    #MainMenu, 
    footer, 
    .viewerBadge_container__172w2,
    div[data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
</style>
""", unsafe_allow_html=True)


def switch_profile():
    st.session_state.active_math_attempt_id = None
    st.session_state.user_role = None
    st.session_state.child_id = None
    st.session_state.current_math_quiz = None
    st.session_state.math_answers = {}
    st.session_state.math_mission_stage = "not_started"
    st.rerun()


# ==================== STEP 2: FAMILY LOGIN / REGISTER ====================
if db.is_db_enabled() and st.session_state.family_id is None:
    st.markdown('<div class="main-title">🌱 My Little Wins</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Log in or Register your Family Account</div>', unsafe_allow_html=True)
    
    login_tab, register_tab = st.tabs(["🔐 Log In", "📝 Register Family"])
    
    with login_tab:
        l_user = st.text_input("Family Username:", key="login_username")
        l_pass = st.text_input("Family Password:", type="password", key="login_password")
        if st.button("Log In 🚀", use_container_width=True, key="login_action_btn"):
            family = db.login_family(l_user, l_pass)
            if family:
                st.session_state.family_id = family["family_id"]
                st.session_state.family_username = family["username"]
                st.session_state.parent_pin = family["parent_pin"]
                st.success("Successfully logged in!")
                st.rerun()
            else:
                st.error("Invalid Username or Password!")
                
    with register_tab:
        r_user = st.text_input("Choose Family Username:", key="reg_username")
        r_pass = st.text_input("Choose Family Password:", type="password", key="reg_password")
        r_pin = st.text_input("Set Parent PIN (4-digits):", type="password", max_chars=4, key="reg_pin")
        if st.button("Register Family ➕", use_container_width=True, key="reg_action_btn"):
            if r_user.strip() and r_pass.strip() and r_pin.strip():
                if len(r_pin.strip()) != 4 or not r_pin.strip().isdigit():
                    st.error("PIN must be exactly 4 digits!")
                else:
                    family = db.register_family(r_user, r_pass, r_pin)
                    if family:
                        st.session_state.family_id = family["family_id"]
                        st.session_state.family_username = family["username"]
                        st.session_state.parent_pin = family["parent_pin"]
                        st.success("Family account created successfully!")
                        st.rerun()
                    else:
                        st.error("Username already taken! Try another one.")
            else:
                st.error("Please fill in all fields!")
    st.stop()


# Load fallback state if DB is offline
state = {}
streak = 0
total_stars = 0
badges = []
missions = []
stars_today = 0

if not db.is_db_enabled():
    state = load_state()
    streak = state.get("streak", 0)
    total_stars = state.get("total_stars", 0)
    badges = state.get("badges", [])
    missions = state.setdefault("daily_missions", [])
    missions.sort(key=lambda m: 0 if m.get("id") == "math_mission" else (2 if (m.get("id") == "reading" or "read" in m.get("title", "").lower()) else 1))
    stars_today = sum(1 for m in missions if m.get("status") == "Completed")


# ==================== STEP 3: PROFILE SELECTOR ====================
if st.session_state.user_role is None:
    st.markdown('<div class="main-title">🌱 My Little Wins</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">A place to grow, accomplish, and celebrate effort!</div>', unsafe_allow_html=True)
    
    col_empty, col_logout = st.columns([3, 1])
    with col_logout:
        if db.is_db_enabled():
            if st.button("Log Out 🔄", use_container_width=True, key="logout_family_btn"):
                st.session_state.family_id = None
                st.rerun()
                
    st.write("")
    
    if db.is_db_enabled():
        children_list = db.get_children(st.session_state.family_id)
        parent_pin_target = st.session_state.parent_pin
    else:
        children_list = [{"child_id": "local", "name": "Child"}]
        parent_pin_target = state.get("parent_pin", "1234")
        
    st.write("### Who is playing today? 🤖")
    
    total_profiles = 1 + len(children_list)
    cols = st.columns(min(total_profiles, 4))
    
    # Parent Card
    with cols[0]:
        st.markdown("""
        <div class="card" style="text-align: center; padding: 20px;">
            <div style="font-size: 3rem; margin-bottom: 8px;">👩</div>
            <h4 style="margin: 0;">Parent</h4>
        </div>
        """, unsafe_allow_html=True)
        pin_input = st.text_input("Enter Parent PIN:", type="password", key="parent_pin_selector", label_visibility="collapsed", placeholder="PIN")
        if st.button("Enter ⚙️", use_container_width=True, key="parent_enter_btn"):
            if pin_input.strip() == parent_pin_target:
                st.session_state.user_role = "parent"
                st.rerun()
            else:
                st.error("Incorrect PIN!")
                
    # Children Cards
    for idx, child in enumerate(children_list):
        col_idx = (idx + 1) % 4
        with cols[col_idx]:
            st.markdown(f"""
            <div class="card" style="text-align: center; padding: 20px;">
                <div style="font-size: 3rem; margin-bottom: 8px;">👧</div>
                <h4 style="margin: 0;">{child['name']}</h4>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Go 🚀", use_container_width=True, key=f"child_go_{child.get('child_id', idx)}"):
                st.session_state.user_role = "child"
                st.session_state.child_id = child.get("child_id")
                st.session_state.child_name = child["name"]
                st.rerun()


# ==================== STEP 4: CHILD VIEW ====================
elif st.session_state.user_role == "child":
    # Load Child State dynamically from Supabase if enabled
    if db.is_db_enabled():
        child_id = st.session_state.child_id
        child = db.get_child_by_id(child_id)
        
        # Calendar-day rollover check
        last_login_str = child.get("last_login_date")
        today_str = db.get_local_operating_date()
        if last_login_str != today_str:
            if not last_login_str:
                gap = 1
            else:
                try:
                    last_login_date = datetime.strptime(last_login_str, "%Y-%m-%d").date()
                    today_date = datetime.strptime(today_str, "%Y-%m-%d").date()
                    gap = (today_date - last_login_date).days
                except Exception:
                    gap = 1
            db.apply_rollover_db(child_id, gap)
            child = db.get_child_by_id(child_id)
            if st.session_state.math_mission_stage != "quiz":
                st.session_state.active_math_attempt_id = None
            
        streak = child["streak"]
        total_stars = child["total_stars"]
        current_level = child["current_level"]
        current_test_in_level = child["current_test_in_level"]
        yesterday_reward = child.get("yesterday_reward_praise", "")
        tomorrow_reward = child.get("tomorrow_reward", "")
        
        badges = db.get_child_badges(child_id)
        missions = db.get_daily_missions(child_id)
        # In-place sort: Math first, Reading last
        missions.sort(key=lambda m: 0 if m.get("id") == "math_mission" else (2 if (m.get("id") == "reading" or "read" in m.get("title", "").lower()) else 1))
        
        reading_log = db.get_reading_logs(child_id)
        journey = db.get_journey_history(child_id)
        stars_today = sum(1 for m in missions if m.get("status") == "Completed")
    else:
        current_level = state.get("current_level", 1)
        current_test_in_level = state.get("current_test_in_level", 1)
        yesterday_reward = state.get("yesterday_reward_praise", "")
        tomorrow_reward = state.get("tomorrow_reward", "")
        reading_log = state.get("reading_log", [])
        journey = state.get("journey", [])

    # Header bar
    col_logo, col_switch = st.columns([3, 1])
    with col_logo:
        st.markdown('<h2 style="margin: 0; color: #EC4899;">🌱 My Little Wins</h2>', unsafe_allow_html=True)
    with col_switch:
        if st.button("Switch Profile 🔄", use_container_width=True, key="switch_profile_btn_child"):
            switch_profile()

    # Motivational child greeting banner
    st.markdown(f"""
    <div style="background-color: #ECFDF5; border-left: 6px solid #10B981; padding: 15px; border-radius: 12px; margin-top: 15px; margin-bottom: 15px; font-weight: 600; color: #065F46;">
        Hi {st.session_state.get('child_name', 'there')}! Your next adventure is waiting! 🚀 What will you accomplish today? Remember: every little effort counts. ❤️
    </div>
    """, unsafe_allow_html=True)

    # Visual indicators panel
    badge_emojis = []
    for b_id in badges:
        b_info = BADGE_CATALOG.get(b_id)
        if b_info:
            badge_emojis.append(b_info["name"].split()[0])
    badge_display = " ".join(badge_emojis) if badge_emojis else "None yet!"

    ind_col1, ind_col2, ind_col3, ind_col4 = st.columns(4)
    with ind_col1:
        st.markdown(f'<div class="card" style="text-align: center; padding: 12px;"><div style="font-size: 1.5rem;">🔥</div><b>Streak:</b> {streak} Days</div>', unsafe_allow_html=True)
    with ind_col2:
        st.markdown(f'<div class="card" style="text-align: center; padding: 12px;"><div style="font-size: 1.5rem;">⭐</div><b>Stars Today:</b> {stars_today}</div>', unsafe_allow_html=True)
    with ind_col3:
        st.markdown(f'<div class="card" style="text-align: center; padding: 12px;"><div style="font-size: 1.5rem;">🌟</div><b>Total Stars:</b> {total_stars}</div>', unsafe_allow_html=True)
    with ind_col4:
        st.markdown(f'<div class="card" style="text-align: center; padding: 12px;"><div style="font-size: 1.5rem;">🏅</div><b>Badges:</b> {badge_display}</div>', unsafe_allow_html=True)

    # Yesterday's reward praise alert
    if yesterday_reward:
        st.info(f"🌟 {yesterday_reward}")

    # Tabs definition
    tab_today, tab_math, tab_reading, tab_journey, tab_rewards = st.tabs([
        "🏠 TODAY",
        "✏️ MATH MISSION",
        "📚 READING LOG",
        "🏆 MY JOURNEY",
        "🎁 MY REWARDS"
    ])

    # ---------- TODAY TAB ----------
    with tab_today:
        st.markdown('<div style="font-size: 1.6rem; font-family:\'Fredoka One\'; margin-bottom:15px;">🗺️ TODAY\'S ADVENTURE</div>', unsafe_allow_html=True)

        # Exclude math mission from checklist tasks list since it has a dedicated tab
        checklist_missions = [m for m in missions if m["id"] != "math_mission"]
        
        if not checklist_missions:
            st.write("No tasks set for today. Ask Mom or Dad to set some! 🌟")
        else:
            # Symmetrical list of columns to select checklist mission
            cols = st.columns(len(checklist_missions))
            for idx, m in enumerate(checklist_missions):
                with cols[idx]:
                    status_emoji = "✅" if m["status"] == "Completed" else ("⏳" if m["status"] == "Pending Confirmation" else "💤")
                    btn_label = f"{m['title'].split()[0]}\n{status_emoji}"
                    if st.button(btn_label, key=f"select_m_btn_{m['id']}", use_container_width=True):
                        st.session_state.selected_mission_id = m["id"]

            if st.session_state.selected_mission_id is None:
                st.session_state.selected_mission_id = checklist_missions[0]["id"]

            sel_id = st.session_state.selected_mission_id
            m = next((item for item in checklist_missions if item["id"] == sel_id), checklist_missions[0])

            st.write("")
            st.markdown(f"""
            <div class="card" style="border: 4px solid #FFE4E6; border-radius: 20px;">
                <div style="font-size: 1.8rem; font-family: 'Fredoka One', sans-serif; color: #EC4899; margin-bottom: 5px;">{m['title']}</div>
                <div style="font-size: 1.15rem; font-style: italic; color: #64748B; margin-bottom: 12px;">{m['why']}</div>
                <div style="font-size: 1.1rem; font-weight: bold;">Status: {m['status']}</div>
            </div>
            """, unsafe_allow_html=True)

            if m["status"] == "Not reported":
                st.write("")
                if st.button("I DID IT! 🎉", key="claim_non_math_mission_btn", type="primary", use_container_width=True):
                    if db.is_db_enabled():
                        db.complete_mission_db(m["id"])
                    else:
                        state = complete_mission(m["id"], state)
                        save_state(state)
                    st.balloons()
                    st.success("Great job! Go tell Mom or Dad to confirm. Digit: 🤖 'You actually did it!'")
                    st.rerun()
            elif m["status"] == "Pending Confirmation":
                st.info("⏳ Waiting for Mom or Dad to confirm! Digit: 🤖 *\"You actually completed it! Let's wait for review.\"*")
            elif m["status"] == "Completed":
                st.success("✅ Fully Confirmed! Digit: 🤖 *\"Excellent work! You kept your word.\"*")
                praise_text = m.get("praise", "").strip()
                if praise_text:
                    st.markdown(f"💬 **Mom/Dad says:** *\"{praise_text}\"*")

    # ---------- MATH TAB (NEW DEDICATED TAB) ----------
    with tab_math:
        st.markdown('<div style="font-size: 1.6rem; font-family:\'Fredoka One\'; margin-bottom:15px;">✏️ MATH SPACE</div>', unsafe_allow_html=True)
        
        # Display 4-test progress stars
        completed_tests = current_test_in_level - 1
        progress_stars = "🌟" * completed_tests + "🤍" * (4 - completed_tests)
        
        st.markdown(f"""
        <div class="card" style="border-color: #3B82F6; background: #EFF6FF; padding: 15px !important; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="margin: 0; color: #1E40AF; font-size: 1.3rem;">Level {current_level} Progress</h3>
                    <div style="font-size: 0.9rem; color: #1E3A8A;">Get 4 perfect scores of 10/10 to level up!</div>
                </div>
                <div style="font-size: 1.8rem; font-family: 'Fredoka One';">{progress_stars}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Retrieve Daily Math Mission record
        math_mission = next((m for m in missions if m["id"] == "math_mission"), None)
        
        if st.session_state.math_mission_stage == "not_started":
            st.write("Ready to sharpen your brain muscles? 🧠")
            if st.button("Start Math Quiz 🚀", key="start_math_quiz_tab_btn", type="primary", use_container_width=True):
                st.session_state.math_mission_stage = "quiz"
                st.session_state.current_math_quiz = generate_new_quiz(current_level)
                st.session_state.math_answers = {}
                if db.is_db_enabled():
                    st.session_state.active_math_attempt_id = db.start_math_attempt_db(child_id, current_level)
                st.rerun()

        elif st.session_state.math_mission_stage == "quiz":
            quiz = st.session_state.current_math_quiz
            level_info = get_level_info(quiz["level"])
            st.write(f"**Topic Focus:** {level_info['description']}")

            with st.form("math_quiz_form_tab"):
                student_answers = {}
                for q in quiz["questions"]:
                    clean_q = q['question'].rstrip("?=\t ")
                    q_col, a_col = st.columns([3, 2])
                    with q_col:
                        st.markdown(
                            f'<div class="question-card" style="margin-bottom: 15px; padding: 0px 18px; height: 58px; display: flex; align-items: center;">'
                            f'<div class="question-text" style="font-size: 1.35rem;">Q{q["id"]}. &nbsp; {clean_q} = ?</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    with a_col:
                        ans_str = st.text_input(
                            label=f"Answer for Q{q['id']}",
                            key=f"math_q_input_tab_{q['id']}",
                            placeholder="Enter answer",
                            label_visibility="collapsed"
                        )
                    student_answers[q['id']] = ans_str

                submitted = st.form_submit_button("Submit Quiz Answers 🚀", type="primary", use_container_width=True)

                if submitted:
                    with st.spinner("Evaluating your answers..."):
                        res = grade_quiz(student_answers, quiz)
                        score = res["score"]
                        st.session_state.last_math_score = score
                        st.session_state.last_math_attempts.append(score)
                        
                        # Never Give Up logic
                        if len(st.session_state.last_math_attempts) > 1 and score > st.session_state.last_math_attempts[0]:
                            if db.is_db_enabled():
                                db.unlock_badge_db(child_id, "never_give_up")
                            else:
                                state["never_give_up_triggered"] = True
                                evaluate_badges(state)

                        # Instant autograded stars reward
                        added_stars = 2 if score == 10 else 1
                        
                        if db.is_db_enabled():
                            if st.session_state.get("active_math_attempt_id"):
                                db.complete_math_attempt_db(st.session_state.active_math_attempt_id, score)
                                st.session_state.active_math_attempt_id = None
                            
                            # Auto-complete math mission task on checklist
                            db.complete_mission_db(math_mission["mission_id"], st.session_state.last_math_attempts)
                            db.confirm_mission_db(math_mission["mission_id"], f"Earned {added_stars} stars instantly! 🚀", child_id)
                            
                            # Increment total stars directly
                            new_total_stars = total_stars + added_stars
                            db.save_child_stats(child_id, new_total_stars, streak)
                            
                            # Progression
                            if score == 10:
                                new_test_idx = current_test_in_level + 1
                                if new_test_idx >= 5:
                                    # Level up!
                                    db.update_child_settings(child_id, child["grade_level"], current_level + 1)
                                    db.save_child_stats(child_id, new_total_stars, streak, 1)
                                    db.unlock_badge_db(child_id, "growing_star")
                                    st.session_state.math_mission_stage = "level_up"
                                else:
                                    db.save_child_stats(child_id, new_total_stars, streak, new_test_idx)
                                    st.session_state.math_mission_stage = "result"
                            else:
                                st.session_state.math_mission_stage = "retry"
                            st.rerun()
                        else:
                            # Fallback local
                            state = complete_mission(math_mission["id"], state)
                            state = confirm_mission(math_mission["id"], f"Earned {added_stars} stars instantly! 🚀", state)
                            state["total_stars"] += added_stars
                            
                            if score == 10:
                                val_level_up, next_l, next_t = evaluate_level_up(10, 10, current_level, current_test_in_level)
                                state["current_level"] = next_l
                                state["current_test_in_level"] = next_t
                                save_state(state)
                                if val_level_up:
                                    st.session_state.math_mission_stage = "level_up"
                                else:
                                    st.session_state.math_mission_stage = "result"
                            else:
                                save_state(state)
                                st.session_state.math_mission_stage = "retry"
                            st.rerun()

        elif st.session_state.math_mission_stage == "retry":
            score = st.session_state.last_math_score
            st.warning(f"🤔 You scored {score}/10. That one was tricky! But you earned +1 Star for your effort! 🌟")
            st.write("🤖 Digit: *\"That one looked tough! Want to try again? You didn't give up!\"*")
            
            col_try, col_done = st.columns(2)
            with col_try:
                if st.button("Try Again 💪", key="retry_quiz_btn", type="primary", use_container_width=True):
                    st.session_state.math_mission_stage = "quiz"
                    if db.is_db_enabled():
                        st.session_state.active_math_attempt_id = db.start_math_attempt_db(child_id, current_level)
                    st.rerun()
            with col_done:
                if st.button("Accept & Exit 🏠", key=f"done_quiz_partial_btn", use_container_width=True):
                    st.session_state.math_mission_stage = "not_started"
                    st.session_state.last_math_attempts = []
                    st.rerun()

        elif st.session_state.math_mission_stage == "result":
            score = st.session_state.last_math_score
            st.success(f"🎉 Perfect 10/10! You earned +2 Stars instantly! ⭐⭐")
            st.write("🤖 Digit: *\"Outstanding! Your brain muscles are getting so strong!\"*")
            if st.button("Back to Math Space 🏠", use_container_width=True, key="back_to_m_btn"):
                st.session_state.math_mission_stage = "not_started"
                st.session_state.last_math_attempts = []
                st.rerun()

        elif st.session_state.math_mission_stage == "level_up":
            st.balloons()
            st.success(f"🏆 LEVEL UP GRADUATION! You earned +2 Stars and advanced to Level {current_level}! Amazing work! 🚀")
            st.write("🤖 Digit: *\"You completed 4 perfect tests! That is incredible dedication! Let's start the next adventure!\"*")
            if st.button("Start Next Level 🚀", use_container_width=True, key="start_next_l_btn"):
                st.session_state.math_mission_stage = "not_started"
                st.session_state.last_math_attempts = []
                st.rerun()

    # ---------- READING LOG TAB ----------
    with tab_reading:
        st.markdown('<div style="font-size: 1.6rem; font-family:\'Fredoka One\'; margin-bottom:15px;">📚 MY READING LOG</div>', unsafe_allow_html=True)
        st.write("Record the books you are reading to build your bookshelf! 📖")
        
        # Form to add a book
        with st.form("add_book_form"):
            book_title = st.text_input("Book Title:", placeholder="Enter the name of the book you read...")
            book_author = st.text_input("Author (optional):", placeholder="Who wrote the book?")
            book_status = st.selectbox("Current Status:", ["In Progress 📖", "Completed 🏆"])
            submitted_book = st.form_submit_button("Log Book 📖", type="primary", use_container_width=True)
            
            if submitted_book:
                if book_title.strip():
                    status_val = "In Progress" if "In Progress" in book_status else "Completed (Pending Confirmation)"
                    
                    if db.is_db_enabled():
                        db.log_book_db(child_id, book_title.strip(), book_author.strip(), status_val)
                        # Auto-complete daily reading task
                        for m in missions:
                            if m["id"] == "reading" and m["status"] == "Not reported":
                                db.complete_mission_db(m["mission_id"])
                    else:
                        book_entry = {
                            "id": f"b_{int(datetime.now().timestamp())}",
                            "title": book_title.strip(),
                            "author": book_author.strip(),
                            "status": status_val,
                            "praise": "",
                            "date": datetime.now().strftime("%Y-%m-%d")
                        }
                        state.setdefault("reading_log", []).append(book_entry)
                        # Auto-complete daily reading task
                        for m in missions:
                            if m["id"] == "reading" and m["status"] == "Not reported":
                                state = complete_mission("reading", state)
                        save_state(state)
                    st.balloons()
                    st.success(f"Added '{book_title.strip()}' to your bookshelf! 🌟")
                    st.rerun()
                else:
                    st.error("Please enter a book title!")
                    
        st.markdown("---")
        st.markdown('<div style="font-size: 1.4rem; font-family:\'Fredoka One\'; margin-bottom:10px;">📖 MY BOOKSHELF</div>', unsafe_allow_html=True)
        
        if not reading_log:
            st.info("Your bookshelf is empty. Log your first book above! 🌟")
        else:
            for idx, book in enumerate(reversed(reading_log)):
                author_text = f" by {book['author']}" if book.get('author') else ""
                
                status = book.get("status", "In Progress")
                if status == "In Progress":
                    badge_html = '<span style="background-color: #FEF3C7; color: #D97706; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">📖 In Progress</span>'
                elif status == "Completed (Pending Confirmation)":
                    badge_html = '<span style="background-color: #DBEAFE; color: #2563EB; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">⏳ Waiting for Approval</span>'
                else:
                    badge_html = '<span style="background-color: #D1FAE5; color: #059669; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">🏆 Completed</span>'
                
                st.markdown(f"""
                <div class="card" style="border-left: 6px solid #8B5CF6; padding: 15px !important; margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div style="font-size: 1.25rem; font-weight: bold; color: #6D28D9;">📘 {book['title']}{author_text}</div>
                        {badge_html}
                    </div>
                    <div style="font-size: 0.85rem; color: #6B7280;">Logged on: {book['date']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if status == "In Progress":
                    if st.button(f"I Finished It! 🏆", key=f"finish_book_btn_{book.get('id', idx)}", use_container_width=True):
                        if db.is_db_enabled():
                            book_id = book.get("id")
                            # Fetch exact book record UUID if exists, otherwise try by title matching
                            if not book_id:
                                db_books = db.get_reading_logs(child_id)
                                matching_book = next((b for b in db_books if b["title"] == book["title"]), None)
                                book_id = matching_book["book_id"] if matching_book else None
                            if book_id:
                                db.update_book_status_db(book_id, "Completed (Pending Confirmation)", "", child_id)
                            # Auto-complete daily reading task
                            for m in missions:
                                if m["id"] == "reading" and m["status"] == "Not reported":
                                    db.complete_mission_db(m["mission_id"])
                        else:
                            book["status"] = "Completed (Pending Confirmation)"
                            # Auto-complete daily reading task
                            for m in missions:
                                if m["id"] == "reading" and m["status"] == "Not reported":
                                    state = complete_mission("reading", state)
                            save_state(state)
                        st.balloons()
                        st.success(f"Marked '{book['title']}' as finished! Tell Mom or Dad to confirm. 🌟")
                        st.rerun()
                elif status == "Completed" and book.get("praise"):
                    st.markdown(f"💬 **Mom/Dad says:** *\"{book['praise']}\"*")

    # ---------- JOURNEY TAB ----------
    with tab_journey:
        lifetime_stars = total_stars
        st.markdown(f"""
        <div class="card" style="text-align: center; border-color: #F59E0B; background: #FFFBEB; margin-bottom: 20px !important;">
            <div style="font-size: 3rem; margin-bottom: 5px;">🌟</div>
            <h3 style="margin-bottom: 5px; color: #B45309;">Lifetime Stars Collected:</h3>
            <div style="font-size: 2.2rem; color: #D97706; font-weight: bold;">
                {lifetime_stars} Stars
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div style="font-size: 1.6rem; font-family:\'Fredoka One\'; margin-bottom:15px;">🏅 MY COLLECTION</div>', unsafe_allow_html=True)
        
        # Badge grid
        badge_cols = st.columns(3)
        for idx, (b_id, b_info) in enumerate(BADGE_CATALOG.items()):
            with badge_cols[idx % 3]:
                if b_id in badges:
                    st.markdown(f"""
                    <div class="card" style="text-align: center; border: 3px solid #10B981; background: #ECFDF5; padding: 15px !important; margin-bottom: 12px;">
                        <div style="font-size: 2.2rem; margin-bottom: 5px;">{b_info['name'].split()[0]}</div>
                        <div style="font-weight: 800; color: #065F46;">{b_info['name']}</div>
                        <div style="font-size: 0.82rem; color: #047857;">{b_info['desc']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="card" style="text-align: center; border: 3px dashed #D1D5DB; background: #F9FAFB; opacity: 0.5; padding: 15px !important; margin-bottom: 12px;">
                        <div style="font-size: 2.2rem; filter: grayscale(100%); margin-bottom: 5px;">🔒</div>
                        <div style="font-weight: bold; color: #4B5563;">{b_info['name']}</div>
                        <div style="font-size: 0.82rem; color: #6B7280;">{b_info['desc']}</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div style="font-size: 1.6rem; font-family:\'Fredoka One\'; margin-bottom:15px;">🏆 MY JOURNEY HISTORY</div>', unsafe_allow_html=True)
        if not journey:
            st.write("You are just beginning your adventure! Accomplishments will show up here tomorrow. 🌱")
        else:
            for entry in reversed(journey):
                st.markdown(f"""
                <div class="card">
                    <div style="font-weight: bold; font-size: 1.15rem; color: #EC4899; margin-bottom: 5px;">☀️ Date: {entry['date']}</div>
                    <div style="font-size: 0.95rem; margin-bottom: 4px;"><b>Stars Earned:</b> ⭐ {entry.get('stars_earned', 0)}</div>
                    <div style="font-size: 0.95rem;"><b>Missions Completed:</b></div>
                    <ul style="margin: 3px 0 0 0; padding-left: 20px;">
                        {"".join([f"<li>{title}</li>" for title in entry.get('completed_missions', [])])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)

    # ---------- REWARDS TAB ----------
    with tab_rewards:
        st.markdown('<div style="font-size: 1.6rem; font-family:\'Fredoka One\'; margin-bottom:15px;">🎁 MY REWARDS</div>', unsafe_allow_html=True)
        
        st.write("")
        st.markdown(f"""
        <div class="card" style="text-align: center; border-color: #EC4899;">
            <div style="font-size: 3rem; margin-bottom: 10px;">🎮</div>
            <h3 style="margin-bottom: 5px;">Yesterday's Accomplished Reward:</h3>
            <div style="font-size: 1.4rem; color: #EC4899; font-weight: bold; margin-bottom: 10px;">
                {yesterday_reward if yesterday_reward else "Ready to complete missions today!"}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        st.markdown(f"""
        <div class="card" style="text-align: center; border-color: #3B82F6;">
            <div style="font-size: 3rem; margin-bottom: 10px;">🎁</div>
            <h3 style="margin-bottom: 5px;">Tomorrow's Upcoming Reward:</h3>
            <div style="font-size: 1.3rem; color: #3B82F6; font-weight: bold;">
                {tomorrow_reward if tomorrow_reward else "Mom or Dad is deciding. Do your best!"}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ==================== STEP 5: PARENT VIEW ====================
elif st.session_state.user_role == "parent":
    # Header bar
    col_logo, col_switch = st.columns([3, 1])
    with col_logo:
        st.markdown('<h2 style="margin: 0; color: #4F46E5;">👩 Parent Settings Panel</h2>', unsafe_allow_html=True)
    with col_switch:
        if st.button("Switch Profile 🔄", use_container_width=True, key="switch_profile_btn_parent"):
            switch_profile()

    st.write("")
    tab_p_status, tab_p_config = st.tabs([
        "📊 TODAY'S STATUS & CONFIRMATIONS",
        "⚙️ CONFIGURATION & SETTINGS"
    ])

    # Load child options dynamically if DB is enabled
    children_list = []
    active_child = None
    active_child_id = None
    
    if db.is_db_enabled():
        children_list = db.get_children(st.session_state.family_id)
        if children_list:
            st.selectbox("Select Child to Manage:", [c["name"] for c in children_list], key="parent_active_child_selector")
            sel_name = st.session_state.parent_active_child_selector
            active_child = next(c for c in children_list if c["name"] == sel_name)
            active_child_id = active_child["child_id"]
            
            # Fetch active child status
            missions = db.get_daily_missions(active_child_id)
            missions.sort(key=lambda m: 0 if m.get("id") == "math_mission" else (2 if (m.get("id") == "reading" or "read" in m.get("title", "").lower()) else 1))
            total_stars = active_child["total_stars"]
            streak = active_child["streak"]
    else:
        active_child_id = "local"
        active_child = {"name": "Child", "current_level": state.get("current_level", 1), "grade_level": state.get("grade_level", 3)}

    # ---------- TODAY'S STATUS TAB ----------
    with tab_p_status:
        if db.is_db_enabled() and not children_list:
            st.info("You don't have any children registered yet. Go to the Settings tab to add your first child! 👧")
        else:
            st.subheader(f"Today's Checklist for {active_child['name']}")
            for m in missions:
                status_color = "#10B981" if m["status"] == "Completed" else ("#F59E0B" if m["status"] == "Pending Confirmation" else "#94A3B8")
                st.markdown(f"- **{m['title']}**: <span style='color:{status_color}; font-weight:bold;'>{m['status']}</span>", unsafe_allow_html=True)

            # Confirmations list
            st.write("")
            st.subheader("Pending Completions (Confirmations)")
            pending = [item for item in missions if item["status"] == "Pending Confirmation"]
            
            if not pending:
                st.info("No tasks pending confirmation right now.")
            else:
                for item in pending:
                    st.markdown(f"""
                    <div class="card">
                        <h4>👧 Completed: {item['title']}</h4>
                        <p style="color: #64748B; font-size: 0.9rem;">Category: {item.get('category', 'standard')}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    praise_input = st.text_input(
                        "Add a message of encouragement / praise:",
                        value="Great job! I'm proud of you! ❤️",
                        key=f"praise_input_{item['id']}"
                    )

                    col_approve, col_reject = st.columns(2)
                    with col_approve:
                        if st.button("Confirm & Add Star ⭐", key=f"confirm_btn_{item['id']}", type="primary", use_container_width=True):
                            if db.is_db_enabled():
                                db.confirm_mission_db(item["mission_id"], praise_input, active_child_id)
                            else:
                                state = confirm_mission(item["id"], praise_input, state)
                                save_state(state)
                            st.balloons()
                            st.rerun()
                    with col_reject:
                        if st.button("Needs More Work 🔄", key=f"reject_btn_{item['id']}", use_container_width=True):
                            if db.is_db_enabled():
                                db.reset_mission_status_db(item["mission_id"])
                            else:
                                item["status"] = "Not reported"
                                save_state(state)
                            st.rerun()

            # Pending Book Completions
            st.write("")
            st.subheader("📚 Finished Books (Pending Approval)")
            
            if db.is_db_enabled():
                reading_log = db.get_reading_logs(active_child_id)
            else:
                reading_log = state.setdefault("reading_log", [])
                
            pending_books = [book for book in reading_log if book.get("status") == "Completed (Pending Confirmation)"]
            
            if not pending_books:
                st.info("No completed books pending approval right now.")
            else:
                for idx, book in enumerate(pending_books):
                    author_text = f" by {book['author']}" if book.get('author') else ""
                    st.markdown(f"""
                    <div class="card" style="border-left: 6px solid #8B5CF6; padding: 15px !important;">
                        <div style="font-size: 1.15rem; font-weight: bold; color: #6D28D9;">📘 {book['title']}{author_text}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    book_praise = st.text_input(
                        "Add a message of praise for finishing this book:",
                        value=f"Fantastic job reading '{book['title']}'! I'm so proud of you! ❤️",
                        key=f"book_praise_input_{book.get('id', idx)}"
                    )
                    
                    b_approve, b_reject = st.columns(2)
                    with b_approve:
                        if st.button("Confirm Book & Award Star ⭐", key=f"book_approve_btn_{book.get('id', idx)}", type="primary", use_container_width=True):
                            if db.is_db_enabled():
                                book_id = book.get("book_id")
                                if book_id:
                                    db.update_book_status_db(book_id, "Completed", book_praise, active_child_id)
                            else:
                                book["status"] = "Completed"
                                book["praise"] = book_praise.strip()
                                state["total_stars"] += 1
                                save_state(state)
                            st.balloons()
                            st.rerun()
                    with b_reject:
                        if st.button("Still In Progress 🔄", key=f"book_reject_btn_{book.get('id', idx)}", use_container_width=True):
                            if db.is_db_enabled():
                                book_id = book.get("book_id")
                                if book_id:
                                    db.update_book_status_db(book_id, "In Progress", "", active_child_id)
                            else:
                                book["status"] = "In Progress"
                                save_state(state)
                            st.rerun()

    # ---------- PARENT SETTINGS TAB ----------
    with tab_p_config:
        if db.is_db_enabled() and children_list:
            st.subheader(f"Configure Rewards for {active_child['name']}")
            tomorrow_reward_val = active_child.get("tomorrow_reward", "")
        else:
            st.subheader("Configure Rewards")
            tomorrow_reward_val = state.get("tomorrow_reward", "")

        reward_val = st.text_input("Tomorrow's Reward:", value=tomorrow_reward_val)
        if st.button("Save Tomorrow's Reward 🎁", type="primary"):
            if db.is_db_enabled():
                db.save_rewards_config(active_child_id, reward_val)
            else:
                state["tomorrow_reward"] = reward_val
                save_state(state)
            st.success("Reward configuration saved!")

        if not db.is_db_enabled() or children_list:
            st.write("")
            st.subheader("Edit Daily Checklist Missions")
            for m_idx, m in enumerate(missions):
                if m["id"] == "math_mission":
                    continue
                m_col1, m_col2 = st.columns([4, 1])
                with m_col1:
                    st.write(f"**{m['title']}** ({m.get('category')}) — *{m['why']}*")
                with m_col2:
                    if st.button("Delete ❌", key=f"del_m_btn_{m['id']}", use_container_width=True):
                        if db.is_db_enabled():
                            db.delete_daily_mission(m["mission_id"])
                        else:
                            missions.pop(m_idx)
                            save_state(state)
                        st.rerun()

            st.markdown("---")
            st.write("**Add New Daily Mission**")
            new_title = st.text_input("Mission Title (e.g. 🧹 Clean your room):", key="new_m_title")
            new_why = st.text_input("Why (e.g. 💡 Growing responsibility):", key="new_m_why")
            new_cat = st.selectbox("Category:", ["helpful", "learning"], key="new_m_cat")
            
            if st.button("Add Mission ➕"):
                if new_title.strip() and new_why.strip():
                    title_val = new_title.strip()
                    if title_val and title_val[0].isalnum():
                        title_val = f"❤️ {title_val}"
                    
                    why_val = new_why.strip()
                    if why_val and not why_val.startswith("💡"):
                        why_val = f"💡 {why_val}"

                    if db.is_db_enabled():
                        db.add_daily_mission(active_child_id, title_val, why_val, new_cat)
                    else:
                        new_id = f"m_{int(datetime.now().timestamp())}"
                        missions.append({
                            "id": new_id,
                            "title": title_val,
                            "why": why_val,
                            "status": "Not reported",
                            "praise": "",
                            "category": new_cat
                        })
                        save_state(state)
                    st.success("Mission added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in both Title and Why!")

        # Register New Child
        if db.is_db_enabled():
            st.markdown("---")
            st.subheader("👧 Add new Child Profile")
            new_c_name = st.text_input("Child's Name:", key="new_child_name")
            new_c_grade = st.number_input("Child's Grade Level:", min_value=1, max_value=12, value=3, key="new_child_grade")
            new_c_math = st.number_input("Starting Math Level (1-5):", min_value=1, max_value=5, value=1, key="new_child_math")
            
            if st.button("Create Profile ➕"):
                if new_c_name.strip():
                    child = db.register_child(st.session_state.family_id, new_c_name.strip(), new_c_grade, new_c_math)
                    if child:
                        st.success(f"Profile created for {new_c_name.strip()}!")
                        st.rerun()
                    else:
                        st.error("Profile already exists with this name!")
                else:
                    st.error("Please enter a name!")

        st.markdown("---")
        st.subheader("Adjust Streaks and Stars")
        new_stars = st.number_input("Override Total Stars:", value=int(total_stars))
        new_streak = st.number_input("Override Streak (Days):", value=int(streak))
        new_level = st.number_input("Override Current Math Level (1-5):", value=int(active_child.get("current_level", 1)) if active_child else 1, min_value=1, max_value=5)
        new_grade = st.number_input("Override Grade Level:", value=int(active_child.get("grade_level", 3)) if active_child else 3, min_value=1, max_value=12)

        if st.button("Save Override Values 💾"):
            if db.is_db_enabled():
                db.save_child_stats(active_child_id, new_stars, new_streak)
                db.update_child_settings(active_child_id, new_grade, new_level)
            else:
                state["total_stars"] = int(new_stars)
                state["streak"] = int(new_streak)
                state["current_level"] = int(new_level)
                state["grade_level"] = int(new_grade)
                save_state(state)
            st.success("Override configuration saved!")
            st.rerun()

        st.markdown("---")
        st.subheader("Manual Testing: Daily Rollover")
        
        if st.button("☀️ Force Daily Rollover (New Day)"):
            if db.is_db_enabled():
                db.apply_rollover_db(active_child_id, 1)
            else:
                state["effective_date"] = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                state = check_and_apply_9am_rollover(state)
                save_state(state)
            st.success("Rollover applied! Day reset completed.")
            st.rerun()
