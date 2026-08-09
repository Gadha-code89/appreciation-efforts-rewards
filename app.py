"""
app.py - Math-for-Minutes Streamlit Web Interface for iPad/Web Browsers
"""

import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from core.logger import logger

from agents_app.orchestrator import (
    get_current_system_state,
    generate_new_quiz,
    grade_and_process_submission
)
from core.levels import get_level_info
from agents_app.reporting_agent import run_daily_reporting_agent
import base64
import os

st.set_page_config(
    page_title="Appreciation of Efforts",
    page_icon="✏️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

@st.cache_data
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Custom Styling for modern tablet UI (inspired by Typo.love and Nudot)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka+One&family=Outfit:wght@400;600;800&display=swap');

    /* Prevent Streamlit from cutting off card shadows and morph animations */
    [data-testid="column"], 
    [data-testid="stVerticalBlock"], 
    .element-container {
        overflow: visible !important;
    }

    .stApp {
        background-color: var(--background-color) !important;
        color: var(--text-color) !important;
        font-family: 'Outfit', sans-serif !important;
    }

    h1, h2, h3, .main-title {
        font-family: 'Fredoka One', cursive, sans-serif !important;
    }

    .main-title {
        font-size: 3.2rem !important;
        color: var(--primary-color) !important; /* Warm theme primary accent */
        text-align: center;
        text-shadow: 3px 3px 0px rgba(0, 0, 0, 0.15);
        margin-bottom: 5px;
        margin-top: -20px;
        animation: wobbleTitle 4s infinite alternate ease-in-out;
    }

    @keyframes wobbleTitle {
        0% { transform: rotate(-1deg) scale(1); }
        100% { transform: rotate(1deg) scale(1.02); }
    }

    .subtitle {
        font-size: 1.1rem;
        color: var(--text-color);
        opacity: 0.8;
        text-align: center;
        font-weight: 800;
        margin-bottom: 20px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Floating background blobs (Nudot style) */
    .blob {
        position: fixed;
        border-radius: 50%;
        filter: blur(80px);
        z-index: -1;
        opacity: 0.15; /* Very light so it fits both light and dark backgrounds */
        animation: floatBlob 10s infinite alternate ease-in-out;
        pointer-events: none;
    }
    .blob-1 {
        width: 350px;
        height: 350px;
        background-color: #FFE4E6; /* Soft Rose Pink */
        top: -50px;
        left: -50px;
        animation-duration: 14s;
    }
    .blob-2 {
        width: 400px;
        height: 400px;
        background-color: #FFEDD5; /* Soft Orange */
        bottom: -100px;
        right: -100px;
        animation-duration: 18s;
    }
    .blob-3 {
        width: 300px;
        height: 300px;
        background-color: #E0F2FE; /* Soft Sky Blue */
        top: 40%;
        right: -50px;
        animation-duration: 12s;
    }
    @keyframes floatBlob {
        0% { transform: translate(0px, 0px) scale(1); }
        100% { transform: translate(40px, -40px) scale(1.15); }
    }

    /* Sidebar Styling with solid backgrounds */
    [data-testid="stSidebar"] {
        background-color: #FFF8F0 !important; /* Solid light warm peach in light mode */
        border-right: 4px solid #FFEDD5 !important;
    }

    /* Sidebar buttons styling (Parent Email & Playtime) */
    [data-testid="stSidebar"] button,
    [data-testid="stSidebar"] [data-testid*="BaseButton"],
    section[data-testid="stSidebar"] div.stButton > button {
        font-family: 'Fredoka One', sans-serif !important;
        font-size: 1.05rem !important;
        padding: 10px 18px !important;
        border-radius: 20px 10px 20px 10px !important;
        border: 4px solid var(--primary-color) !important;
        background-color: #FFFFFF !important;
        color: var(--text-color) !important;
        box-shadow: 0px 5px 0px #FFEDD5 !important;
        transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.3s, border-radius 0.3s !important;
        white-space: normal !important;
        line-height: 1.3 !important;
        display: inline-block !important;
    }

    [data-testid="stSidebar"] button:hover,
    [data-testid="stSidebar"] [data-testid*="BaseButton"]:hover,
    section[data-testid="stSidebar"] div.stButton > button:hover {
        transform: translateY(-4px) scale(1.02) rotate(1deg) !important;
        box-shadow: 0px 8px 0px #FFEDD5 !important;
        border-radius: 10px 20px 10px 20px !important;
    }

    [data-testid="stSidebar"] button:active,
    [data-testid="stSidebar"] [data-testid*="BaseButton"]:active,
    section[data-testid="stSidebar"] div.stButton > button:active {
        transform: translateY(2px) scale(0.97) !important;
        box-shadow: 0px 2px 0px #FFEDD5 !important;
    }

    /* Tab container bar styling with solid background - targeted specifically */
    div[data-baseweb="tab-list"],
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 12px !important;
        justify-content: center !important;
        background-color: #FFF8F0 !important; /* Solid warm peach */
        padding: 10px !important;
        border-radius: 24px !important;
        border: 4px solid #FFEDD5 !important;
        box-shadow: 0px 6px 0px rgba(0, 0, 0, 0.03) !important;
        margin-bottom: 20px !important;
    }

    /* Tab styling with button override to fix white-on-white text */
    button[data-baseweb="tab"] {
        font-family: 'Fredoka One', sans-serif !important;
        border-radius: 18px 10px 18px 10px !important;
        padding: 10px 24px !important;
        transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: var(--primary-color) !important;
        color: #FFFFFF !important;
        border: 3px solid var(--primary-color) !important;
        box-shadow: 0px 4px 0px var(--primary-color) !important;
    }

    button[data-baseweb="tab"][aria-selected="false"] {
        background-color: #FFFFFF !important; /* Solid white background */
        color: var(--text-color) !important;
        border: 3px solid #FFEDD5 !important;
        box-shadow: 0px 4px 0px #FFEDD5 !important;
    }

    button[data-baseweb="tab"]:hover {
        transform: translateY(-3px) rotate(1deg) !important;
        border-radius: 10px 18px 10px 18px !important;
    }

    /* Force text and emojis inside tab buttons to inherit the color */
    button[data-baseweb="tab"] div,
    button[data-baseweb="tab"] span,
    button[data-baseweb="tab"] p {
        color: inherit !important;
        font-weight: 800 !important;
    }

    /* Stats Cards with solid backgrounds */
    .stat-card {
        background-color: #FFFFFF !important; /* Solid white */
        border: 4px solid var(--primary-color) !important;
        border-radius: 35px 20px 35px 20px !important;
        padding: 20px;
        text-align: center;
        box-shadow: 0px 8px 0px rgba(0, 0, 0, 0.05) !important;
        margin-bottom: 25px !important;
        transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), border-radius 0.4s ease !important;
    }
    .stat-card:hover {
        transform: translateY(-8px) scale(1.02) rotate(-1deg) !important;
        border-radius: 20px 35px 20px 35px !important;
        box-shadow: 0px 12px 0px rgba(0, 0, 0, 0.05) !important;
    }
    .stat-number {
        font-size: 2.4rem;
        font-weight: 800;
        color: var(--primary-color);
        font-family: 'Fredoka One', sans-serif;
        line-height: 1.1;
    }
    .stat-label {
        font-size: 0.95rem;
        color: var(--text-color);
        font-weight: 800;
        text-transform: uppercase;
        margin-top: 5px;
    }

    /* Status Banner */
    .status-banner {
        border-radius: 28px 15px 28px 15px;
        padding: 22px;
        text-align: center;
        border: 4px solid;
        margin: 20px 0px;
        font-family: 'Fredoka One', sans-serif;
        font-size: 1.6rem;
        transition: all 0.3s ease;
    }
    .status-banner:hover {
        border-radius: 15px 28px 15px 28px;
    }
    .status-unlocked {
        background-color: #ECFDF5 !important; /* Solid light green */
        border-color: #34D399;
        color: #059669;
        box-shadow: 0px 8px 0px rgba(16, 185, 129, 0.1);
    }
    .status-locked {
        background-color: #FFF5F5 !important; /* Solid light red */
        border-color: #FCA5A5;
        color: #DC2626;
        box-shadow: 0px 8px 0px rgba(239, 68, 68, 0.1);
    }

    /* Progress Tracker Card with solid background */
    .progress-box {
        background-color: #FFFFFF !important; /* Solid white */
        border: 4px solid #FFE4E6 !important;
        border-radius: 28px;
        padding: 25px;
        box-shadow: 0px 8px 0px rgba(0,0,0,0.05);
        margin: 20px 0px 30px 0px !important;
    }
    .progress-title {
        font-size: 1.6rem;
        color: var(--primary-color);
        font-family: 'Fredoka One', sans-serif;
        text-align: center;
        margin-bottom: 15px;
    }
    .progress-row {
        display: flex;
        justify-content: space-around;
        align-items: center;
        margin-top: 15px;
    }
    .progress-dot {
        flex: 1;
        text-align: center;
        padding: 12px;
        border-radius: 40% 60% 40% 60% / 60% 40% 60% 40% !important;
        margin: 0px 8px;
        font-family: 'Fredoka One', sans-serif;
        font-weight: 800;
        font-size: 1rem;
        border: 4px solid;
        box-shadow: 0px 5px 0px rgba(0,0,0,0.1);
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }
    .progress-dot:hover {
        border-radius: 60% 40% 60% 40% / 40% 60% 40% 60% !important;
        transform: scale(1.12) rotate(4deg) !important;
    }
    .dot-passed {
        background-color: #ECFDF5 !important;
        border-color: #34D399 !important;
        color: #059669 !important;
    }
    .dot-current {
        background-color: #FEF3C7 !important;
        border-color: #FCD34D !important;
        color: #D97706 !important;
        animation: activePulse 1.2s infinite alternate !important;
    }
    @keyframes activePulse {
        0% { transform: scale(1) rotate(0deg); }
        100% { transform: scale(1.06) rotate(1deg); }
    }
    .dot-locked {
        background-color: #F9FAFB !important;
        border-color: #E5E7EB !important;
        color: var(--text-color) !important;
        opacity: 0.5 !important;
    }

    /* Question Cards with solid background */
    .question-card {
        background-color: #FFFFFF !important; /* Solid white */
        border: 4px solid #FFE4E6 !important;
        border-radius: 28px 14px 28px 14px;
        padding: 20px;
        margin-bottom: 12px;
        box-shadow: 0px 6px 0px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    .question-card:hover {
        border-radius: 14px 28px 14px 28px;
    }

    /* Style all text inputs inside the quiz forms to match the question cards */
    div[data-testid="stForm"] div[data-testid="stTextInput"] input {
        background-color: #FFFFFF !important;
        color: var(--text-color) !important;
        border: 4px solid #FFE4E6 !important;
        border-radius: 28px 14px 28px 14px !important;
        padding: 10px 18px !important;
        font-family: 'Fredoka One', sans-serif !important;
        font-size: 1.3rem !important;
        box-shadow: 0px 6px 0px rgba(0,0,0,0.05) !important;
        height: 58px !important; /* Force same height as question cards */
        transition: all 0.3s ease !important;
    }
    div[data-testid="stForm"] div[data-testid="stTextInput"] input:focus {
        border-color: var(--primary-color) !important;
    }
    div[data-testid="stForm"] div[data-testid="stTextInput"] {
        margin-bottom: 15px !important;
    }

    /* Solid backgrounds for Streamlit Forms and Expanders */
    div[data-testid="stForm"] {
        background-color: #FFFFFF !important;
        border: 4px solid #FFE4E6 !important;
        border-radius: 28px !important;
        padding: 30px !important;
        box-shadow: 0px 8px 0px rgba(0, 0, 0, 0.05) !important;
        margin-bottom: 20px !important;
    }
    div[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 3px solid #FFE4E6 !important;
        border-radius: 20px !important;
        box-shadow: 0px 4px 0px rgba(0, 0, 0, 0.05) !important;
        margin-bottom: 15px !important;
    }

    /* Solid backgrounds for notifications and alert banners (e.g. Battery bonus) */
    div[data-testid="stNotification"], 
    div[data-testid="stAlert"],
    div[data-testid="stAlertContainer"] {
        background-color: #EFF6FF !important; /* Solid light blue */
        border: 2px solid #BFDBFE !important;
        border-radius: 16px !important;
        color: #1E40AF !important;
    }
    
    /* Dark Mode Overrides for solid colors */
    @media (prefers-color-scheme: dark) {
        [data-testid="stSidebar"] {
            background-color: #111827 !important;
            border-right: 4px solid #1F2937 !important;
        }
        button[data-baseweb="tab"][aria-selected="false"] {
            background-color: #1F2937 !important;
            border-color: #374151 !important;
            box-shadow: 0px 4px 0px #374151 !important;
        }
        .stat-card {
            background-color: #1E293B !important;
            border-color: var(--primary-color) !important;
        }
        .status-unlocked {
            background-color: #064E3B !important;
            border-color: #059669;
            color: #A7F3D0;
        }
        .status-locked {
            background-color: #7F1D1D !important;
            border-color: #DC2626;
            color: #FEE2E2;
        }
        .progress-box {
            background-color: #1E293B !important;
            border-color: #374151 !important;
        }
        .question-card {
            background-color: #1E293B !important;
            border-color: #374151 !important;
        }
        div[data-testid="stForm"] div[data-testid="stTextInput"] input {
            background-color: #1E293B !important;
            border-color: #374151 !important;
            color: #FFFFFF !important;
        }
        div[data-testid="stForm"] {
            background-color: #1E293B !important;
            border-color: #374151 !important;
        }
        div[data-testid="stExpander"] {
            background-color: #1E293B !important;
            border-color: #374151 !important;
        }
        div[data-testid="stNotification"], 
        div[data-testid="stAlert"],
        div[data-testid="stAlertContainer"] {
            background-color: #1E3A8A !important;
            border-color: #3B82F6 !important;
            color: #EFF6FF !important;
        }
        .dot-passed {
            background-color: #064E3B !important;
            border-color: #059669 !important;
            color: #A7F3D0 !important;
        }
        .dot-current {
            background-color: #78350F !important;
            border-color: #D97706 !important;
            color: #FDE68A !important;
        }
        .dot-locked {
            background-color: #374151 !important;
            border-color: #4B5563 !important;
            color: #9CA3AF !important;
        }
    }
    .question-text {
        font-size: 1.6rem;
        font-weight: 800;
        color: var(--text-color);
        font-family: 'Fredoka One', sans-serif;
    }
    
    /* Play Button & Form Submits Bubble effect */
    .stButton>button {
        font-family: 'Fredoka One', sans-serif !important;
        font-size: 1.15rem !important;
        padding: 12px 24px !important;
        border-radius: 25px 12px 25px 12px !important;
        border: 4px solid var(--primary-color) !important;
        background-color: var(--background-color) !important;
        color: var(--text-color) !important;
        box-shadow: 0px 6px 0px var(--secondary-background-color) !important;
        transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.3s, border-radius 0.3s !important;
    }
    .stButton>button:hover {
        transform: translateY(-5px) scale(1.04) rotate(1deg) !important;
        box-shadow: 0px 10px 0px var(--secondary-background-color) !important;
        border-radius: 12px 25px 12px 25px !important;
    }
    .stButton>button:active {
        transform: translateY(3px) scale(0.97) !important;
        box-shadow: 0px 2px 0px var(--secondary-background-color) !important;
    }
    
    /* Play Button override - Green wobbly playtime button (handles both main and sidebar play buttons) */
    .play-btn>div>button,
    div.play-btn + div button {
        background-color: #10B981 !important; /* Emerald green */
        color: #FFFFFF !important;
        border-color: #047857 !important;
        box-shadow: 0px 8px 0px #047857 !important;
        font-size: 1.15rem !important;
        padding: 12px 24px !important;
    }
    .play-btn>div>button:hover,
    div.play-btn + div button:hover {
        background-color: #34D399 !important;
        box-shadow: 0px 12px 0px #047857 !important;
    }
    .play-btn>div>button:active,
    div.play-btn + div button:active {
        transform: translateY(4px) !important;
        box-shadow: 0px 4px 0px #047857 !important;
    }

    /* Quest Map / Level-up Journey Styling */
    .quest-container {
        background-color: #FFFFFF !important;
        border: 4px solid #FFE4E6 !important;
        border-radius: 35px !important;
        padding: 30px 20px !important;
        box-shadow: 0px 8px 0px rgba(0, 0, 0, 0.04) !important;
        margin: 25px 0px 30px 0px !important;
        text-align: center;
        overflow: visible !important;
    }
    .quest-title {
        font-family: 'Fredoka One', sans-serif !important;
        font-size: 1.8rem !important;
        color: var(--primary-color) !important;
        margin-bottom: 8px !important;
    }
    .quest-subtitle {
        font-size: 1rem !important;
        color: var(--text-color) !important;
        opacity: 0.8 !important;
        font-weight: bold !important;
        margin-bottom: 25px !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    .quest-map {
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        max-width: 550px !important;
        margin: 0 auto 20px auto !important;
        position: relative !important;
        padding: 0 10px !important;
        overflow: visible !important;
    }
    .quest-node {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        position: relative !important;
        z-index: 2 !important;
    }
    .node-bubble {
        width: 55px !important;
        height: 55px !important;
        border-radius: 50% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        font-size: 1.5rem !important;
        font-family: 'Fredoka One', sans-serif !important;
        border: 4px solid !important;
        box-shadow: 0px 5px 0px rgba(0,0,0,0.1) !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }
    .node-bubble:hover {
        transform: scale(1.15) rotate(5deg) !important;
    }
    .node-label {
        font-family: 'Fredoka One', sans-serif !important;
        font-size: 0.85rem !important;
        margin-top: 8px !important;
    }
    .node-status {
        font-size: 0.75rem !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        margin-top: 3px !important;
        letter-spacing: 0.5px !important;
    }
    .quest-line {
        flex-grow: 1 !important;
        height: 8px !important;
        border-radius: 4px !important;
        margin: -25px 5px 0 5px !important;
        position: relative !important;
        z-index: 1 !important;
    }
    
    /* Passed Node Colors */
    .node-passed .node-bubble {
        background-color: #ECFDF5 !important;
        border-color: #34D399 !important;
        color: #059669 !important;
    }
    .node-passed .node-label { color: #059669 !important; }
    .node-passed .node-status { color: #10B981 !important; }
    .line-passed { background-color: #34D399 !important; }

    /* Current Node Colors */
    .node-current .node-bubble {
        background-color: #FEF3C7 !important;
        border-color: #FCD34D !important;
        color: #D97706 !important;
        animation: activePulse 1.2s infinite alternate !important;
    }
    .node-current .node-label { color: #D97706 !important; }
    .node-current .node-status { color: #F59E0B !important; }
    .line-active { 
        background-color: #FDBA74 !important; 
        animation: activeLine 1.5s infinite alternate ease-in-out !important;
    }
    @keyframes activeLine {
        0% { opacity: 0.6; }
        100% { opacity: 1; }
    }

    /* Locked Node Colors */
    .node-locked .node-bubble {
        background-color: #F9FAFB !important;
        border-color: #E5E7EB !important;
        color: #9CA3AF !important;
    }
    .node-locked .node-label { color: #9CA3AF !important; }
    .node-locked .node-status { color: #9CA3AF !important; }
    .line-locked { background-color: #E5E7EB !important; }

    /* Mascot Speech Bubble Styling */
    .mascot-container {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 20px 0 !important;
    }
    .mascot-bubble {
        background-color: #FFFFFF !important;
        border: 3px solid #FFE4E6 !important;
        border-radius: 20px 20px 20px 0px !important;
        padding: 12px 20px !important;
        font-weight: bold !important;
        color: var(--text-color) !important;
        box-shadow: 0px 4px 0px rgba(0,0,0,0.03) !important;
        font-size: 1.05rem !important;
        position: relative !important;
        max-width: 450px !important;
    }

    /* Play Bank Progress Bar Styling */
    .play-bank-bar-container {
        background-color: #E2E8F0 !important;
        border-radius: 10px !important;
        height: 10px !important;
        width: 80% !important;
        margin: 8px auto 0 auto !important;
        overflow: hidden !important;
        border: 1px solid #CBD5E1 !important;
    }
    .play-bank-bar-fill {
        background-color: #10B981 !important;
        height: 100% !important;
        border-radius: 10px !important;
        transition: width 0.5s ease !important;
    }

    /* Morning Bonus Card Styling */
    .morning-bonus-card {
        background-color: #FFFFFF !important;
        border: 4px dashed #FCD34D !important;
        border-radius: 24px !important;
        padding: 20px !important;
        text-align: center !important;
        max-width: 400px !important;
        margin: 20px auto !important;
        box-shadow: 0px 5px 0px rgba(253, 211, 77, 0.15) !important;
    }
    .bonus-claimed-badge {
        background-color: #ECFDF5 !important;
        color: #059669 !important;
        border: 2px solid #34D399 !important;
        border-radius: 12px !important;
        padding: 4px 12px !important;
        font-family: 'Fredoka One', sans-serif !important;
        font-size: 0.9rem !important;
        display: inline-block !important;
        margin-top: 5px !important;
    }

    /* Celebration Card Styling */
    .celebration-card {
        background-color: #FFFFFF !important;
        border: 4px solid #10B981 !important;
        border-radius: 35px !important;
        padding: 30px !important;
        text-align: center !important;
        box-shadow: 0px 10px 0px rgba(16, 185, 129, 0.1) !important;
        margin-bottom: 25px !important;
        animation: popCelebration 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }
    @keyframes popCelebration {
        0% { transform: scale(0.8); opacity: 0; }
        100% { transform: scale(1); opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# Dynamically load and inject background image asset if it exists
bg_img_path = "assets/math_background.png"
if os.path.exists(bg_img_path):
    try:
        bg_base64 = get_base64_of_bin_file(bg_img_path)
        st.markdown(f"""
        <style>
            .stApp::before {{
                content: "" !important;
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100% !important;
                height: 100% !important;
                background-image: url("data:image/png;base64,{bg_base64}") !important;
                background-size: 320px !important;
                background-repeat: repeat !important;
                opacity: 0.03 !important; /* Low opacity watermark effect */
                z-index: -1 !important;
                pointer-events: none !important;
            }}
        </style>
        """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error loading background image: {str(e)}", exc_info=True)


def init_session_state():
    if "current_actual_quiz" not in st.session_state:
        st.session_state.current_actual_quiz = None
    if "last_actual_result" not in st.session_state:
        st.session_state.last_actual_result = None
    if "current_practice_quiz" not in st.session_state:
        st.session_state.current_practice_quiz = None
    if "last_practice_result" not in st.session_state:
        st.session_state.last_practice_result = None
    if "activation_status" not in st.session_state:
        st.session_state.activation_status = None
    if "show_celebration" not in st.session_state:
        st.session_state.show_celebration = False


import threading
import time

def main():
    init_session_state()

    # Inject background floating blobs (Nudot design)
    st.markdown('<div class="blob blob-1"></div><div class="blob blob-2"></div><div class="blob blob-3"></div>', unsafe_allow_html=True)

    # Load system state (applies 9 AM day rollover if needed)
    state = get_current_system_state()
    current_level = state.get("current_level", 1)
    current_test = state.get("current_test_in_level", 1)
    level_info = get_level_info(current_level)
    banked_minutes = state.get("minutes_banked", 0)
    sessions_today = state.get("sessions_today", 0)
    unlocked_until_str = state.get("unlocked_until")
    total_stars = state.get("total_stars", 120)
    streak = state.get("streak", 3)





    # Tabs Setup
    tab_dashboard, tab_actual, tab_practice = st.tabs([
        "🏠 MATH SPACE",
        "🗺️ MISSION MAP",
        "✏️ PRACTICE"
    ])

    # ==================== TAB 1: MATH SPACE DASHBOARD ====================
    with tab_dashboard:
        # Dashboard header (no parental lockouts or screen time limits)
        st.markdown(
            '<div style="text-align: center; font-family: \'Fredoka One\', sans-serif; font-size: 1.8rem; color: var(--primary-color); margin-bottom: 20px; margin-top: 10px;">'
            '✨ WELCOME TO YOUR MATH SPACE! ✨<br>'
            '<span style="font-size: 1.2rem; color: var(--text-color); opacity: 0.8; font-weight: bold;">Earn play minutes and stars by completing missions! 🚀</span>'
            '</div>',
            unsafe_allow_html=True
        )

        # Show celebration card if requested
        if st.session_state.get("show_celebration", False):
            st.balloons()
            st.markdown(
                f"""
                <div class="celebration-card">
                    <div style="font-size: 2.2rem; font-family: 'Fredoka One', sans-serif; color: #10B981; margin-bottom: 10px;">🎉 EXCELLENT PERFORMANCE! 🎉</div>
                    <div style="font-size: 1.5rem; font-weight: 800; color: #F59E0B; margin-bottom: 8px;">⭐ Total Stars: {total_stars}</div>
                    <div style="font-size: 1.5rem; font-weight: 800; color: #10B981; margin-bottom: 15px;">🎮 Total Play Minutes: {banked_minutes}</div>
                    <div style="font-size: 1.15rem; font-weight: bold; color: var(--text-color); opacity: 0.85; margin-bottom: 15px;">
                        Show this screen to your parent to physically redeem your screen time! 🎈
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
            if st.button("📧 Send Daily Parent Email Digest Now", key="celebration_send_digest_btn", use_container_width=True):
                with st.spinner("Compiling and sending daily report..."):
                    report_res = run_daily_reporting_agent()
                    if report_res.get("sent_via_resend"):
                        st.success(f"Report emailed to {report_res.get('recipient')}!")
                    else:
                        st.info(f"Report saved locally to:\n`{report_res.get('local_file')}`")

            if st.button("Close Celebration ❌", key="close_celebration_btn", use_container_width=True):
                st.session_state.show_celebration = False
                st.rerun()

        # Stats Cards Grid
        col_lv, col_bk, col_se = st.columns(3)
        with col_lv:
            st.markdown(
                f'<div class="stat-card">'
                f'<div class="stat-label" style="font-size: 0.9rem; font-weight: bold; opacity: 0.85; text-transform: uppercase;">🏆 Level</div>'
                f'<div class="stat-number" style="font-size: 2.1rem; margin: 5px 0;">Level {current_level}</div>'
                f'<div class="stat-label" style="font-size: 0.85rem; opacity: 0.7;">{level_info["grade_focus"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        with col_bk:
            bar_fill_width = min(100, banked_minutes * 5)
            st.markdown(
                f'<div class="stat-card">'
                f'<div class="stat-label" style="font-size: 0.9rem; font-weight: bold; opacity: 0.85; text-transform: uppercase;">🎮 Play Bank</div>'
                f'<div class="stat-number" style="font-size: 2.1rem; margin: 5px 0;">{banked_minutes} min</div>'
                f'<div class="play-bank-bar-container">'
                f'<div class="play-bank-bar-fill" style="width: {bar_fill_width}%;"></div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            # Large Celebrate My Rewards! button on the Dashboard Play Bank card
            if st.button("Celebrate My Rewards! 🎈", key="celebrate_my_rewards_btn", use_container_width=True):
                st.session_state.show_celebration = True
                st.rerun()

        with col_se:
            st.markdown(
                f'<div class="stat-card">'
                f'<div class="stat-label" style="font-size: 0.9rem; font-weight: bold; opacity: 0.85; text-transform: uppercase;">⭐ Stars</div>'
                f'<div class="stat-number" style="font-size: 2.1rem; margin: 5px 0;">{total_stars}</div>'
                f'<div class="stat-label" style="font-size: 0.85rem; opacity: 0.8; color: #EF4444; font-weight: bold;">🔥 {streak} Day Streak!</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        if st.session_state.activation_status:
            st.success(st.session_state.activation_status)

        # Morning Battery Bonus Notification
        if state.get("morning_battery_bonus_claimed"):
            st.markdown(
                f'<div class="morning-bonus-card">'
                f'<div style="font-size: 1.4rem; font-family: \'Fredoka One\', sans-serif; color: #D97706; margin-bottom: 5px;">☀️ MORNING BONUS!</div>'
                f'<div style="font-size: 1.15rem; font-weight: 800; color: #10B981; margin-bottom: 5px;">+5 PLAY MINUTES</div>'
                f'<div class="bonus-claimed-badge">✓ CLAIMED!</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        # Visual Progression Tracker: Connected Quest / Level-up Journey
        quest_html = (
            f'<div class="quest-container">'
            f'<div class="quest-title">🏆 LEVEL-UP JOURNEY</div>'
            f'<div class="quest-subtitle">Level {current_level} ───★─── Level {current_level + 1}</div>'
            f'<div class="quest-map">'
        )
        for i in range(1, 5):
            is_final = (i == 4)
            label = "Final Mission" if is_final else f"Mission {i}"
            
            if i < current_test:
                # Passed
                quest_html += (
                    f'<div class="quest-node node-passed">'
                    f'<div class="node-bubble">⭐</div>'
                    f'<div class="node-label">{label}</div>'
                    f'<div class="node-status">✓ DONE</div>'
                    f'</div>'
                )
            elif i == current_test:
                # Current/Active
                icon = "🚀" if is_final else "⭐"
                quest_html += (
                    f'<div class="quest-node node-current">'
                    f'<div class="node-bubble">{icon}</div>'
                    f'<div class="node-label">{label}</div>'
                    f'<div class="node-status">ACTIVE</div>'
                    f'</div>'
                )
            else:
                # Locked
                quest_html += (
                    f'<div class="quest-node node-locked">'
                    f'<div class="node-bubble">🔒</div>'
                    f'<div class="node-label">{label}</div>'
                    f'<div class="node-status">LOCKED</div>'
                    f'</div>'
                )
            
            # Draw line between nodes
            if i < 4:
                if i < current_test:
                    line_class = "line-passed"
                elif i == current_test - 1:
                    line_class = "line-active"
                else:
                    line_class = "line-locked"
                quest_html += f'<div class="quest-line {line_class}"></div>'
                
        # Close the map
        missions_completed = current_test - 1
        encouragement = "You're SO close!" if missions_completed == 3 else "Keep going, you got this!"
        quest_html += (
            f'</div>'
            f'<div style="font-size: 1.25rem; font-weight: 800; color: var(--primary-color); margin-top: 15px;">'
            f'⭐ {missions_completed} / 4 MISSIONS COMPLETE'
            f'</div>'
            f'<div style="font-size: 1.05rem; font-weight: bold; color: var(--text-color); opacity: 0.8; margin-top: 5px;">'
            f'"{encouragement}"'
            f'</div>'
            f'</div>'
        )
        st.markdown(quest_html, unsafe_allow_html=True)

        # Mascot and CTA Section
        mascot_text = ""
        if missions_completed == 3:
            mascot_text = "🤖 \"You're SO close! Only ONE mission left to level up to Level {}! Let's do this! 🚀\"".format(current_level + 1)
        elif missions_completed > 0:
            mascot_text = "🤖 \"Awesome! {} of 4 missions complete! Complete the next mission to level up! 🌟\"".format(missions_completed)
        else:
            mascot_text = "🤖 \"Hey there! I'm Digit. Complete your first mission to start earning play minutes and stars! Let's do this! 💪\""

        st.markdown(
            f'<div class="mascot-container">'
            f'<div class="mascot-bubble">{mascot_text}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Session State for rendering quiz directly on Dashboard
        if "dashboard_quiz_active" not in st.session_state:
            st.session_state.dashboard_quiz_active = False

        if not st.session_state.dashboard_quiz_active:
            # Obvious next action button
            btn_label = "🚀 START FINAL MISSION" if current_test == 4 else f"🚀 START MISSION {current_test}"
            st.write("")
            if st.button(btn_label, type="primary", use_container_width=True, key="dashboard_start_mission_btn"):
                st.session_state.dashboard_quiz_active = True
                st.rerun()
            st.write("")
        else:
                # Render the active mission quiz directly inside the Dashboard!
                st.write("")
                st.markdown('<div class="quest-container" style="text-align: left; padding: 25px;">', unsafe_allow_html=True)
                st.subheader(f"⚡ Level {current_level} - Mission {current_test} of 4")
                st.caption(f"Topic: {level_info['name']} — {level_info['description']}")
                st.write("Complete all 10 questions. A **perfect 10/10 (100% correct)** is required to earn play minutes and progress!")

                # Generate / retrieve quiz (reuse key st.session_state.current_actual_quiz)
                if st.session_state.current_actual_quiz is None:
                    st.session_state.current_actual_quiz = generate_new_quiz(current_level, is_practice=False)

                quiz = st.session_state.current_actual_quiz

                with st.form("dashboard_quiz_form"):
                    student_answers = {}
                    for q in quiz["questions"]:
                        clean_q = q['question'].rstrip("?=\t ")
                        q_col, a_col = st.columns([3, 2])
                        with q_col:
                            st.markdown(
                                f'<div class="question-card" style="margin-bottom: 15px; padding: 0px 18px; height: 58px; display: flex; align-items: center;">'
                                f'<div class="question-text" style="font-size: 1.4rem;">Q{q["id"]}. &nbsp; {clean_q} = ?</div>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        with a_col:
                            ans_str = st.text_input(
                                label=f"Answer for Q{q['id']}",
                                key=f"dash_q_input_{q['id']}",
                                placeholder="Enter answer",
                                label_visibility="collapsed"
                            )
                        student_answers[q['id']] = ans_str

                    st.write("")
                    col_submit, col_cancel = st.columns([2, 1])
                    with col_submit:
                        submitted = st.form_submit_button("Submit Mission Answers 🚀", type="primary", use_container_width=True)
                    with col_cancel:
                        # cancel button inside form
                        cancelled = st.form_submit_button("🏠 Cancel & Go Back", use_container_width=True)

                    if submitted:
                        with st.spinner("Grading your mission answers..."):
                            result = grade_and_process_submission(student_answers, quiz, is_practice=False)
                            st.session_state.last_actual_result = result
                            st.session_state.current_actual_quiz = None
                            st.session_state.dashboard_quiz_active = False
                            st.rerun()
                    elif cancelled:
                        st.session_state.current_actual_quiz = None
                        st.session_state.dashboard_quiz_active = False
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # ==================== TAB 2: MISSION MAP ====================
    with tab_actual:
        st.subheader(f"🗺️ Level {current_level} Mission ({current_test} of 4)")
        st.caption(f"Topic: {level_info['name']} — {level_info['description']}")
        
        # Display Result if just completed
        if st.session_state.last_actual_result:
            res = st.session_state.last_actual_result
            st.subheader("🎉 Mission Summary & Results")

            if res["score"] == 10:
                st.balloons()
                if res["level_up_occurred"]:
                    msg = f"🌟 YOU LEVELED UP TO LEVEL {res['current_level']}! 🌟"
                else:
                    msg = f"🎉 Mission {current_test - 1 if current_test > 1 else 4} of 4 complete!"
                st.markdown(f"""
                <div class="celebration-card">
                    <div style="font-size: 2.2rem; font-family: 'Fredoka One', sans-serif; color: #10B981; margin-bottom: 10px;">🎉 MISSION COMPLETE!</div>
                    <div style="font-size: 1.3rem; font-weight: 800; color: #F59E0B; margin-bottom: 8px;">⭐ +20 Stars Earned</div>
                    <div style="font-size: 1.3rem; font-weight: 800; color: #10B981; margin-bottom: 15px;">🎮 +{res['earned_minutes']} Play Minutes</div>
                    <div style="font-size: 1.15rem; font-weight: bold; color: var(--text-color); opacity: 0.85;">
                        {msg}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.write("")
            else:
                st.warning(f"You scored {res['score']}/10. A strict 10/10 (100% correct) is required to earn minutes and progress. Keep trying!")

            st.markdown(f"**Total Banked Minutes in Play Bank:** `{res['total_minutes_banked']} minutes`")
            
            # Action Buttons
            act_col1, act_col2 = st.columns(2)
            with act_col1:
                if st.button("🚀 Take Next Mission", type="primary", use_container_width=True, key="next_act_quiz_btn"):
                    st.session_state.last_actual_result = None
                    st.session_state.current_actual_quiz = None
                    st.rerun()
            with act_col2:
                if st.button("🏠 Go to Dashboard", use_container_width=True, key="dashboard_act_btn"):
                    st.session_state.last_actual_result = None
                    st.rerun()

            st.write("")
            with st.expander("Inspect Detailed Question Review"):
                for q_res in res["question_results"]:
                    icon = "✅" if q_res["is_correct"] else "❌"
                    st.write(f"{icon} **Q{q_res['id']}:** {q_res['question']} = **{q_res['expected']}** | Your answer: `{q_res['user_input']}`")

        else:
            # Generate / retrieve quiz
            if st.session_state.current_actual_quiz is None:
                st.session_state.current_actual_quiz = generate_new_quiz(current_level, is_practice=False)

            quiz = st.session_state.current_actual_quiz
            reward_label = f"{5 * current_level} minutes"
            st.caption(f"Answer all 10 questions. A **strict 10/10 (100%)** is required to earn {reward_label}!")

            with st.form("actual_quiz_form"):
                student_answers = {}
                for q in quiz["questions"]:
                    clean_q = q['question'].rstrip("?=\t ")
                    q_col, a_col = st.columns([3, 2])
                    with q_col:
                        st.markdown(
                            f'<div class="question-card" style="margin-bottom: 15px; padding: 0px 18px; height: 58px; display: flex; align-items: center;">'
                            f'<div class="question-text" style="font-size: 1.4rem;">Q{q["id"]}. &nbsp; {clean_q} = ?</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    with a_col:
                        ans_str = st.text_input(
                            label=f"Answer for Q{q['id']}",
                            key=f"actual_q_input_{q['id']}",
                            placeholder="Enter answer",
                            label_visibility="collapsed"
                        )
                    student_answers[q['id']] = ans_str

                st.write("")
                submitted = st.form_submit_button("Submit Mission Answers 🚀", type="primary", use_container_width=True)

                if submitted:
                    with st.spinner("Grading your mission answers..."):
                        result = grade_and_process_submission(student_answers, quiz, is_practice=False)
                        st.session_state.last_actual_result = result
                        st.session_state.current_actual_quiz = None
                        st.rerun()

    # ==================== TAB 3: PRACTICE ARENA ====================
    with tab_practice:
        st.subheader("✏️ Practice Area")
        st.caption("Practice here to master the concepts! Complete actual missions on the Dashboard or Mission Map to earn rewards.")

        selected_practice_level = st.selectbox(
            "Select Practice Level:",
            options=list(range(1, 6)),
            format_func=lambda x: get_level_info(x)['name']
        )

        # Clear quiz if practice level changed
        if st.session_state.current_practice_quiz:
            if st.session_state.current_practice_quiz.get("level") != selected_practice_level:
                st.session_state.current_practice_quiz = None

        # Display Result if just completed
        if st.session_state.last_practice_result:
            res = st.session_state.last_practice_result
            st.subheader("🎉 Practice Mission Summary")

            if res["score"] == 10:
                st.balloons()
                st.markdown(f"""
                <div class="celebration-card">
                    <div style="font-size: 2.2rem; font-family: 'Fredoka One', sans-serif; color: #10B981; margin-bottom: 10px;">🎉 PRACTICE COMPLETE!</div>
                    <div style="font-size: 1.3rem; font-weight: 800; color: #F59E0B; margin-bottom: 8px;">⭐ +{res.get('stars_earned', 0)} Stars Earned (Practice)</div>
                    <div style="font-size: 1.3rem; font-weight: 800; color: #10B981; margin-bottom: 15px;">🎮 +{res.get('earned_minutes', 0)} Play Minutes (Practice)</div>
                    <div style="font-size: 1.15rem; font-weight: bold; color: var(--text-color); opacity: 0.85;">
                        Keep practicing to get even stronger!
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.write("")
            else:
                st.warning(f"You scored {res['score']}/10. Keep practicing to master this level! Remember, complete actual missions to earn rewards.")

            st.markdown(f"**Total Banked Minutes in Play Bank:** `{res['total_minutes_banked']} minutes`")
            
            if st.button("🚀 Take Another Practice Mission", type="primary", use_container_width=True, key="next_prac_quiz_btn"):
                st.session_state.last_practice_result = None
                st.session_state.current_practice_quiz = None
                st.rerun()

            st.write("")
            with st.expander("Inspect Detailed Question Review"):
                for q_res in res["question_results"]:
                    icon = "✅" if q_res["is_correct"] else "❌"
                    st.write(f"{icon} **Q{q_res['id']}:** {q_res['question']} = **{q_res['expected']}** | Your answer: `{q_res['user_input']}`")

        else:
            # Generate / retrieve quiz
            if st.session_state.current_practice_quiz is None:
                st.session_state.current_practice_quiz = generate_new_quiz(selected_practice_level, is_practice=True)

            quiz = st.session_state.current_practice_quiz
            st.caption("Practice here to sharpen your math skills! (Practice awards 0 play minutes and 0 stars, so go complete actual missions to earn rewards!)")

            with st.form("practice_quiz_form"):
                student_answers = {}
                for q in quiz["questions"]:
                    clean_q = q['question'].rstrip("?=\t ")
                    q_col, a_col = st.columns([3, 2])
                    with q_col:
                        st.markdown(
                            f'<div class="question-card" style="margin-bottom: 15px; padding: 0px 18px; height: 58px; display: flex; align-items: center;">'
                            f'<div class="question-text" style="font-size: 1.4rem;">Q{q["id"]}. &nbsp; {clean_q} = ?</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    with a_col:
                        ans_str = st.text_input(
                            label=f"Answer for Q{q['id']}",
                            key=f"practice_q_input_{q['id']}",
                            placeholder="Enter answer",
                            label_visibility="collapsed"
                        )
                    student_answers[q['id']] = ans_str

                st.write("")
                submitted = st.form_submit_button("Submit Mission Answers 🚀", type="primary", use_container_width=True)

                if submitted:
                    with st.spinner("Grading your mission answers..."):
                        result = grade_and_process_submission(student_answers, quiz, is_practice=True)
                        st.session_state.last_practice_result = result
                        st.session_state.current_practice_quiz = None
                        st.rerun()


if __name__ == "__main__":
    main()
