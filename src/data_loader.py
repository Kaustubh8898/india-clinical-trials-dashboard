"""
Data loading module for India Clinical Trials Intelligence Dashboard.
Handles loading, validation, and caching of cleaned clinical trial data.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.config import PROCESSED_DATA_DIR

# ============================================================================
# CONSTANTS
# ============================================================================

CLEANED_DATA_FILE = PROCESSED_DATA_DIR / "india_trials_clean.csv"
EXPECTED_COLUMNS = {
    'nct_id', 'brief_title', 'sponsor', 'phase', 'conditions',
    'recruitment_status', 'start_date', 'completion_date', 'enrollment_count',
    'city', 'state', 'country', 'fetched_date', 'therapeutic_area',
    'trial_duration_days', 'india_only_trial'
}


# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_clinical_trials_data() -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
    """
    Load cleaned clinical trials data from CSV file.
    
    Returns:
        Tuple containing:
        - DataFrame with trial data (or None if error)
        - Dict with metadata (file_exists, is_empty, columns_valid, error, last_modified, record_count, last_updated_timestamp)
    """
    metadata = {
        "file_exists": False,
        "is_empty": False,
        "columns_valid": False,
        "error": None,
        "last_modified": None,
        "record_count": 0,
        "last_updated_timestamp": None
    }
    
    try:
        # Check file existence
        if not CLEANED_DATA_FILE.exists():
            metadata["error"] = f"Data file not found: {CLEANED_DATA_FILE}"
            logger.error(metadata["error"])
            return None, metadata
        
        metadata["file_exists"] = True
        
        # Get file modification time
        file_stat = CLEANED_DATA_FILE.stat()
        metadata["last_modified"] = datetime.fromtimestamp(file_stat.st_mtime)
        metadata["last_updated_timestamp"] = metadata["last_modified"].strftime("%Y-%m-%d %H:%M:%S")
        
        # Load CSV file
        logger.info(f"Loading clinical trials data from {CLEANED_DATA_FILE}")
        df = pd.read_csv(CLEANED_DATA_FILE)
        
        # Check if empty
        if len(df) == 0:
            metadata["is_empty"] = True
            metadata["error"] = "Data file is empty"
            logger.warning(metadata["error"])
            return df, metadata
        
        # Validate columns
        loaded_columns = set(df.columns)
        if not EXPECTED_COLUMNS.issubset(loaded_columns):
            missing_cols = EXPECTED_COLUMNS - loaded_columns
            metadata["error"] = f"Missing required columns: {missing_cols}"
            logger.error(metadata["error"])
            return None, metadata
        
        metadata["columns_valid"] = True
        metadata["record_count"] = len(df)
        
        # Parse date columns
        df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
        df["completion_date"] = pd.to_datetime(df["completion_date"], errors="coerce")
        
        # Create year columns for filtering
        df["start_year"] = df["start_date"].dt.year
        df["completion_year"] = df["completion_date"].dt.year
        
        logger.info(f"Successfully loaded {len(df)} clinical trial records")
        return df, metadata
        
    except Exception as e:
        metadata["error"] = f"Error loading data: {str(e)}"
        logger.error(metadata["error"])
        return None, metadata


def get_unique_values(df: pd.DataFrame, column: str) -> list:
    """Get sorted unique values from a column, excluding NaN."""
    if df is None or column not in df.columns:
        return []
    return sorted(df[column].dropna().unique().tolist())


def get_data_summary(df: pd.DataFrame, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate summary statistics for the dataset.
    
    Args:
        df: Clinical trials DataFrame
        metadata: File metadata dictionary
        
    Returns:
        Dictionary with summary statistics
    """
    if df is None or len(df) == 0:
        return {
            "total_trials": 0,
            "recruiting_trials": 0,
            "active_trials": 0,
            "completed_trials": 0,
            "total_sponsors": 0,
            "total_areas": 0,
            "total_states": 0,
            "total_cities": 0,
            "avg_duration_days": 0,
            "total_enrollment": 0,
            "top_sponsor": "N/A",
            "top_area": "N/A",
            "most_active_area": "N/A",
            "top_state": "N/A"
        }
    
    recruiting = (df["recruitment_status"] == "Recruiting").sum()
    active = (df["recruitment_status"].isin(["Recruiting", "Active, not recruiting"])).sum()
    completed = (df["recruitment_status"] == "Completed").sum()
    
    top_area = df["therapeutic_area"].value_counts().index[0] if len(df) > 0 else "N/A"
    
    return {
        "total_trials": len(df),
        "recruiting_trials": recruiting,
        "active_trials": active,
        "completed_trials": completed,
        "total_sponsors": df["sponsor"].nunique(),
        "total_areas": df["therapeutic_area"].nunique(),
        "total_states": df["state"].nunique(),
        "total_cities": df["city"].nunique(),
        "avg_duration_days": int(df["trial_duration_days"].mean()) if "trial_duration_days" in df.columns else 0,
        "total_enrollment": int(df["enrollment_count"].sum()) if "enrollment_count" in df.columns else 0,
        "top_sponsor": df["sponsor"].value_counts().index[0] if len(df) > 0 else "N/A",
        "top_area": top_area,
        "most_active_area": top_area,
        "top_state": df["state"].value_counts().index[0] if len(df) > 0 else "N/A"
    }


