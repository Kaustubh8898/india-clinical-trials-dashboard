"""
Clinical Trials Data Cleaning Module

Production-grade module for cleaning and normalizing clinical trial datasets.
Handles data quality, standardization, and transformation for the India Clinical
Trials Intelligence Dashboard.

Author: Clinical Trials Analytics Team
Version: 1.0.0
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import re
import sys

# Create the log directory before registering a FileHandler; this must work
# in a fresh checkout where logs/ is not present yet.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "data_cleaning.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
INPUT_FILENAME = "india_trials_raw.csv"
OUTPUT_FILENAME = "india_trials_clean.csv"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
Path("logs").mkdir(parents=True, exist_ok=True)


# ============================================================================
# STANDARDIZATION MAPS
# ============================================================================

PHASE_STANDARDIZATION = {
    "early phase 1": "Early Phase 1", "early_phase1": "Early Phase 1",
    "phase 1": "Phase 1", "phase1": "Phase 1",
    "phase i": "Phase 1", "phasei": "Phase 1", "1": "Phase 1",
    "phase 2": "Phase 2", "phase2": "Phase 2",
    "phase ii": "Phase 2", "phaseii": "Phase 2", "2": "Phase 2",
    "phase 3": "Phase 3", "phase3": "Phase 3",
    "phase iii": "Phase 3", "phaseiii": "Phase 3", "3": "Phase 3",
    "phase 4": "Phase 4", "phase4": "Phase 4",
    "phase iv": "Phase 4", "phaseiv": "Phase 4", "4": "Phase 4",
    "not applicable": "Not Applicable",
    "not_applicable": "Not Applicable",
    "n/a": "Not Applicable", "na": "Not Applicable",
    "": "Unknown",
}

RECRUITMENT_STATUS_STANDARDIZATION = {
    "recruiting": "Recruiting",
    "active, not recruiting": "Active, not recruiting",
    "active not recruiting": "Active, not recruiting",
    "active_not_recruiting": "Active, not recruiting",
    "enrolling by invitation": "Enrolling by invitation",
    "enrolling_by_invitation": "Enrolling by invitation",
    "not yet recruiting": "Not yet recruiting",
    "not_yet_recruiting": "Not yet recruiting",
    "suspended": "Suspended",
    "terminated": "Terminated",
    "completed": "Completed",
    "unknown": "Unknown",
    "unknown_status": "Unknown",
    "withdrawn": "Withdrawn",
    "no longer available": "No longer available",
    "no_longer_available": "No longer available",
    "available": "Available",
    "temporarily not available": "Temporarily not available",
    "temporarily_not_available": "Temporarily not available",
    "": "Unknown",
}

THERAPEUTIC_AREA_MAPPING = {
    "cancer": "Oncology",
    "oncology": "Oncology",
    "tumor": "Oncology",
    "malignancy": "Oncology",
    
    "heart": "Cardiology",
    "cardiac": "Cardiology",
    "cardiovascular": "Cardiology",
    "hypertension": "Cardiology",
    "arrhythmia": "Cardiology",
    
    "lung": "Respiratory",
    "respiratory": "Respiratory",
    "asthma": "Respiratory",
    "copd": "Respiratory",
    "bronchi": "Respiratory",
    
    "infection": "Infectious Disease",
    "infectious": "Infectious Disease",
    "covid": "Infectious Disease",
    "hiv": "Infectious Disease",
    "tuberculosis": "Infectious Disease",
    "tb": "Infectious Disease",
    
    "gastro": "Gastroenterology",
    "digestive": "Gastroenterology",
    "liver": "Hepatology",
    "hepatic": "Hepatology",
    
    "brain": "Neurology",
    "neurological": "Neurology",
    "neuro": "Neurology",
    "parkinson": "Neurology",
    "alzheimer": "Neurology",
    "epilepsy": "Neurology",
    
    "joint": "Rheumatology",
    "rheumat": "Rheumatology",
    "arthritis": "Rheumatology",
    
    "diabetes": "Endocrinology",
    "thyroid": "Endocrinology",
    "metabolic": "Endocrinology",
    
    "immune": "Immunology",
    "autoimmune": "Immunology",
    
    "eye": "Ophthalmology",
    "ophthal": "Ophthalmology",
    "vision": "Ophthalmology",
    
    "skin": "Dermatology",
    "dermat": "Dermatology",
    "psoriasis": "Dermatology",
}

INDIAN_STATES = {
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
    "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya",
    "mizoram", "nagaland", "odisha", "punjab", "rajasthan", "sikkim",
    "tamil nadu", "telangana", "tripura", "uttar pradesh", "uttarakhand",
    "west bengal", "delhi", "jammu and kashmir", "ladakh"
}

MAJOR_INDIAN_CITIES = {
    "mumbai", "delhi", "bangalore", "hyderabad", "chennai", "kolkata",
    "pune", "ahmedabad", "jaipur", "lucknow", "chandigarh", "kochi",
    "indore", "bhopal", "visakhapatnam", "pimpri-chinchwad", "patna",
    "vadodara", "ghaziabad", "ludhiana", "coimbatore", "nashik",
    "agra", "salem", "srinagar", "aurangabad", "dhanbad",
}


class TrialDataCleaner:
    """
    Comprehensive data cleaning and standardization for clinical trials.
    
    Handles:
    - Data loading and validation
    - Duplicate removal
    - Text standardization
    - Date parsing
    - Missing value handling
    - Geographic normalization
    - Feature engineering
    """
    
    def __init__(self, input_file: Optional[Path] = None):
        """
        Initialize the data cleaner.
        
        Args:
            input_file (Optional[Path]): Path to raw data file
        """
        self.input_file = input_file or (RAW_DATA_DIR / INPUT_FILENAME)
        self.df = None
        self.original_row_count = 0
        self.cleaning_report = {}
        
        logger.info(f"Initialized TrialDataCleaner with input: {self.input_file}")
    
    def load_raw_data(self) -> pd.DataFrame:
        """
        Load raw trial data from CSV file.
        
        Returns:
            pd.DataFrame: Loaded dataframe
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            Exception: If data loading fails
        """
        try:
            if not self.input_file.exists():
                raise FileNotFoundError(f"Input file not found: {self.input_file}")
            
            self.df = pd.read_csv(self.input_file)
            self.original_row_count = len(self.df)

            required_columns = {
                "nct_id", "brief_title", "sponsor", "phase", "conditions",
                "recruitment_status", "start_date", "completion_date",
                "enrollment_count", "city", "state", "country", "fetched_date",
                "data_source", "source_url"
            }
            missing_columns = required_columns - set(self.df.columns)
            if missing_columns:
                raise ValueError(
                    "Raw dataset is missing required columns: "
                    + ", ".join(sorted(missing_columns))
                )
            if self.df.empty:
                raise ValueError("Raw dataset contains no records.")

            ids = self.df["nct_id"].astype("string").str.strip()
            valid_ids = ids.str.fullmatch(r"NCT\d{8}", na=False)
            if not valid_ids.all():
                examples = ids[~valid_ids].head(5).tolist()
                raise ValueError(f"Invalid or missing NCT identifiers: {examples}")

            sources = self.df["data_source"].astype("string").str.strip()
            if not sources.eq("ClinicalTrials.gov API v2").fillna(False).all():
                raise ValueError("Raw data is missing the expected ClinicalTrials.gov API v2 source marker.")

            expected_urls = "https://clinicaltrials.gov/study/" + ids.astype("string")
            actual_urls = self.df["source_url"].astype("string").str.strip()
            if not actual_urls.eq(expected_urls).fillna(False).all():
                raise ValueError("Source URL does not match the NCT ID for every row.")

            logger.info(f"Loaded {self.original_row_count} rows from {self.input_file}")
            logger.info(f"Columns: {list(self.df.columns)}")
            
            return self.df
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
    
    def remove_duplicates(self) -> None:
        """Remove duplicate NCT IDs, keeping the first occurrence."""
        if self.df is None:
            raise ValueError("No data loaded. Call load_raw_data() first.")
        
        initial_count = len(self.df)
        
        # Remove duplicates based on nct_id
        if "nct_id" in self.df.columns:
            self.df = self.df.drop_duplicates(subset=["nct_id"], keep="first")
            
            removed_count = initial_count - len(self.df)
            self.cleaning_report["duplicates_removed"] = removed_count
            
            logger.info(f"Removed {removed_count} duplicate NCT IDs")
        else:
            logger.warning("nct_id column not found, skipping duplicate removal")
    
    def standardize_phase(self) -> None:
        """Standardize trial phase values."""
        if self.df is None or "phase" not in self.df.columns:
            logger.warning("No phase column found")
            return
        
        def normalize_phase(phase):
            if pd.isna(phase):
                return "Unknown"
            phase_str = str(phase).lower().strip()
            return PHASE_STANDARDIZATION.get(phase_str, "Unknown")
        
        self.df["phase"] = self.df["phase"].apply(normalize_phase)
        
        phase_counts = self.df["phase"].value_counts()
        logger.info(f"Phase distribution:\n{phase_counts}")
        self.cleaning_report["phase_distribution"] = phase_counts.to_dict()
    
    def standardize_recruitment_status(self) -> None:
        """Standardize recruitment status values."""
        if self.df is None or "recruitment_status" not in self.df.columns:
            logger.warning("No recruitment_status column found")
            return
        
        def normalize_status(status):
            if pd.isna(status):
                return "Unknown"
            status_str = str(status).lower().strip()
            return RECRUITMENT_STATUS_STANDARDIZATION.get(
                status_str, status
            )
        
        self.df["recruitment_status"] = self.df["recruitment_status"].apply(
            normalize_status
        )
        
        status_counts = self.df["recruitment_status"].value_counts()
        logger.info(f"Recruitment status distribution:\n{status_counts}")
        self.cleaning_report["status_distribution"] = status_counts.to_dict()
    
    def standardize_sponsor_names(self) -> None:
        """Standardize and clean sponsor organization names."""
        if self.df is None or "sponsor" not in self.df.columns:
            logger.warning("No sponsor column found")
            return
        
        def clean_sponsor(sponsor):
            if pd.isna(sponsor) or not sponsor:
                return "Unknown"
            
            sponsor_str = str(sponsor).strip()
            
            # Preserve registered/legal suffixes: removing them can merge
            # distinct sponsor entities. Normalize whitespace only.
            sponsor_str = " ".join(sponsor_str.split())
            
            return sponsor_str if sponsor_str else "Unknown"
        
        self.df["sponsor"] = self.df["sponsor"].apply(clean_sponsor)
        
        top_sponsors = self.df["sponsor"].value_counts().head(10)
        logger.info(f"Top 10 sponsors:\n{top_sponsors}")
        self.cleaning_report["top_sponsors"] = top_sponsors.to_dict()
    
    def extract_therapeutic_area(self) -> None:
        """
        Extract therapeutic area from conditions field.
        
        Maps condition keywords to standardized therapeutic areas.
        """
        if self.df is None or "conditions" not in self.df.columns:
            logger.warning("No conditions column found")
            return
        
        def get_therapeutic_area(conditions):
            if pd.isna(conditions) or not conditions:
                return "Other"
            
            conditions_str = str(conditions).lower()
            
            # Check for keyword matches
            for keyword, area in THERAPEUTIC_AREA_MAPPING.items():
                if keyword in conditions_str:
                    return area
            
            return "Other"
        
        self.df["therapeutic_area"] = self.df["conditions"].apply(
            get_therapeutic_area
        )
        
        area_counts = self.df["therapeutic_area"].value_counts()
        logger.info(f"Therapeutic area distribution:\n{area_counts}")
        self.cleaning_report["therapeutic_areas"] = area_counts.to_dict()
    
    def parse_dates(self) -> None:
        """Parse start_date and completion_date to datetime objects."""
        if self.df is None:
            return
        
        date_columns = ["start_date", "completion_date"]
        
        for col in date_columns:
            if col in self.df.columns:
                try:
                    raw_values = self.df[col].astype("string").str.strip()
                    precision = pd.Series("unknown", index=self.df.index, dtype="string")
                    precision.loc[raw_values.str.fullmatch(r"\d{4}", na=False)] = "year"
                    precision.loc[raw_values.str.fullmatch(r"\d{4}-\d{2}", na=False)] = "month"
                    precision.loc[raw_values.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)] = "day"
                    self.df[f"{col}_precision"] = precision
                    self.df[col] = pd.to_datetime(raw_values, errors="coerce")
                    
                    null_count = self.df[col].isna().sum()
                    if null_count > 0:
                        logger.warning(
                            f"Could not parse {null_count} dates in {col}"
                        )
                except Exception as e:
                    logger.warning(f"Error parsing {col}: {str(e)}")
    
    def create_trial_duration(self) -> None:
        """Create trial_duration_days column from date fields."""
        if self.df is None:
            return
        
        if "start_date" not in self.df.columns or "completion_date" not in self.df.columns:
            logger.warning("Date columns not found, skipping duration calculation")
            return
        
        def calculate_duration(row):
            if pd.isna(row["start_date"]) or pd.isna(row["completion_date"]):
                return None

            # Registry dates may specify only year/month precision. Only
            # calculate day-level duration when both dates specify a full day.
            if "start_date_precision" in row.index and row["start_date_precision"] != "day":
                return None
            if "completion_date_precision" in row.index and row["completion_date_precision"] != "day":
                return None

            duration = (row["completion_date"] - row["start_date"]).days
            return duration if duration >= 0 else None
        
        self.df["trial_duration_days"] = self.df.apply(
            calculate_duration, axis=1
        )
        
        avg_duration = self.df["trial_duration_days"].mean()
        logger.info(f"Average trial duration: {avg_duration:.0f} days")
        self.cleaning_report["avg_trial_duration_days"] = avg_duration
    
    def normalize_geographic_data(self) -> None:
        """Normalize city, state, and country text."""
        if self.df is None:
            return
        
        def normalize_text(text):
            if pd.isna(text) or not text:
                return None
            
            text_str = str(text).strip()
            # Title case with proper spacing
            text_str = " ".join([word.capitalize() for word in text_str.split()])
            
            return text_str if text_str else None
        
        for col in ["city", "state", "country"]:
            if col in self.df.columns:
                self.df[col] = self.df[col].apply(normalize_text)
        
        logger.info(f"Normalized {len(self.df)} geographic entries")
    
    def validate_india_location(self) -> None:
        """
        Add has_indian_location using country, site-count, or state evidence.

        This does not claim a study is India-only; a multinational study can
        include Indian sites.
        """
        if self.df is None:
            return

        country_evidence = (
            self.df["country"].astype("string").str.strip().str.casefold().eq("india")
            if "country" in self.df.columns
            else pd.Series(False, index=self.df.index)
        )
        state_evidence = (
            self.df["state"].astype("string").str.strip().str.casefold().isin(INDIAN_STATES)
            if "state" in self.df.columns
            else pd.Series(False, index=self.df.index)
        )
        if "india_site_count" in self.df.columns:
            site_count = pd.to_numeric(
                self.df["india_site_count"], errors="coerce"
            ).fillna(0)
            site_evidence = site_count.gt(0)
        else:
            site_evidence = pd.Series(False, index=self.df.index)

        self.df["has_indian_location"] = (
            country_evidence | state_evidence | site_evidence
        ).astype(bool)

        india_trials = int(self.df["has_indian_location"].sum())
        total_trials = len(self.df)
        percentage = india_trials / total_trials * 100 if total_trials else 0.0
        logger.info(
            "Records with Indian-location evidence: %s/%s (%.1f%%)",
            india_trials, total_trials, percentage
        )
        self.cleaning_report["has_indian_location_count"] = india_trials
    
    def handle_missing_values(self) -> None:
        """Handle and report missing values in key columns."""
        if self.df is None:
            return
        
        missing_report = {}
        
        for col in self.df.columns:
            null_count = self.df[col].isna().sum()
            if null_count > 0:
                pct = (null_count / len(self.df)) * 100
                missing_report[col] = {
                    "count": int(null_count),
                    "percentage": round(pct, 2)
                }
        
        if missing_report:
            logger.info(f"Missing values report:\n{missing_report}")
            self.cleaning_report["missing_values"] = missing_report
        else:
            logger.info("No missing values found")
    
    def convert_data_types(self) -> None:
        """Convert columns to appropriate data types."""
        if self.df is None:
            return
        
        type_conversions = {
            "enrollment_count": "Int64",  # Nullable integer
            "trial_duration_days": "Int64",
            "has_indian_location": "bool",
            "india_site_count": "Int64"
        }
        
        for col, dtype in type_conversions.items():
            if col in self.df.columns:
                try:
                    self.df[col] = self.df[col].astype(dtype)
                    logger.info(f"Converted {col} to {dtype}")
                except Exception as e:
                    logger.warning(f"Could not convert {col} to {dtype}: {str(e)}")
    
    def clean(self) -> pd.DataFrame:
        """
        Execute the complete data cleaning pipeline.
        
        Returns:
            pd.DataFrame: Cleaned dataframe
        """
        logger.info("=" * 60)
        logger.info("STARTING DATA CLEANING PIPELINE")
        logger.info("=" * 60)
        
        try:
            # Load data
            self.load_raw_data()
            
            # Cleaning steps in order
            self.remove_duplicates()
            self.standardize_phase()
            self.standardize_recruitment_status()
            self.standardize_sponsor_names()
            self.extract_therapeutic_area()
            self.parse_dates()
            self.create_trial_duration()
            self.normalize_geographic_data()
            self.validate_india_location()
            self.handle_missing_values()
            self.convert_data_types()
            
            logger.info("=" * 60)
            logger.info("DATA CLEANING PIPELINE COMPLETED")
            logger.info("=" * 60)
            
            return self.df
            
        except Exception as e:
            logger.error(f"Error in cleaning pipeline: {str(e)}", exc_info=True)
            raise
    
    def save_cleaned_data(
        self,
        output_file: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Save cleaned data to CSV file.
        
        Args:
            output_file (Optional[Path]): Output file path
            
        Returns:
            Optional[Path]: Path to saved file
        """
        if self.df is None:
            logger.error("No cleaned data to save")
            return None
        
        output_file = output_file or (PROCESSED_DATA_DIR / OUTPUT_FILENAME)

        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            temporary_file = output_file.with_suffix(output_file.suffix + ".tmp")
            self.df.to_csv(temporary_file, index=False)
            temporary_file.replace(output_file)

            logger.info(f"Saved {len(self.df)} cleaned records to {output_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error saving cleaned data: {str(e)}")
            return None
    
    def get_cleaning_report(self) -> Dict:
        """
        Get detailed cleaning report.
        
        Returns:
            Dict: Cleaning statistics and metrics
        """
        report = {
            "original_row_count": self.original_row_count,
            "final_row_count": len(self.df) if self.df is not None else 0,
            "rows_removed": self.original_row_count - (len(self.df) if self.df is not None else 0),
            "cleaning_details": self.cleaning_report,
            "cleaned_at": datetime.now().isoformat()
        }
        
        return report


