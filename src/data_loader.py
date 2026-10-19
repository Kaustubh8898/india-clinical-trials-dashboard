"""
Load, validate, and summarize the cleaned clinical-trial registry snapshot.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import pandas as pd
import streamlit as st

from src.config import PROCESSED_DATA_DIR

logger = logging.getLogger(__name__)

CLEANED_DATA_FILE = PROCESSED_DATA_DIR / "india_trials_clean.csv"
REQUIRED_COLUMNS = {
    "nct_id", "brief_title", "sponsor", "phase", "conditions",
    "recruitment_status", "start_date", "completion_date", "enrollment_count",
    "city", "state", "country", "fetched_date", "therapeutic_area",
    "trial_duration_days",
}
# Kept as a compatibility alias for scripts that imported the previous constant.
EXPECTED_COLUMNS = REQUIRED_COLUMNS | {"has_indian_location"}


def _empty_summary() -> Dict[str, Any]:
    return {
        "total_trials": 0,
        "recruiting_trials": 0,
        "active_trials": 0,
        "completed_trials": 0,
        "total_sponsors": 0,
        "active_sponsors": 0,
        "total_areas": 0,
        "total_states": 0,
        "total_cities": 0,
        "avg_duration_days": 0,
        "total_enrollment": 0,
        "top_sponsor": "N/A",
        "top_area": "N/A",
        "most_active_area": "N/A",
        "top_state": "N/A",
    }


def _derive_indian_location_flag(df: pd.DataFrame) -> pd.Series:
    """Derive presence of an Indian site; this is not an India-only flag."""
    country = (
        df["country"].astype("string").str.strip().str.casefold().eq("india")
        if "country" in df else pd.Series(False, index=df.index)
    )
    states = {
        "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
        "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
        "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya",
        "mizoram", "nagaland", "odisha", "punjab", "rajasthan", "sikkim",
        "tamil nadu", "telangana", "tripura", "uttar pradesh", "uttarakhand",
        "west bengal", "delhi", "jammu and kashmir", "ladakh",
    }
    state = (
        df["state"].astype("string").str.strip().str.casefold().isin(states)
        if "state" in df else pd.Series(False, index=df.index)
    )
    site_count = (
        pd.to_numeric(df["india_site_count"], errors="coerce").fillna(0).gt(0)
        if "india_site_count" in df else pd.Series(False, index=df.index)
    )
    return (country | state | site_count).astype(bool)


@st.cache_data(ttl=3600)
def load_clinical_trials_data() -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
    """
    Load the cleaned CSV and validate schema plus provenance.

    A syntactically plausible NCT ID alone is not proof that a record came
    from the registry. The ingestion pipeline writes explicit source metadata;
    without it the application marks the dataset unverified and refuses to
    present the records as registry facts.
    """
    metadata: Dict[str, Any] = {
        "file_exists": False,
        "is_empty": False,
        "columns_valid": False,
        "registry_verified": False,
        "source_label": "Unverified legacy dataset",
        "error": None,
        "last_modified": None,
        "record_count": 0,
        "last_updated_timestamp": None,
        "source_last_fetched": None,
        "verification_issues": [],
    }

    try:
        if not CLEANED_DATA_FILE.exists():
            metadata["error"] = f"Data file not found: {CLEANED_DATA_FILE}"
            logger.error(metadata["error"])
            return None, metadata

        metadata["file_exists"] = True
        file_stat = CLEANED_DATA_FILE.stat()
        modified = datetime.fromtimestamp(file_stat.st_mtime)
        metadata["last_modified"] = modified
        metadata["last_updated_timestamp"] = modified.strftime("%Y-%m-%d %H:%M:%S")

        df = pd.read_csv(CLEANED_DATA_FILE)
        if df.empty:
            metadata["is_empty"] = True
            metadata["error"] = "Data file is empty."
            return df, metadata

        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            metadata["error"] = "Missing required columns: " + ", ".join(sorted(missing))
            return None, metadata

        metadata["columns_valid"] = True
        metadata["record_count"] = int(len(df))

        ids = df["nct_id"].astype("string").str.strip()
        ids_valid = ids.str.fullmatch(r"NCT\d{8}", na=False)
        if not bool(ids_valid.all()):
            metadata["verification_issues"].append("One or more identifiers are not valid NCT-ID-shaped strings.")
        if bool(ids.duplicated().any()):
            metadata["verification_issues"].append("Duplicate NCT IDs were found.")

        expected_urls = "https://clinicaltrials.gov/study/" + ids.astype("string")
        provenance_ok = (
            "data_source" in df.columns
            and df["data_source"].astype("string").str.strip()
                .eq("ClinicalTrials.gov API v2").fillna(False).all()
            and "source_url" in df.columns
            and df["source_url"].astype("string").str.strip()
                .eq(expected_urls).fillna(False).all()
        )
        if not provenance_ok:
            metadata["verification_issues"].append(
                "The CSV has no complete ClinicalTrials.gov API v2 provenance marker; rerun ingestion and cleaning."
            )
        metadata["registry_verified"] = bool(ids_valid.all() and not ids.duplicated().any() and provenance_ok)
        if metadata["registry_verified"]:
            metadata["source_label"] = "ClinicalTrials.gov API v2"
        else:
            metadata["error"] = (
                "The included dataset is an unverified legacy snapshot. Run the ingestion and cleaning pipeline "
                "before using its figures as clinical-trial facts."
            )

        for column in ("start_date", "completion_date"):
            raw = df[column].astype("string").str.strip()
            precision_column = f"{column}_precision"
            if precision_column not in df.columns:
                precision = pd.Series("unknown", index=df.index, dtype="string")
                precision.loc[raw.str.fullmatch(r"\d{4}", na=False)] = "year"
                precision.loc[raw.str.fullmatch(r"\d{4}-\d{2}", na=False)] = "month"
                precision.loc[raw.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)] = "day"
                df[precision_column] = precision
            df[column] = pd.to_datetime(raw, errors="coerce")
            df[f"{column.split('_')[0]}_year"] = df[column].dt.year

        for numeric in ("enrollment_count", "trial_duration_days", "india_site_count"):
            if numeric in df.columns:
                df[numeric] = pd.to_numeric(df[numeric], errors="coerce")

        df["has_indian_location"] = _derive_indian_location_flag(df)
        # Never silently rename the old state-only flag: its previous semantics
        # incorrectly implied that the entire study was India-only.
        if "fetched_date" in df.columns:
            fetched = pd.to_datetime(df["fetched_date"], errors="coerce")
            if fetched.notna().any():
                metadata["source_last_fetched"] = fetched.max().strftime("%Y-%m-%d %H:%M:%S")

        logger.info(
            "Loaded %s rows; registry_verified=%s",
            len(df), metadata["registry_verified"]
        )
        return df, metadata

    except Exception as exc:
        metadata["error"] = f"Error loading data: {exc}"
        logger.exception(metadata["error"])
        return None, metadata


def get_unique_values(df: Optional[pd.DataFrame], column: str) -> list:
    """Get stable, sorted unique values from a column, excluding missing values."""
    if df is None or column not in df.columns:
        return []
    return sorted(df[column].dropna().unique().tolist(), key=lambda item: str(item).casefold())


def get_data_summary(df: Optional[pd.DataFrame], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Calculate robust KPI values; sponsor metrics are based on active trial status."""
    if df is None or df.empty:
        return _empty_summary()

    statuses = df.get("recruitment_status", pd.Series("", index=df.index)).astype("string").str.casefold()
    recruiting_mask = statuses.eq("recruiting")
    active_mask = statuses.isin([
        "recruiting", "enrolling by invitation",
        "active, not recruiting", "active not recruiting"
    ])
    completed_mask = statuses.eq("completed")

    def unique_count(column: str) -> int:
        return int(df[column].dropna().nunique()) if column in df else 0

    def first_value(series: pd.Series) -> str:
        return str(series.index[0]) if not series.empty else "N/A"

    if "sponsor" in df:
        sponsor_values = df["sponsor"].astype("string").str.strip()
        known_sponsor_mask = (
            sponsor_values.notna()
            & sponsor_values.ne("")
            & sponsor_values.str.casefold().ne("unknown")
        ).fillna(False)
        sponsor_counts = sponsor_values[known_sponsor_mask].value_counts()
        total_sponsors = int(sponsor_values[known_sponsor_mask].nunique())
        active_sponsors = int(sponsor_values[active_mask & known_sponsor_mask].nunique())
    else:
        sponsor_counts = pd.Series(dtype="int64")
        total_sponsors = 0
        active_sponsors = 0

    area_counts = df.get("therapeutic_area", pd.Series(dtype="string")).dropna().value_counts()
    active_area_counts = df.loc[active_mask, "therapeutic_area"].dropna().value_counts() if "therapeutic_area" in df else pd.Series(dtype="int64")
    state_counts = df.get("state", pd.Series(dtype="string")).dropna().value_counts()

    duration = pd.to_numeric(df.get("trial_duration_days", pd.Series(dtype="float64")), errors="coerce").dropna()
    enrollment = pd.to_numeric(df.get("enrollment_count", pd.Series(dtype="float64")), errors="coerce")

    return {
        "total_trials": int(len(df)),
        "recruiting_trials": int(recruiting_mask.sum()),
        "active_trials": int(active_mask.sum()),
        "completed_trials": int(completed_mask.sum()),
        "total_sponsors": total_sponsors,
        "active_sponsors": active_sponsors,
        "total_areas": unique_count("therapeutic_area"),
        "total_states": unique_count("state"),
        "total_cities": unique_count("city"),
        "avg_duration_days": int(round(float(duration.mean()))) if not duration.empty else 0,
        "total_enrollment": int(enrollment.sum(min_count=1)) if enrollment.notna().any() else 0,
        "top_sponsor": first_value(sponsor_counts),
        "top_area": first_value(area_counts),
        "most_active_area": first_value(active_area_counts),
        "top_state": first_value(state_counts),
    }


