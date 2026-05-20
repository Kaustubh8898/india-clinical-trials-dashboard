"""
Example usage of the Clinical Trials data cleaning module.

Demonstrates:
1. Basic cleaning workflow
2. Custom cleaning with specific options
3. Data quality report generation
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.cleaning.clean_trials import (
    TrialDataCleaner,
    print_cleaning_report
)
import pandas as pd


def example_basic_cleaning():
    """
    Example 1: Basic cleaning workflow.
    
    This is the simplest way to clean the raw trial data.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Basic Cleaning Workflow")
    print("=" * 60)
    
    # Initialize cleaner
    cleaner = TrialDataCleaner()
    
    # Execute cleaning
    print("Cleaning raw trial data...")
    cleaned_df = cleaner.clean()
    
    # Save cleaned data
    output_file = cleaner.save_cleaned_data()
    
    # Display report
    if output_file:
        report = cleaner.get_cleaning_report()
        print_cleaning_report(report)
        
        print(f"\nCleaned data shape: {cleaned_df.shape}")
        print(f"Columns: {list(cleaned_df.columns)}")
        print(f"\nFirst record:")
        print(cleaned_df.iloc[0])


def example_inspect_data():
    """
    Example 2: Inspect and analyze cleaned data.
    
    Demonstrates data exploration after cleaning.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Inspect Cleaned Data")
    print("=" * 60)
    
    # Initialize cleaner
    cleaner = TrialDataCleaner()
    
    # Clean data
    cleaned_df = cleaner.clean()
    
    # Save
    output_file = cleaner.save_cleaned_data()
    
    if output_file:
        # Load and inspect
        df = pd.read_csv(output_file)
        
        print(f"\nDataset Shape: {df.shape}")
        print(f"\nColumn Data Types:")
        print(df.dtypes)
        
        print(f"\nPhase Distribution:")
        print(df["phase"].value_counts())
        
        print(f"\nTop 10 Sponsors:")
        print(df["sponsor"].value_counts().head(10))
        
        print(f"\nTherapeutic Area Distribution:")
        print(df["therapeutic_area"].value_counts())
        
        print(f"\nRecruitment Status Distribution:")
        print(df["recruitment_status"].value_counts())
        
        print(f"\nIndia Verified Trials:")
        print(f"  Yes: {df['india_only_trial'].sum()}")
        print(f"  No: {(~df['india_only_trial']).sum()}")
        
        print(f"\nMissing Values:")
        missing = df.isnull().sum()
        print(missing[missing > 0])


def example_custom_cleaning():
    """
    Example 3: Custom cleaning with manual steps.
    
    Shows how to customize the cleaning process.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Custom Cleaning Steps")
    print("=" * 60)
    
    # Initialize cleaner
    cleaner = TrialDataCleaner()
    
    # Load raw data
    print("Loading raw data...")
    cleaner.load_raw_data()
    
    # Apply selective cleaning
    print("Removing duplicates...")
    cleaner.remove_duplicates()
    
    print("Standardizing phases...")
    cleaner.standardize_phase()
    
    print("Standardizing sponsors...")
    cleaner.standardize_sponsor_names()
    
    print("Extracting therapeutic areas...")
    cleaner.extract_therapeutic_area()
    
    print("Parsing dates...")
    cleaner.parse_dates()
    
    print("Creating trial duration...")
    cleaner.create_trial_duration()
    
    print("Validating India locations...")
    cleaner.validate_india_location()
    
    # Save
    output_file = cleaner.save_cleaned_data()
    
    if output_file:
        report = cleaner.get_cleaning_report()
        print_cleaning_report(report)


def example_compare_before_after():
    """
    Example 4: Compare raw vs cleaned data.
    
    Demonstrates the impact of cleaning operations.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Before & After Comparison")
    print("=" * 60)
    
    from src.ingestion import clinical_trials_api
    
    # Load raw data
    raw_file = Path(__file__).parent.parent.parent / "data" / "raw" / "india_trials_raw.csv"
    
    if raw_file.exists():
        print("\nLoading raw data...")
        raw_df = pd.read_csv(raw_file)
        
        print(f"\nRAW DATA:")
        print(f"  Shape: {raw_df.shape}")
        print(f"  Duplicate NCT IDs: {raw_df['nct_id'].duplicated().sum()}")
        print(f"  Missing phases: {raw_df['phase'].isna().sum()}")
        print(f"  Missing sponsors: {raw_df['sponsor'].isna().sum()}")
        
        # Clean
        cleaner = TrialDataCleaner()
        cleaned_df = cleaner.clean()
        
        print(f"\nCLEANED DATA:")
        print(f"  Shape: {cleaned_df.shape}")
        print(f"  Duplicate NCT IDs: {cleaned_df['nct_id'].duplicated().sum()}")
        print(f"  Missing phases: {cleaned_df['phase'].isna().sum()}")
        print(f"  Missing sponsors: {cleaned_df['sponsor'].isna().sum()}")
        print(f"  India verified: {cleaned_df['india_only_trial'].sum()}")
        
        print(f"\nIMPACT SUMMARY:")
        print(f"  Records removed: {len(raw_df) - len(cleaned_df)}")
        print(f"  Reduction: {(1 - len(cleaned_df)/len(raw_df)) * 100:.1f}%")
    
    else:
        print(f"Raw data file not found: {raw_file}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CLINICAL TRIALS DATA CLEANING - EXAMPLES")
    print("=" * 60)
    
    # Run examples (uncomment to execute)
    example_basic_cleaning()
    # example_inspect_data()
    # example_custom_cleaning()
    # example_compare_before_after()
    
    print("\n" + "=" * 60)
    print("Examples completed")
    print("=" * 60)
