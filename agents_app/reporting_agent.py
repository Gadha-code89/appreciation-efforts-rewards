"""
agents_app/reporting_agent.py - Parent Daily Email Digest Generator Agent
"""

import os
from datetime import datetime
from typing import Dict, Any

from core.state import load_state
from core.email_client import send_daily_email


def generate_html_digest(state: Dict[str, Any]) -> str:
    """
    Build rich HTML body for parent daily report.
    """
    effective_date = state.get("effective_date", datetime.now().strftime("%Y-%m-%d"))
    total_stars = state.get("total_stars", 0)
    streak = state.get("streak", 0)
    
    # List completed missions
    missions = state.get("daily_missions", [])
    completed_missions = [m for m in missions if m.get("status") == "Completed"]
    pending_missions = [m for m in missions if m.get("status") == "Pending Confirmation"]
    not_reported_missions = [m for m in missions if m.get("status") == "Not reported"]

    completed_html = "".join([f"<li><b>{m['title']}</b> - Praise: <i>{m.get('praise') or 'Great job!'}</i></li>" for m in completed_missions])
    if not completed_html:
        completed_html = "<li>No missions confirmed yet today.</li>"

    pending_html = "".join([f"<li><b>{m['title']}</b></li>" for m in pending_missions])
    if not pending_html:
        pending_html = "<li>No missions pending confirmation.</li>"

    not_reported_html = "".join([f"<li><b>{m['title']}</b></li>" for m in not_reported_missions])
    if not not_reported_html:
        not_reported_html = "<li>No remaining missions.</li>"

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
        ul {{ margin: 5px 0 0 0; padding-left: 20px; color: #4B5563; }}
        .footer {{ font-size: 12px; color: #9CA3AF; text-align: center; margin-top: 20px; border-top: 1px solid #E5E7EB; padding-top: 15px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h2>Appreciation of Efforts Personal Growth Report</h2>
          <p>Date: {effective_date}</p>
        </div>

        <!-- Overall Progress Card -->
        <div class="card">
          <h3>Current Progress Summary</h3>
          <div class="stat-grid">
            <div class="stat-box">
              <div class="stat-value">{streak} Days</div>
              <div class="stat-label">Current Streak</div>
            </div>
            <div class="stat-box">
              <div class="stat-value">{total_stars}</div>
              <div class="stat-label">Total Stars Earned</div>
            </div>
          </div>
        </div>

        <!-- Completed Missions Card -->
        <div class="card">
          <h3>Today's Accomplishments (Confirmed)</h3>
          <ul>{completed_html}</ul>
        </div>

        <!-- Pending Confirmation Card -->
        <div class="card">
          <h3>Pending Parent Confirmation</h3>
          <ul>{pending_html}</ul>
        </div>

        <!-- Remaining Missions Card -->
        <div class="card">
          <h3>Missions Not Yet Reported</h3>
          <ul>{not_reported_html}</ul>
        </div>

        <div class="footer">
          Appreciation of Efforts App &bull; Generated for Parents
        </div>
      </div>
    </body>
    </html>
    """
    return html


def run_daily_reporting_agent() -> Dict[str, Any]:
    """
    Execute daily reporting pipeline.
    """
    state = load_state()
    effective_date = state.get("effective_date", datetime.now().strftime("%Y-%m-%d"))
    subject = f"Appreciation of Efforts Personal Growth Report — {effective_date}"

    html_body = generate_html_digest(state)
    result = send_daily_email(subject, html_body, effective_date)

    return result
