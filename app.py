"""
app.py - Math-for-Minutes Streamlit Web Interface for iPad/Web Browsers
"""

import streamlit as st
import json
import random
import os
import base64
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from core.logger import logger
from core.state import load_state, save_state, check_and_apply_9am_rollover
from core.scoring import generate_new_quiz, grade_quiz
from core.reward import complete_mission, confirm_mission
from core.badges import BADGE_CATALOG, evaluate_badges
from core.levels import get_level_info
from agents_app.reporting_agent import run_daily_reporting_agent

st.set_page_config(
    page_title="My Little Wins",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize Session State Variables
if "user_role" not in st.session_state:
    st.session_state.user_role = None  # None, "child", "parent"

if "selected_mission_id" not in st.session_state:
    st.session_state.selected_mission_id = None

if "current_math_quiz" not in st.session_state:
    st.session_state.current_math_quiz = None

if "math_answers" not in st.session_state:
    st.session_state.math_answers = {}

if "math_mission_stage" not in st.session_state:
    st.session_state.math_mission_stage = "not_started"  # not_started, quiz, result

if "last_math_score" not in st.session_state:
    st.session_state.last_math_score = None

if "last_math_attempts" not in st.session_state:
    st.session_state.last_math_attempts = []


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
    st.session_state.user_role = None
    st.session_state.current_math_quiz = None
    st.session_state.math_answers = {}
    st.session_state.math_mission_stage = "not_started"
    st.rerun()


state = load_state()
streak = state.get("streak", 0)
total_stars = state.get("total_stars", 0)
badges = state.get("badges", [])
missions = state.setdefault("daily_missions", [])
# Sort in-place: Math first, Reading last, others in middle
missions.sort(key=lambda m: 0 if m.get("id") == "math_mission" else (2 if (m.get("id") == "reading" or "read" in m.get("title", "").lower()) else 1))
stars_today = sum(1 for m in missions if m.get("status") == "Completed")


# ==================== PROFILE SELECTOR SCREEN ====================
if st.session_state.user_role is None:
    st.markdown('<div class="main-title">🌱 My Little Wins</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">A place to grow, accomplish, and celebrate effort!</div>', unsafe_allow_html=True)

    col_child, col_parent = st.columns(2)

    with col_child:
        st.markdown("""
        <div class="card" style="text-align: center; padding: 30px;">
            <div style="font-size: 4rem; margin-bottom: 15px;">👧</div>
            <h3 style="margin-bottom: 8px;">Child Profile</h3>
            <p style="color: #64748B; font-size: 0.95rem; margin-bottom: 20px;">Ready for today's accomplishments?</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to My Little Wins 🚀", use_container_width=True, key="child_login_btn"):
            st.session_state.user_role = "child"
            st.rerun()

    with col_parent:
        st.markdown("""
        <div class="card" style="text-align: center; padding: 30px;">
            <div style="font-size: 4rem; margin-bottom: 15px;">👩</div>
            <h3 style="margin-bottom: 8px;">Parent Profile</h3>
            <p style="color: #64748B; font-size: 0.95rem; margin-bottom: 20px;">Review progress and manage rewards.</p>
        </div>
        """, unsafe_allow_html=True)
        pin_input = st.text_input("Parent PIN:", type="password", placeholder="Enter 4-digit PIN", key="parent_pin_input")
        if st.button("Access Parent View ⚙️", use_container_width=True, key="parent_login_btn"):
            if pin_input.strip() == state.get("parent_pin", "1234"):
                st.session_state.user_role = "parent"
                st.rerun()
            else:
                st.error("Incorrect PIN! Try again.")

# ==================== CHILD VIEW ====================
elif st.session_state.user_role == "child":
    # Header bar
    col_logo, col_switch = st.columns([3, 1])
    with col_logo:
        st.markdown('<h2 style="margin: 0; color: #EC4899;">🌱 My Little Wins</h2>', unsafe_allow_html=True)
    with col_switch:
        if st.button("Switch Profile 🔄", use_container_width=True, key="switch_profile_btn_child"):
            switch_profile()

    # Visual indicators panel
    st.write("")
    ind_col1, ind_col2, ind_col3, ind_col4 = st.columns(4)
    with ind_col1:
        st.markdown(f'<div class="card" style="text-align: center; padding: 12px;"><div style="font-size: 1.5rem;">🔥</div><b>Streak:</b> {streak} Days</div>', unsafe_allow_html=True)
    with ind_col2:
        st.markdown(f'<div class="card" style="text-align: center; padding: 12px;"><div style="font-size: 1.5rem;">⭐</div><b>Stars Today:</b> {stars_today}</div>', unsafe_allow_html=True)
    with ind_col3:
        st.markdown(f'<div class="card" style="text-align: center; padding: 12px;"><div style="font-size: 1.5rem;">🌟</div><b>Total Stars:</b> {total_stars}</div>', unsafe_allow_html=True)
    with ind_col4:
        st.markdown(f'<div class="card" style="text-align: center; padding: 12px;"><div style="font-size: 1.5rem;">🏅</div><b>Badges:</b> {len(badges)}</div>', unsafe_allow_html=True)

    # Yesterday's reward praise alert
    yesterday_reward = state.get("yesterday_reward_praise", "").strip()
    if yesterday_reward:
        st.info(f"🌟 {yesterday_reward}")

    # Tabs definition
    tab_today, tab_journey, tab_rewards = st.tabs([
        "🏠 TODAY",
        "🏆 MY JOURNEY",
        "🎁 MY REWARDS"
    ])

    # ---------- TODAY TAB ----------
    with tab_today:
        st.markdown('<div style="font-size: 1.6rem; font-family:\'Fredoka One\'; margin-bottom:15px;">🗺️ TODAY\'S ADVENTURE</div>', unsafe_allow_html=True)

        if not missions:
            st.write("No missions set for today. Ask Mom or Dad to set some! 🌟")
        else:
            # Symmetrical list of columns to select mission
            cols = st.columns(len(missions))
            for idx, m in enumerate(missions):
                with cols[idx]:
                    status_emoji = "✅" if m["status"] == "Completed" else ("⏳" if m["status"] == "Pending Confirmation" else "💤")
                    btn_label = f"{m['title'].split()[0]}\n{status_emoji}"
                    if st.button(btn_label, key=f"select_m_btn_{m['id']}", use_container_width=True):
                        st.session_state.selected_mission_id = m["id"]
                        if m["id"] != "math_mission":
                            st.session_state.math_mission_stage = "not_started"

            # Detail Card
            if st.session_state.selected_mission_id is None:
                st.session_state.selected_mission_id = missions[0]["id"]

            sel_id = st.session_state.selected_mission_id
            m = next((item for item in missions if item["id"] == sel_id), missions[0])

            st.write("")
            st.markdown(f"""
            <div class="card" style="border: 4px solid #FFE4E6; border-radius: 20px;">
                <div style="font-size: 1.8rem; font-family: 'Fredoka One', sans-serif; color: #EC4899; margin-bottom: 5px;">{m['title']}</div>
                <div style="font-size: 1.15rem; font-style: italic; color: #64748B; margin-bottom: 12px;">{m['why']}</div>
                <div style="font-size: 1.1rem; font-weight: bold;">Status: {m['status']}</div>
            </div>
            """, unsafe_allow_html=True)

            # Details action logic
            if m["status"] == "Not reported":
                if m["id"] != "math_mission":
                    st.write("")
                    if st.button("I DID IT! 🎉", key="claim_non_math_mission_btn", type="primary", use_container_width=True):
                        state = complete_mission(m["id"], state)
                        save_state(state)
                        st.balloons()
                        st.success("Great job! Go tell Mom or Dad to confirm. Digit: 🤖 'You actually did it!'")
                        st.rerun()
                else:
                    # Math Mission interactive quiz
                    st.write("")
                    if st.session_state.math_mission_stage == "not_started":
                        if st.button("Start Math Mission 🚀", key="start_math_mission_btn", type="primary", use_container_width=True):
                            st.session_state.math_mission_stage = "quiz"
                            st.session_state.current_math_quiz = generate_new_quiz(state.get("current_level", 1))
                            st.session_state.math_answers = {}
                            st.rerun()

                    elif st.session_state.math_mission_stage == "quiz":
                        quiz = st.session_state.current_math_quiz
                        level_info = get_level_info(quiz["level"])
                        st.write(f"**Topic Focus:** {level_info['description']}")

                        with st.form("math_quiz_form"):
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
                                        key=f"math_q_input_{q['id']}",
                                        placeholder="Enter answer",
                                        label_visibility="collapsed"
                                    )
                                student_answers[q['id']] = ans_str

                            submitted = st.form_submit_button("Submit Mission Answers 🚀", type="primary", use_container_width=True)

                            if submitted:
                                with st.spinner("Evaluating your answers..."):
                                    res = grade_quiz(student_answers, quiz)
                                    score = res["score"]
                                    st.session_state.last_math_score = score
                                    st.session_state.last_math_attempts.append(score)
                                    
                                    # Never Give Up logic
                                    if len(st.session_state.last_math_attempts) > 1 and score > st.session_state.last_math_attempts[0]:
                                        state["never_give_up_triggered"] = True
                                        evaluate_badges(state)

                                    if score == 10:
                                        # Mastered
                                        state = complete_mission(m["id"], state)
                                        m["math_attempts"] = st.session_state.last_math_attempts
                                        save_state(state)
                                        st.session_state.math_mission_stage = "result"
                                        st.balloons()
                                        st.rerun()
                                    else:
                                        # Partially completed (tricky!)
                                        st.session_state.math_mission_stage = "retry"
                                        st.rerun()

                    elif st.session_state.math_mission_stage == "retry":
                        score = st.session_state.last_math_score
                        st.warning(f"🤔 You scored {score}/10. That one was tricky!")
                        st.write("🤖 Digit: *\"That one looked tough! Want to try again? You didn't give up!\"*")
                        
                        col_try, col_done = st.columns(2)
                        with col_try:
                            if st.button("Try Again 💪", key="retry_quiz_btn", type="primary", use_container_width=True):
                                st.session_state.math_mission_stage = "quiz"
                                st.rerun()
                        with col_done:
                            if st.button("Submit as Completed 🌱", key="done_quiz_partial_btn", use_container_width=True):
                                # Record attempt effort
                                state = complete_mission(m["id"], state)
                                m["math_attempts"] = st.session_state.last_math_attempts
                                save_state(state)
                                st.session_state.math_mission_stage = "result"
                                st.rerun()

                    elif st.session_state.math_mission_stage == "result":
                        score = st.session_state.last_math_score
                        badge_label = "🌱 Started" if score < 7 else ("💪 Kept Going" if len(st.session_state.last_math_attempts) > 1 and score < 10 else ("🏆 Mastered" if score == 10 else "🚀 Improved"))
                        
                        st.success(f"🎉 Math quiz submitted for confirmation! Score: {score}/10 ({badge_label})")
                        st.write("🤖 Digit: *\"You figured it out! Go show your parent to confirm.\"*")
                        if st.button("Back to Mission List 🏠", use_container_width=True, key="back_to_m_btn"):
                            st.session_state.math_mission_stage = "not_started"
                            st.session_state.last_math_attempts = []
                            st.rerun()

            elif m["status"] == "Pending Confirmation":
                st.info("⏳ Waiting for Mom or Dad to confirm! Digit: 🤖 *\"You actually completed it! Let's wait for review.\"*")

            elif m["status"] == "Completed":
                st.success("✅ Fully Confirmed! Digit: 🤖 *\"Excellent work! You kept your word.\"*")
                praise_text = m.get("praise", "").strip()
                if praise_text:
                    st.markdown(f"💬 **Mom/Dad says:** *\"{praise_text}\"*")

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
        journey = state.get("journey", [])
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
        tomorrow_reward = state.get("tomorrow_reward", "").strip()
        st.markdown(f"""
        <div class="card" style="text-align: center; border-color: #3B82F6;">
            <div style="font-size: 3rem; margin-bottom: 10px;">🎁</div>
            <h3 style="margin-bottom: 5px;">Tomorrow's Upcoming Reward:</h3>
            <div style="font-size: 1.3rem; color: #3B82F6; font-weight: bold;">
                {tomorrow_reward if tomorrow_reward else "Mom or Dad is deciding. Do your best!"}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ==================== PARENT VIEW ====================
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

    # ---------- TODAY'S STATUS TAB ----------
    with tab_p_status:
        st.subheader("Today's Daily Checklist")
        for m in missions:
            status_color = "#10B981" if m["status"] == "Completed" else ("#F59E0B" if m["status"] == "Pending Confirmation" else "#94A3B8")
            st.markdown(f"- **{m['title']}**: <span style='color:{status_color}; font-weight:bold;'>{m['status']}</span>", unsafe_allow_html=True)

        # Confirmations list
        st.write("")
        st.subheader("Pending Completions (Confirmations)")
        pending = [item for item in missions if item["status"] == "Pending Confirmation"]
        
        if not pending:
            st.info("No missions pending confirmation right now.")
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
                        state = confirm_mission(item["id"], praise_input, state)
                        save_state(state)
                        st.balloons()
                        st.rerun()
                with col_reject:
                    if st.button("Needs More Work 🔄", key=f"reject_btn_{item['id']}", use_container_width=True):
                        item["status"] = "Not reported"
                        save_state(state)
                        st.rerun()

    # ---------- SETTINGS TAB ----------
    with tab_p_config:
        st.subheader("Tomorrow's Reward Configuration")
        reward_val = st.text_input("Tomorrow's Reward:", value=state.get("tomorrow_reward", ""))
        if st.button("Save Tomorrow's Reward 🎁", type="primary"):
            state["tomorrow_reward"] = reward_val
            save_state(state)
            st.success("Reward configuration saved!")

        st.write("")
        st.subheader("Edit Daily Missions")
        for m_idx, m in enumerate(missions):
            m_col1, m_col2 = st.columns([4, 1])
            with m_col1:
                st.write(f"**{m['title']}** ({m.get('category')}) — *{m['why']}*")
            with m_col2:
                if st.button("Delete ❌", key=f"del_m_btn_{m['id']}", use_container_width=True):
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
                new_id = f"m_{int(datetime.now().timestamp())}"
                
                # Check if title already starts with an emoji/non-alphanumeric character
                title_val = new_title.strip()
                if title_val and title_val[0].isalnum():
                    default_emoji = "❤️"
                    title_val = f"{default_emoji} {title_val}"

                why_val = new_why.strip()
                if why_val and not why_val.startswith("💡"):
                    why_val = f"💡 {why_val}"

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

        st.markdown("---")
        st.subheader("Adjust Streaks and Stars")
        new_stars = st.number_input("Override Total Stars:", value=total_stars)
        new_streak = st.number_input("Override Streak (Days):", value=streak)
        new_level = st.number_input("Override Current Math Level (1-5):", value=state.get("current_level", 1), min_value=1, max_value=5)
        new_pin = st.text_input("Override Parent PIN:", value=state.get("parent_pin", "1234"), max_chars=4)

        if st.button("Save Override Values 💾"):
            state["total_stars"] = int(new_stars)
            state["streak"] = int(new_streak)
            state["current_level"] = int(new_level)
            state["parent_pin"] = new_pin
            save_state(state)
            st.success("Override configuration saved!")
            st.rerun()

        st.markdown("---")
        st.subheader("Manual Testing: Daily Rollover")
        st.caption("Testing simulation: Click the button below to force a rollover to a new day. Today's completed tasks will move to 'My Journey' history.")
        
        if st.button("☀️ Force Daily Rollover (New Day)"):
            # Set effective date to yesterday to force rollover condition
            state["effective_date"] = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            state = check_and_apply_9am_rollover(state)
            save_state(state)
            st.success("Rollover applied! Day reset completed.")
            st.rerun()

        st.markdown("---")
        st.subheader("Manual Parent Digest Email Trigger")
        if st.button("📧 Send Parent digest email now", key="parent_digest_p_btn"):
            with st.spinner("Compiling and sending daily report..."):
                report_res = run_daily_reporting_agent()
                if report_res.get("sent_via_resend"):
                    st.success(f"Report emailed to {report_res.get('recipient')}!")
                else:
                    st.info(f"Report saved locally to:\n`{report_res.get('local_file')}`")
