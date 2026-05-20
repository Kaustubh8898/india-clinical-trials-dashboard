"""
Data validation module for clinical trial records.

Provides functions to validate and quality-check clinical trial data
ingested from various sources.
"""

import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class TrialValidator:
    """Validator for clinical trial records."""
    
    REQUIRED_FIELDS = [
        "nct_id",
        "brief_title",
        "sponsor",
        "recruitment_status"
    ]
    
    VALID_PHASES = ["Phase 1", "Phase 2", "Phase 3", "Phase 4", "Not Applicable"]
    
    VALID_RECRUITMENT_STATUSES = [
        "Recruiting",
        "Active, not recruiting",
        "Enrolling by invitation",
        "Not yet recruiting",
        "Suspended",
        "Terminated",
        "Completed",
        "Unknown"
    ]
    
    def __init__(self):
        """Initialize the validator."""
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_record(self, trial: Dict[str, Any]) -> bool:
        """
        Validate a single trial record.
        
        Args:
            trial (Dict): Trial record to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        self.validation_errors = []
        self.validation_warnings = []
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if not trial.get(field):
                self.validation_errors.append(f"Missing required field: {field}")
        
        if self.validation_errors:
            return False
        
        # Validate NCT ID format
        nct_id = trial.get("nct_id", "")
        if not nct_id.startswith("NCT"):
            self.validation_errors.append(f"Invalid NCT ID format: {nct_id}")
        
        # Validate phase if present
        if trial.get("phase") and trial["phase"] not in self.VALID_PHASES:
            self.validation_warnings.append(f"Unusual phase value: {trial['phase']}")
        
        # Validate recruitment status
        if trial.get("recruitment_status") not in self.VALID_RECRUITMENT_STATUSES:
            self.validation_warnings.append(
                f"Unexpected recruitment status: {trial['recruitment_status']}"
            )
        
        # Validate enrollment count
        if trial.get("enrollment_count"):
            try:
                enrollment = int(trial["enrollment_count"])
                if enrollment < 0:
                    self.validation_warnings.append("Negative enrollment count")
            except (ValueError, TypeError):
                self.validation_warnings.append(
                    f"Invalid enrollment count: {trial['enrollment_count']}"
                )
        
        # Validate dates
        try:
            if trial.get("start_date") and trial.get("completion_date"):
                start = datetime.fromisoformat(trial["start_date"])
                completion = datetime.fromisoformat(trial["completion_date"])
                if completion < start:
                    self.validation_warnings.append(
                        "Completion date before start date"
                    )
        except (ValueError, TypeError) as e:
            self.validation_warnings.append(f"Date parsing error: {str(e)}")
        
        return len(self.validation_errors) == 0
    
    def validate_batch(self, trials: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Validate a batch of trial records.
        
        Args:
            trials (List[Dict]): Batch of trial records
            
        Returns:
            Tuple[int, int]: (valid_count, invalid_count)
        """
        valid_count = 0
        invalid_count = 0
        
        for trial in trials:
            if self.validate_record(trial):
                valid_count += 1
            else:
                invalid_count += 1
                if invalid_count <= 5:  # Log first 5 errors
                    logger.warning(
                        f"Invalid record {trial.get('nct_id')}: {self.validation_errors}"
                    )
        
        logger.info(
            f"Validation complete - Valid: {valid_count}, Invalid: {invalid_count}"
        )
        
        return valid_count, invalid_count


def validate_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate a DataFrame of clinical trial records.
    
    Args:
        df (pd.DataFrame): DataFrame with trial records
        
    Returns:
        Dict: Validation report
    """
    report = {
        "total_rows": len(df),
        "missing_values": df.isnull().sum().to_dict(),
        "duplicate_nct_ids": df["nct_id"].duplicated().sum() if "nct_id" in df.columns else 0,
        "data_types": df.dtypes.to_dict()
    }
    
    logger.info(f"DataFrame validation report: {report}")
    
    return report


def clean_trial_data(trials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Clean and standardize trial records.
    
    Args:
        trials (List[Dict]): Raw trial records
        
    Returns:
        List[Dict]: Cleaned trial records
    """
    cleaned_trials = []
    
    for trial in trials:
        cleaned_trial = trial.copy()
        
        # Standardize text fields
        if "brief_title" in cleaned_trial:
            cleaned_trial["brief_title"] = cleaned_trial["brief_title"].strip()
        
        if "sponsor" in cleaned_trial:
            cleaned_trial["sponsor"] = cleaned_trial["sponsor"].strip()
        
        # Standardize phase
        if "phase" in cleaned_trial and cleaned_trial["phase"]:
            phase = cleaned_trial["phase"].upper()
            if "1" in phase:
                cleaned_trial["phase"] = "Phase 1"
            elif "2" in phase:
                cleaned_trial["phase"] = "Phase 2"
            elif "3" in phase:
                cleaned_trial["phase"] = "Phase 3"
            elif "4" in phase:
                cleaned_trial["phase"] = "Phase 4"
        
        # Convert enrollment to integer
        if "enrollment_count" in cleaned_trial:
            try:
                cleaned_trial["enrollment_count"] = int(cleaned_trial["enrollment_count"])
            except (ValueError, TypeError):
                cleaned_trial["enrollment_count"] = None
        
        cleaned_trials.append(cleaned_trial)
    
    logger.info(f"Cleaned {len(cleaned_trials)} trial records")
    
    return cleaned_trials