def print_cleaning_report(report: Dict) -> None:
    """
    Pretty-print the cleaning report.
    
    Args:
        report (Dict): Cleaning report dictionary
    """
    output = f"""
    ============================================================
    CLINICAL TRIALS DATA CLEANING REPORT
    ============================================================
    
    SUMMARY:
    - Original Records: {report['original_row_count']}
    - Final Records: {report['final_row_count']}
    - Records Removed: {report['rows_removed']}
    - Cleaned At: {report['cleaned_at']}
    
    DETAILS:
    """
    
    details = report.get("cleaning_details", {})
    for key, value in details.items():
        if isinstance(value, dict):
            output += f"\n    {key}:\n"
            for subkey, subvalue in list(value.items())[:5]:
                output += f"      {subkey}: {subvalue}\n"
        else:
            output += f"    {key}: {value}\n"
    
    output += "\n    ============================================================\n"
    
    logger.info(output)
    print(output)


def main():
    """
    Main execution function for data cleaning.
    
    Orchestrates the complete cleaning workflow.
    """
    logger.info("=" * 60)
    logger.info("CLINICAL TRIALS DATA CLEANING - MAIN")
    logger.info("=" * 60)
    
    try:
        # Initialize cleaner
        cleaner = TrialDataCleaner()
        
        # Execute cleaning pipeline
        cleaned_df = cleaner.clean()
        
        # Save cleaned data
        output_file = cleaner.save_cleaned_data()
        
        # Generate and display report
        report = cleaner.get_cleaning_report()
        print_cleaning_report(report)
        
        if output_file:
            logger.info(f"✓ Cleaning completed successfully")
            logger.info(f"✓ Output file: {output_file}")
            return 0
        else:
            logger.error("✗ Failed to save cleaned data")
            return 1
        
    except Exception as e:
        logger.error(f"Fatal error during cleaning: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
