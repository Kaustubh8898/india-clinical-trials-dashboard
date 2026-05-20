"""
Clinical Trials API Ingestion Module

Production-grade module for fetching clinical trial data from ClinicalTrials.gov API v2.
Filters for trials with study locations in India and handles pagination, retries, and logging.

Author: Clinical Trials Analytics Team
Version: 1.0.0
"""

import logging
import json
import time
import requests
import pandas as pd
from typing import Optional, Dict, List, Any
from pathlib import Path
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/api_ingestion.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration constants
API_BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
DEFAULT_PAGE_SIZE = 100
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
REQUEST_TIMEOUT = 30  # seconds
DATA_OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
OUTPUT_FILENAME = "india_trials_raw.csv"

# Ensure output directory exists
DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class ClinicalTrialsAPIClient:
    """
    Client for fetching clinical trial data from ClinicalTrials.gov API v2.
    
    Handles authentication, pagination, retries, and error handling for robust
    data ingestion from ClinicalTrials.gov.
    """
    
    def __init__(
        self,
        base_url: str = API_BASE_URL,
        page_size: int = DEFAULT_PAGE_SIZE,
        max_retries: int = MAX_RETRIES,
        retry_delay: int = RETRY_DELAY,
        timeout: int = REQUEST_TIMEOUT
    ):
        """
        Initialize the API client.
        
        Args:
            base_url (str): Base URL for ClinicalTrials.gov API v2
            page_size (int): Number of records per API page
            max_retries (int): Maximum number of retry attempts
            retry_delay (int): Delay in seconds between retries
            timeout (int): Request timeout in seconds
        """
        self.base_url = base_url
        self.page_size = page_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.session = requests.Session()
        self.total_records_fetched = 0
        self.failed_requests = []
        
        logger.info(
            f"Initialized ClinicalTrialsAPIClient - "
            f"Base URL: {base_url}, Page Size: {page_size}"
        )
    
    def _make_request(
        self,
        params: Dict[str, Any],
        attempt: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Make an HTTP GET request with retry logic.
        
        Args:
            params (Dict): Query parameters for the API request
            attempt (int): Current attempt number
            
        Returns:
            Optional[Dict]: JSON response if successful, None otherwise
        """
        try:
            logger.debug(f"Making API request (Attempt {attempt}/{self.max_retries + 1})")
            
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.warning(f"Request timeout (Attempt {attempt})")
            if attempt <= self.max_retries:
                time.sleep(self.retry_delay)
                return self._make_request(params, attempt + 1)
            self.failed_requests.append({"params": params, "error": "Timeout"})
            return None
            
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error (Attempt {attempt}): {str(e)}")
            if attempt <= self.max_retries:
                time.sleep(self.retry_delay)
                return self._make_request(params, attempt + 1)
            self.failed_requests.append({"params": params, "error": f"Connection: {str(e)}"})
            return None
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {str(e)}")
            self.failed_requests.append({"params": params, "error": f"HTTP {e.response.status_code}"})
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            self.failed_requests.append({"params": params, "error": "Invalid JSON response"})
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            self.failed_requests.append({"params": params, "error": str(e)})
            return None
    
    def fetch_india_trials(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch all clinical trials with study locations in India.
        
        Uses pagination to retrieve all matching trials from ClinicalTrials.gov API.
        Filters for studies with locations in India.
        
        Returns:
            Optional[List[Dict]]: List of trial records if successful, None otherwise
        """
        all_trials = []
        page_token = None
        page_number = 1
        
        logger.info("Starting fetch of Indian clinical trials...")
        
        while True:
            logger.info(f"Fetching page {page_number}...")
            
            # Build query parameters
            params = {
                "pageSize": self.page_size,
                "countryFilter": "India",  # Filter for India
                "fields": "NCTId,BriefTitle,Sponsor,OverallStatus,Phase,Condition,RecruitmentStatus,StartDate,CompletionDate,EnrollmentCount,StudyLocations"
            }
            
            # Add pagination token if available
            if page_token:
                params["pageToken"] = page_token
            
            # Make API request
            response = self._make_request(params)
            
            if response is None:
                logger.error(f"Failed to fetch page {page_number} after retries")
                break
            
            # Extract studies from response
            studies = response.get("studies", [])
            
            if not studies:
                logger.info(f"No more trials found (page {page_number} was empty)")
                break
            
            logger.info(f"Retrieved {len(studies)} trials on page {page_number}")
            all_trials.extend(studies)
            self.total_records_fetched += len(studies)
            
            # Check for next page
            page_token = response.get("nextPageToken")
            if not page_token:
                logger.info("Reached last page")
                break
            
            page_number += 1
            time.sleep(0.5)  # Rate limiting - be respectful to the API
        
        logger.info(
            f"Completed fetch - Total records retrieved: {self.total_records_fetched}"
        )
        
        return all_trials if all_trials else None
    
    def close(self):
        """Close the session connection."""
        self.session.close()
        logger.info("API client session closed")


def parse_study_locations(study_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract location information from study data.
    
    Args:
        study_data (Dict): Raw study data from API
        
    Returns:
        Dict: Extracted location data with city, state, country
    """
    location_info = {
        "city": None,
        "state": None,
        "country": None
    }
    
    try:
        # Navigate nested structure for study locations
        protocol = study_data.get("protocolSection", {})
        contact_info = protocol.get("contactsLocationsModule", {})
        locations = contact_info.get("locations", [])
        
        if locations:
            # Extract first location's details
            first_location = locations[0]
            location_info["city"] = first_location.get("city")
            location_info["state"] = first_location.get("state")
            location_info["country"] = first_location.get("country")
    
    except (KeyError, TypeError, IndexError) as e:
        logger.debug(f"Error parsing study locations: {str(e)}")
    
    return location_info


def extract_trial_record(study: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract relevant fields from a raw study record.
    
    Maps nested API response structure to flat trial record format.
    
    Args:
        study (Dict): Raw study data from API
        
    Returns:
        Dict: Extracted trial record with required fields
    """
    try:
        # Navigate nested structure
        protocol = study.get("protocolSection", {})
        identification = protocol.get("identificationModule", {})
        status = protocol.get("statusModule", {})
        design = protocol.get("designModule", {})
        recruitment = protocol.get("recruitmentModule", {})
        
        # Extract location information
        location_info = parse_study_locations(study)
        
        # Build trial record
        trial_record = {
            "nct_id": identification.get("nctId"),
            "brief_title": identification.get("briefTitle"),
            "sponsor": identification.get("organization", {}).get("name"),
            "phase": design.get("phases", [None])[0] if design.get("phases") else None,
            "conditions": ", ".join(
                protocol.get("conditionsModule", {}).get("conditions", [])
            ),
            "recruitment_status": status.get("overallStatus"),
            "start_date": status.get("startDateStruct", {}).get("date"),
            "completion_date": status.get("completionDateStruct", {}).get("date"),
            "enrollment_count": recruitment.get("enrollmentCount"),
            "city": location_info["city"],
            "state": location_info["state"],
            "country": location_info["country"],
            "fetched_date": datetime.now().isoformat()
        }
        
        return trial_record
        
    except Exception as e:
        logger.error(f"Error extracting trial record: {str(e)}")
        return {}


def save_trials_to_csv(
    trials: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Optional[Path]:
    """
    Save trial records to a CSV file.
    
    Args:
        trials (List[Dict]): List of trial records
        output_path (Optional[Path]): Output file path (uses default if None)
        
    Returns:
        Optional[Path]: Path to saved file if successful, None otherwise
    """
    if not trials:
        logger.warning("No trials to save")
        return None
    
    output_path = output_path or DATA_OUTPUT_DIR / OUTPUT_FILENAME
    
    try:
        df = pd.DataFrame(trials)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=False)
        logger.info(
            f"Saved {len(trials)} trial records to {output_path}"
        )
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error saving trials to CSV: {str(e)}")
        return None


def generate_ingestion_report(
    total_fetched: int,
    total_parsed: int,
    failed_requests: List[Dict],
    output_file: Optional[Path]
) -> None:
    """
    Generate a summary report of the ingestion process.
    
    Args:
        total_fetched (int): Total records fetched from API
        total_parsed (int): Total records successfully parsed
        failed_requests (List[Dict]): List of failed requests
        output_file (Optional[Path]): Output file path
    """
    report = f"""
    ============================================================
    CLINICAL TRIALS API INGESTION REPORT
    ============================================================
    
    Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    RESULTS:
    - Total Records Fetched: {total_fetched}
    - Total Records Parsed: {total_parsed}
    - Success Rate: {(total_parsed / total_fetched * 100):.1f}% if total_fetched > 0 else 0%
    - Failed Requests: {len(failed_requests)}
    - Output File: {output_file}
    
    SUMMARY:
    - API Endpoint: {API_BASE_URL}
    - Region Filter: India
    - Page Size: {DEFAULT_PAGE_SIZE}
    - Max Retries: {MAX_RETRIES}
    
    {'ERRORS:' if failed_requests else ''}
    {chr(10).join([f"  - {f}" for f in failed_requests[:5]]) if failed_requests else ''}
    
    ============================================================
    """
    
    logger.info(report)
    print(report)


def main():
    """
    Main execution function for API ingestion.
    
    Orchestrates the complete workflow:
    1. Initialize API client
    2. Fetch trials from India
    3. Parse and extract fields
    4. Save to CSV
    5. Generate report
    """
    logger.info("=" * 60)
    logger.info("STARTING CLINICAL TRIALS API INGESTION")
    logger.info("=" * 60)
    
    try:
        # Initialize API client
        client = ClinicalTrialsAPIClient()
        
        # Fetch trials from India
        logger.info("Fetching clinical trials with India locations...")
        raw_studies = client.fetch_india_trials()
        
        if not raw_studies:
            logger.error("No trials fetched from API")
            generate_ingestion_report(0, 0, client.failed_requests, None)
            return
        
        logger.info(f"Processing {len(raw_studies)} trials...")
        
        # Extract and parse trials
        parsed_trials = []
        for study in raw_studies:
            trial_record = extract_trial_record(study)
            if trial_record and trial_record.get("nct_id"):
                parsed_trials.append(trial_record)
        
        logger.info(f"Successfully parsed {len(parsed_trials)} trials")
        
        # Save to CSV
        output_file = save_trials_to_csv(parsed_trials)
        
        # Generate report
        generate_ingestion_report(
            len(raw_studies),
            len(parsed_trials),
            client.failed_requests,
            output_file
        )
        
        # Close client
        client.close()
        
        logger.info("=" * 60)
        logger.info("INGESTION COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error during ingestion: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
