"""
Example usage of the Clinical Trials API ingestion module.

This script demonstrates how to:
1. Initialize the API client
2. Fetch trials from ClinicalTrials.gov
3. Validate and clean the data
4. Save to CSV
5. Generate reports
"""

import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingestion.clinical_trials_api import (
    ClinicalTrialsAPIClient,
    extract_trial_record,
    save_trials_to_csv
)
from src.ingestion.validators import TrialValidator, clean_trial_data, validate_dataframe


def example_basic_fetch():
    """
    Example 1: Basic fetch and save.
    
    This is the simplest way to fetch and save clinical trials.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Basic Fetch and Save")
    print("=" * 60)
    
    # Initialize client
    client = ClinicalTrialsAPIClient(page_size=50)
    
    # Fetch trials
    print("Fetching Indian clinical trials...")
    raw_studies = client.fetch_india_trials()
    
    if raw_studies:
        print(f"Fetched {len(raw_studies)} studies")
        
        # Extract records
        trials = [extract_trial_record(study) for study in raw_studies]
        trials = [t for t in trials if t]  # Remove empty records
        
        # Save to CSV
        output_file = save_trials_to_csv(trials)
        print(f"Saved {len(trials)} trials to {output_file}")
    
    client.close()


def example_with_validation():
    """
    Example 2: Fetch with validation and cleaning.
    
    This example includes data validation and cleaning steps.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Fetch with Validation and Cleaning")
    print("=" * 60)
    
    # Initialize client and validator
    client = ClinicalTrialsAPIClient(page_size=50)
    validator = TrialValidator()
    
    # Fetch trials
    print("Fetching Indian clinical trials...")
    raw_studies = client.fetch_india_trials()
    
    if raw_studies:
        print(f"Fetched {len(raw_studies)} studies")
        
        # Extract records
        trials = [extract_trial_record(study) for study in raw_studies]
        trials = [t for t in trials if t]  # Remove empty records
        
        # Validate batch
        print("Validating records...")
        valid_count, invalid_count = validator.validate_batch(trials)
        print(f"Validation: {valid_count} valid, {invalid_count} invalid")
        
        # Clean data
        print("Cleaning records...")
        clean_trials = clean_trial_data(trials)
        
        # Save to CSV
        output_file = save_trials_to_csv(clean_trials)
        
        if output_file and output_file.exists():
            # Validate DataFrame
            df = pd.read_csv(output_file)
            report = validate_dataframe(df)
            print(f"Saved {len(clean_trials)} clean trials to {output_file}")
            print(f"DataFrame shape: {df.shape}")
    
    client.close()


def example_partial_fetch(max_records: int = 10):
    """
    Example 3: Fetch and stop after N records.
    
    Useful for testing and development.
    """
    print("\n" + "=" * 60)
    print(f"EXAMPLE 3: Partial Fetch (First {max_records} Records)")
    print("=" * 60)
    
    # Initialize client with small page size
    client = ClinicalTrialsAPIClient(page_size=max_records)
    
    # Fetch trials
    print(f"Fetching up to {max_records} Indian clinical trials...")
    raw_studies = client.fetch_india_trials()
    
    if raw_studies:
        # Only use first max_records
        raw_studies = raw_studies[:max_records]
        
        # Extract records
        trials = [extract_trial_record(study) for study in raw_studies]
        trials = [t for t in trials if t]  # Remove empty records
        
        print(f"\nSample records ({len(trials)} total):")
        for i, trial in enumerate(trials[:3], 1):
            print(f"\n  Record {i}:")
            print(f"    NCT ID: {trial.get('nct_id')}")
            print(f"    Title: {trial.get('brief_title', 'N/A')[:60]}...")
            print(f"    Sponsor: {trial.get('sponsor')}")
            print(f"    Status: {trial.get('recruitment_status')}")
            print(f"    City: {trial.get('city')}")
            print(f"    State: {trial.get('state')}")
    
    client.close()


def example_error_handling():
    """
    Example 4: Error handling and recovery.
    
    Demonstrates how the client handles network errors.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Error Handling")
    print("=" * 60)
    
    # Initialize client with short timeout to simulate errors
    client = ClinicalTrialsAPIClient(
        timeout=5,  # Short timeout to test retry logic
        max_retries=2,
        retry_delay=1
    )
    
    print("Fetching with limited retries...")
    raw_studies = client.fetch_india_trials()
    
    if raw_studies:
        print(f"Successfully fetched {len(raw_studies)} studies")
    else:
        print("No studies fetched")
    
    print(f"\nFailed requests: {len(client.failed_requests)}")
    for failed in client.failed_requests[:3]:
        print(f"  - {failed.get('error')}")
    
    client.close()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CLINICAL TRIALS API INGESTION - EXAMPLES")
    print("=" * 60)
    
    # Uncomment the examples you want to run:
    
    # example_basic_fetch()
    # example_with_validation()
    example_partial_fetch(max_records=5)
    # example_error_handling()
    
    print("\n" + "=" * 60)
    print("Examples completed")
    print("=" * 60)
