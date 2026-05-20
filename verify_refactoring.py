#!/usr/bin/env python
"""
Verification script for refactored dashboard.
Tests all components end-to-end.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_data_loader():
    """Test data loading module."""
    print("\n" + "="*60)
    print("TEST 1: Data Loader Module")
    print("="*60)
    
    from src.data_loader import (
        load_clinical_trials_data, 
        get_unique_values,
        get_data_summary,
        apply_filters
    )
    
    # Load data
    df, metadata = load_clinical_trials_data()
    
    if metadata.get("file_exists"):
        print(f"✓ Data file exists: {metadata['file_exists']}")
        print(f"✓ Records loaded: {metadata['record_count']}")
        print(f"✓ Last updated: {metadata['last_updated_timestamp']}")
        print(f"✓ Schema valid: {metadata['columns_valid']}")
    else:
        print(f"✗ Error: {metadata['error']}")
        return False
    
    if df is None or len(df) == 0:
        print("✗ No data returned")
        return False
    
    # Test summary
    summary = get_data_summary(df, metadata)
    print(f"\n✓ Summary Statistics:")
    print(f"  - Total trials: {summary['total_trials']}")
    print(f"  - Recruiting: {summary['recruiting_trials']}")
    print(f"  - Active sponsors: {summary['total_sponsors']}")
    print(f"  - Avg duration: {summary['avg_duration_days']} days")
    
    # Test unique values
    areas = get_unique_values(df, "therapeutic_area")
    print(f"\n✓ Therapeutic areas: {len(areas)} found")
    print(f"  Examples: {areas[:3]}")
    
    # Test filters
    filters = {
        "therapeutic_areas": [areas[0]] if len(areas) > 0 else [],
        "phases": [],
        "statuses": [],
        "sponsor": "All Sponsors",
        "states": [],
        "year_range": (2020, 2027)
    }
    filtered_df = apply_filters(df, filters)
    print(f"\n✓ Filters applied: {len(filtered_df)} records after filtering")
    
    return True


def test_visualizations():
    """Test visualization functions."""
    print("\n" + "="*60)
    print("TEST 2: Visualization Functions")
    print("="*60)
    
    from src.data_loader import load_clinical_trials_data
    from src.visualizations import (
        plot_trials_by_therapeutic_area,
        plot_phase_distribution,
        plot_recruitment_status,
        plot_geographic_distribution
    )
    
    df, metadata = load_clinical_trials_data()
    if df is None or len(df) == 0:
        print("✗ No data available")
        return False
    
    try:
        # Test each visualization
        charts = [
            ("Therapeutic Area", plot_trials_by_therapeutic_area),
            ("Phase Distribution", plot_phase_distribution),
            ("Recruitment Status", plot_recruitment_status),
            ("Geographic Distribution", plot_geographic_distribution),
        ]
        
        for name, func in charts:
            try:
                fig = func(df)
                print(f"✓ {name}: Generated successfully")
            except Exception as e:
                print(f"✗ {name}: {str(e)[:50]}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_data_columns():
    """Test data column mapping."""
    print("\n" + "="*60)
    print("TEST 3: Data Column Validation")
    print("="*60)
    
    from src.data_loader import load_clinical_trials_data, EXPECTED_COLUMNS
    
    df, metadata = load_clinical_trials_data()
    if df is None:
        print("✗ No data loaded")
        return False
    
    # Check expected columns
    loaded_cols = set(df.columns)
    missing = EXPECTED_COLUMNS - loaded_cols
    extra = loaded_cols - EXPECTED_COLUMNS
    
    if len(missing) == 0:
        print(f"✓ All {len(EXPECTED_COLUMNS)} expected columns present")
    else:
        print(f"✗ Missing columns: {missing}")
        return False
    
    # Check column usage in app
    required_for_app = {
        "nct_id", "sponsor", "therapeutic_area", "phase",
        "recruitment_status", "city", "state", "enrollment_count",
        "start_date", "completion_date"
    }
    
    missing_app = required_for_app - loaded_cols
    if len(missing_app) == 0:
        print(f"✓ All app-required columns available")
    else:
        print(f"✗ Missing app columns: {missing_app}")
        return False
    
    # Check derived columns
    if "start_year" in df.columns:
        print(f"✓ Derived column 'start_year' available")
    if "completion_year" in df.columns:
        print(f"✓ Derived column 'completion_year' available")
    
    return True


def test_config():
    """Test configuration module."""
    print("\n" + "="*60)
    print("TEST 4: Configuration Module")
    print("="*60)
    
    from src.config import (
        APP_TITLE, PROCESSED_DATA_DIR,
        THERAPEUTIC_AREAS, TRIAL_PHASES,
        RECRUITMENT_STATUSES, INDIAN_STATES
    )
    
    print(f"✓ App title: {APP_TITLE}")
    print(f"✓ Processed data dir: {PROCESSED_DATA_DIR}")
    print(f"✓ Therapeutic areas: {len(THERAPEUTIC_AREAS)} configured")
    print(f"✓ Trial phases: {len(TRIAL_PHASES)} configured")
    print(f"✓ Recruitment statuses: {len(RECRUITMENT_STATUSES)} configured")
    print(f"✓ Indian states: {len(INDIAN_STATES)} configured")
    
    return True


def test_file_structure():
    """Test project file structure."""
    print("\n" + "="*60)
    print("TEST 5: File Structure")
    print("="*60)
    
    required_files = [
        "app.py",
        "src/data_loader.py",
        "src/config.py",
        "src/visualizations.py",
        "src/cleaning/clean_trials.py",
        "src/ingestion/clinical_trials_api.py",
        "data/processed/india_trials_clean.csv",
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = PROJECT_ROOT / file_path
        exists = full_path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("INDIA CLINICAL TRIALS DASHBOARD")
    print("Refactoring Verification Suite")
    print("="*60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Configuration", test_config),
        ("Data Columns", test_data_columns),
        ("Data Loader", test_data_loader),
        ("Visualizations", test_visualizations),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n✗ Test '{name}' failed with error: {str(e)}")
            results[name] = False
    
    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All verification tests passed!")
        print("\n✅ Dashboard is ready for use:")
        print("   cd ~/clinical_trials_dashboard")
        print("   source .venv/bin/activate")
        print("   streamlit run app.py")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
