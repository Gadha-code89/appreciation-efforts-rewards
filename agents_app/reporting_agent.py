"""
agents_app/reporting_agent.py - Parent Daily Email Digest Generator Agent
"""

import os
from datetime import datetime
from typing import Dict, Any

from core.state import load_state
from core.telemetry import get_mock_usage_telemetry, get_mock_battery_telemetry
from core.email_client import send_daily_email
from core.levels import get_level_info


def generate_html_digest(state: Dict[str, Any], usage_data: Dict[str, Any], battery_data: Dict[str, Any]) -> str:
    """
    Build rich HTML body for parent daily report.
    """
    effective_date = state.get("effective_date", datetime.now().strftime("%Y-%m-%d"))
    current_level = state.get("current_level", 1)
    level_info = get_level_info(current_level)
    sessions_today = state.get("sessions_today", 0)
    minutes_banked = state.get("minutes_banked", 0)
    history = state.get("history", [])

    # Calculate total questions and correct answers today
    total_correct = sum(h.get("correct", 0) for h in history)
    total_questions = sum(h.get("total", 0) for h in history)
    overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0.0

    # API Telemetry Status
    openai_ok = bool(os.getenv("OPENAI_API_KEY"))
    resend_ok = bool(os.getenv("RESEND_API_KEY"))

    # Games vs Video App Usage Breakdown
    games = usage_data.get("categories", {}).get("Games", {})
    video = usage_data.get("categories", {}).get("Video", {})

    games_apps_html = "".join([f"<li><b>{app}:</b> {mins} mins</li>" for app, mins in games.get("apps", {}).items()])
    video_apps_html = "".join([f"<li><b>{app}:</b> {mins} mins</li>" for app, mins in video.get("apps", {}).items()])

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
        .header {{ border-bottom: 2px solid #4F46E5; padding-bottom: 15px; margin-bottom: 20px; }}
        .header h2 {{ color: #4F46E5; margin: 0; font-size: 24px; }}
        .header p {{ color: #6B7280; margin: 5px 0 0 0; font-size: 14px; }}
        .card {{ background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 8px; padding: 15px; margin-bottom: 15px; }}
        .card h3 {{ margin-top: 0; color: #1F2937; font-size: 16px; border-bottom: 1px solid #E5E7EB; padding-bottom: 8px; }}
        .stat-grid {{ display: flex; gap: 10px; margin-bottom: 10px; }}
        .stat-box {{ background: #EEF2FF; border-radius: 6px; padding: 10px; flex: 1; text-align: center; }}
        .stat-value {{ font-size: 20px; font-weight: bold; color: #4F46E5; }}
        .stat-label {{ font-size: 12px; color: #4B5563; }}
        .status-badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .badge-success {{ background: #DEF7EC; color: #03543F; }}
        .badge-warning {{ background: #FEF08A; color: #713F12; }}
        ul {{ margin: 5px 0 0 0; padding-left: 20px; color: #4B5563; }}
        .footer {{ font-size: 12px; color: #9CA3AF; text-align: center; margin-top: 20px; border-top: 1px solid #E5E7EB; padding-top: 15px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h2>Appreciation of Efforts Math Report</h2>
          <p>Date: {effective_date} (9:00 AM Operating Day Cycle)</p>
        </div>

        <!-- Math Performance Card -->
        <div class="card">
          <h3>Math Practice Summary</h3>
          <p><b>Current Level:</b> {level_info['name']}</p>
          <div class="stat-grid">
            <div class="stat-box">
              <div class="stat-value">{sessions_today}</div>
              <div class="stat-label">Quizzes Taken</div>
            </div>
            <div class="stat-box">
              <div class="stat-value">{total_correct}/{total_questions}</div>
              <div class="stat-label">Questions Correct</div>
            </div>
            <div class="stat-box">
              <div class="stat-value">{round(overall_accuracy, 1)}%</div>
              <div class="stat-label">Overall Accuracy</div>
            </div>
          </div>
          <p><b>Total Banked Screen Time Earned Today:</b> <span style="color:#4F46E5; font-weight:bold;">{minutes_banked} minutes</span></p>
        </div>

        <!-- App Usage Telemetry Card -->
        <div class="card">
          <h3>Screen Time Telemetry (Games & Video)</h3>
          <p><b>Games ({games.get('total_minutes', 0)} mins total):</b></p>
          <ul>{games_apps_html}</ul>
          <p><b>Video ({video.get('total_minutes', 0)} mins total):</b></p>
          <ul>{video_apps_html}</ul>
        </div>

        <!-- Battery Status Card -->
        <div class="card">
          <h3>Morning Battery Charge Check</h3>
          <p><b>iPad Battery Status:</b> {battery_data.get('charge_percent', 0)}% charged</p>
          <p><b>Morning Bonus Status:</b> 
            {"<span class='status-badge badge-success'>+5 Bonus Minutes Claimed</span>" if state.get("morning_battery_bonus_claimed") else "<span class='status-badge badge-warning'>No Morning Bonus (<50% Charge)</span>"}
          </p>
        </div>

        <!-- System & API Telemetry Card -->
        <div class="card">
          <h3>System & API Key Telemetry</h3>
          <p><b>OpenAI API Status:</b> {"<span class='status-badge badge-success'>Connected (gpt-4o-mini)</span>" if openai_ok else "<span class='status-badge badge-warning'>Unconfigured (Using Fallback Engine)</span>"}</p>
          <p><b>Resend API Status:</b> {"<span class='status-badge badge-success'>Active</span>" if resend_ok else "<span class='status-badge badge-warning'>Unconfigured (Logged to Local File)</span>"}</p>
        </div>

        <div class="footer">
          Appreciation of Efforts Math App &bull; Generated Automatically at 9:00 AM
        </div>
      </div>
    </body>
    </html>
    """
    return html


def run_daily_reporting_agent() -> Dict[str, Any]:
    """
    Execute daily reporting pipeline:
    1. Read state & telemetry.
    2. Render HTML email body.
    3. Send via Resend or save locally to reports/ directory.
    """
    state = load_state()
    usage = get_mock_usage_telemetry()
    battery = get_mock_battery_telemetry()

    effective_date = state.get("effective_date", datetime.now().strftime("%Y-%m-%d"))
    subject = f"Appreciation of Efforts Math Report — {effective_date}"

    html_body = generate_html_digest(state, usage, battery)
    result = send_daily_email(subject, html_body, effective_date)

    return result
