"""
core/telemetry.py - Mocked Device Telemetry (Battery & App Usage)
"""

import random
from typing import Dict, Any


def get_mock_battery_telemetry() -> Dict[str, Any]:
    """
    Simulate device battery status telemetry.
    Defaults to realistic high charge state (e.g. 85%) for testing.
    """
    return {
        "charge_percent": 85,
        "is_charging": True,
        "device_type": "iPad (Simulated)",
        "battery_health": "Good"
    }


def get_mock_usage_telemetry() -> Dict[str, Any]:
    """
    Simulate per-app usage minutes for Games and Video categories.
    (Learning apps explicitly excluded per design requirements).
    """
    # Realistic usage distribution for demo digest
    return {
        "categories": {
            "Games": {
                "total_minutes": 45,
                "apps": {
                    "Roblox": 25,
                    "Minecraft": 15,
                    "Boddle": 5
                }
            },
            "Video": {
                "total_minutes": 35,
                "apps": {
                    "YouTube": 20,
                    "Disney+": 10,
                    "Netflix": 5
                }
            }
        },
        "total_screen_time_minutes": 80
    }
