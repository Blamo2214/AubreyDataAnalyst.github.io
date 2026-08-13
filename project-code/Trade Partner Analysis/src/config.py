from pathlib import Path


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "output"

WORKBOOK_FILE = DATA_DIR / "Master Trade Data Tidy.xlsx"


# ---------------------------------------------------------
# Workbook sheets
# ---------------------------------------------------------

TRADE_DATA_SHEET = "Trade Data"
METRIC_METADATA_SHEET = "Metric Metadata"
COUNTRY_METADATA_SHEET = "Country Metadata"


# ---------------------------------------------------------
# Default chart settings
# ---------------------------------------------------------

DEFAULT_FRAME_DURATION = 600
DEFAULT_TRANSITION_DURATION = 300

DEFAULT_FIGURE_WIDTH = 1100
DEFAULT_FIGURE_HEIGHT = 750

DEFAULT_AXIS_PADDING = 1.10


# ---------------------------------------------------------
# Color settings
# ---------------------------------------------------------

X_PARTNER_COLOR = "#ef4444"
Y_PARTNER_COLOR = "#3b82f6"
NEUTRAL_COLOR = "#9ca3af"
MARKER_OUTLINE_COLOR = "#ffffff"