def apply_filters(df: Optional[pd.DataFrame], filters: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Apply dashboard filters without mutating the original DataFrame."""
    if df is None or df.empty:
        return df

    filtered = df.copy()
    selections = (
        ("therapeutic_areas", "therapeutic_area"),
        ("phases", "phase"),
        ("statuses", "recruitment_status"),
        ("states", "state"),
    )
    for filter_key, column in selections:
        selected = filters.get(filter_key)
        if selected and column in filtered.columns:
            filtered = filtered[filtered[column].isin(selected)]

    sponsor = filters.get("sponsor")
    if sponsor and sponsor != "All Sponsors" and "sponsor" in filtered.columns:
        filtered = filtered[filtered["sponsor"] == sponsor]

    year_range = filters.get("year_range")
    if year_range and "start_year" in filtered.columns:
        low, high = year_range
        years = pd.to_numeric(filtered["start_year"], errors="coerce")
        filtered = filtered[years.between(low, high, inclusive="both")]

    return filtered


def validate_and_log_data(df: Optional[pd.DataFrame], metadata: Dict[str, Any]) -> bool:
    """Return True only when the dataset passes schema, provenance and basic checks."""
    if metadata.get("error"):
        logger.error("Data validation failed: %s", metadata["error"])
        return False
    if df is None or df.empty:
        logger.warning("Dataset is empty")
        return False
    if not metadata.get("columns_valid"):
        logger.error("Invalid column schema")
        return False
    if not metadata.get("registry_verified"):
        logger.error("Dataset provenance was not verified.")
        return False
    if df["nct_id"].duplicated().any():
        logger.error("Duplicate NCT IDs are not allowed.")
        return False
    if "has_indian_location" in df and not df["has_indian_location"].all():
        logger.error("One or more records lack evidence of an Indian trial location.")
        return False

    missing_ratio = df.isnull().sum() / len(df)
    high_missing = missing_ratio[missing_ratio > 0.5]
    if not high_missing.empty:
        logger.warning("Columns with >50%% missing values: %s", high_missing.to_dict())
    logger.info("Data validation passed")
    return True


def clear_data_cache() -> None:
    """Clear Streamlit's cached data to force a reload."""
    st.cache_data.clear()
    logger.info("Data cache cleared")


if __name__ == "__main__":
    frame, file_metadata = load_clinical_trials_data()
    print(f"Records: {file_metadata.get('record_count', 0)}")
    print(f"Registry verified: {file_metadata.get('registry_verified', False)}")
    if file_metadata.get("error"):
        print(f"Validation note: {file_metadata['error']}")
    if frame is not None and not frame.empty:
        print(get_data_summary(frame, file_metadata))
