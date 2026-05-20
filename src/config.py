"""
Configuration module for the India Clinical Trials Intelligence Dashboard.
Store all reusable constants, paths, and settings here.
"""

from pathlib import Path
from typing import Final

# ============================================================================
# APP CONFIGURATION
# ============================================================================

APP_TITLE: Final[str] = "India Clinical Trials Intelligence Dashboard"
APP_ICON: Final[str] = "🏥"
APP_VERSION: Final[str] = "2.0.0"

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================

SIDEBAR_OPTIONS: Final[list[str]] = [
    "Overview Dashboard",
    "Sponsor Intelligence",
    "Therapeutic Area Analysis",
    "Geographic Analysis",
    "Trial Explorer"
]

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
RAW_DATA_DIR: Final[Path] = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Final[Path] = DATA_DIR / "processed"
LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"

# Create directories if they don't exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# API CONFIGURATION
# ============================================================================

API_BASE_URL: Final[str] = "http://localhost:8000"
API_TIMEOUT: Final[int] = 30  # seconds

# ============================================================================
# DATA PROCESSING CONFIGURATION
# ============================================================================

# Supported file formats for upload
SUPPORTED_FILE_FORMATS: Final[list[str]] = ["csv", "xlsx", "xls"]

# Default pandas read options
CSV_READ_OPTIONS: Final[dict] = {
    "dtype_backend": "numpy_nullable",
    "na_values": ["NA", "N/A", "", "null"]
}

# ============================================================================
# VISUALIZATION CONFIGURATION
# ============================================================================

PLOTLY_TEMPLATE: Final[str] = "plotly_white"
CHART_HEIGHT: Final[int] = 400
CHART_WIDTH: Final[str] = "100%"

# Color palette for charts
COLOR_PALETTE: Final[dict] = {
    "primary": "rgba(99, 110, 250, 0.8)",
    "secondary": "rgba(239, 85, 59, 0.8)",
    "success": "rgba(0, 204, 150, 0.8)",
    "warning": "rgba(255, 161, 90, 0.8)",
    "danger": "rgba(255, 102, 102, 0.8)"
}

# ============================================================================
# ANALYSIS CONFIGURATION
# ============================================================================

# Default cohort grouping column
DEFAULT_COHORT_COLUMN: Final[str] = "treatment_group"

# Statistical significance threshold
SIGNIFICANCE_LEVEL: Final[float] = 0.05

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL: Final[str] = "INFO"

# ============================================================================
# CACHE CONFIGURATION
# ============================================================================

# Streamlit cache TTL in seconds
CACHE_TTL: Final[int] = 3600  # 1 hour

# ============================================================================
# FEATURE FLAGS
# ============================================================================

ENABLE_DATA_UPLOAD: Final[bool] = True
ENABLE_ANALYTICS: Final[bool] = True
ENABLE_EXPORT: Final[bool] = True

# ============================================================================
# CLINICAL TRIAL SPECIFIC CONFIGURATION
# ============================================================================

TRIAL_PHASES: Final[list[str]] = ["Phase I", "Phase II", "Phase III", "Phase IV"]

RECRUITMENT_STATUSES: Final[list[str]] = [
    "Recruiting", "Active, not recruiting", "Enrolling by invitation",
    "Completed", "Suspended", "Terminated"
]

THERAPEUTIC_AREAS: Final[list[str]] = [
    "Oncology", "Cardiology", "Respiratory", "Infectious Disease",
    "Gastroenterology", "Neurology", "Rheumatology", "Endocrinology",
    "Immunology", "Ophthalmology", "Dermatology", "Hepatology"
]

INDIAN_STATES: Final[list[str]] = [
    "Maharashtra", "Delhi", "Karnataka", "Telangana", "Tamil Nadu",
    "West Bengal", "Gujarat", "Rajasthan", "Uttar Pradesh", "Punjab",
    "Kerala", "Haryana", "Madhya Pradesh", "Odisha"
]

# Dashboard descriptions
DASHBOARD_DESCRIPTION: Final[str] = (
    "Monitor and analyze clinical trials across India in real-time. "
    "Track sponsor activity, therapeutic areas, geographic distribution, "
    "and recruitment metrics."
)

SPONSOR_INTELLIGENCE_DESCRIPTION: Final[str] = (
    "Analyze pharmaceutical sponsors' trial portfolios, therapeutic focus, "
    "and historical trial performance."
)

THERAPEUTIC_ANALYSIS_DESCRIPTION: Final[str] = (
    "Explore trial distribution and status across different therapeutic areas "
    "to identify market trends and gaps."
)

GEOGRAPHIC_ANALYSIS_DESCRIPTION: Final[str] = (
    "Visualize clinical trial distribution across Indian states and cities. "
    "Identify key research centers and regional variations."
)

TRIAL_EXPLORER_DESCRIPTION: Final[str] = (
    "Search and filter individual clinical trials with detailed information "
    "on phases, recruitment status, and enrollment metrics."
)