def apply_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """
    Apply user-selected filters to the dataset.
    
    Args:
        df: Clinical trials DataFrame
        filters: Dictionary with filter specifications
        
    Returns:
        Filtered DataFrame
    """
    if df is None or len(df) == 0:
        return df
    
    filtered_df = df.copy()
    
    # Therapeutic area filter
    if filters.get("therapeutic_areas") and len(filters["therapeutic_areas"]) > 0:
        filtered_df = filtered_df[filtered_df["therapeutic_area"].isin(filters["therapeutic_areas"])]
    
    # Phase filter
    if filters.get("phases") and len(filters["phases"]) > 0:
        filtered_df = filtered_df[filtered_df["phase"].isin(filters["phases"])]
    
    # Recruitment status filter
    if filters.get("statuses") and len(filters["statuses"]) > 0:
        filtered_df = filtered_df[filtered_df["recruitment_status"].isin(filters["statuses"])]
    
    # Sponsor filter
    if filters.get("sponsor") and filters["sponsor"] != "All Sponsors":
        filtered_df = filtered_df[filtered_df["sponsor"] == filters["sponsor"]]
    
    # State filter
    if filters.get("states") and len(filters["states"]) > 0:
        filtered_df = filtered_df[filtered_df["state"].isin(filters["states"])]
    
    # Year range filter
    if filters.get("year_range"):
        start_year, end_year = filters["year_range"]
        filtered_df = filtered_df[
            (filtered_df["start_year"] >= start_year) & 
            (filtered_df["start_year"] <= end_year)
        ]
    
    return filtered_df


def validate_and_log_data(df: pd.DataFrame, metadata: Dict[str, Any]) -> bool:
    """
    Validate data quality and log issues.
    
    Args:
        df: Clinical trials DataFrame
        metadata: File metadata dictionary
        
    Returns:
        True if data is valid, False otherwise
    """
    if metadata.get("error"):
        logger.error(f"Data validation failed: {metadata['error']}")
        return False
    
    if df is None or len(df) == 0:
        logger.warning("Dataset is empty")
        return False
    
    # Check for missing critical columns
    if not metadata.get("columns_valid"):
        logger.error("Invalid column schema")
        return False
    
    # Check for excessive missing values
    missing_ratio = df.isnull().sum() / len(df)
    high_missing = missing_ratio[missing_ratio > 0.5]
    if len(high_missing) > 0:
        logger.warning(f"Columns with >50% missing values: {high_missing.to_dict()}")
    
    logger.info("Data validation passed")
    return True


# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

def clear_data_cache():
    """Clear the cached data to force a reload."""
    st.cache_data.clear()
    logger.info("Data cache cleared")


if __name__ == "__main__":
    # Test the data loader
    print("Testing data loader...")
    df, metadata = load_clinical_trials_data()
    
    if metadata.get("file_exists"):
        print(f"✓ Data loaded successfully")
        print(f"  Records: {metadata['record_count']}")
        print(f"  Last modified: {metadata['last_updated_timestamp']}")
        
        summary = get_data_summary(df, metadata)
        print(f"\nSummary Statistics:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
    else:
        print(f"✗ Error loading data: {metadata['error']}")
