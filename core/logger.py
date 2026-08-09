"""
core/logger.py - Centralized logging module for Math-for-Minutes
"""

import logging
from pathlib import Path

LOG_FILE = Path(__file__).parent.parent / "reports" / "app.log"

def setup_logger():
    """
    Configure global logger to write to console and reports/app.log.
    """
    LOG_FILE.parent.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

# Run setup
setup_logger()

# Export a default logger name
logger = logging.getLogger("math-reward-agent")
