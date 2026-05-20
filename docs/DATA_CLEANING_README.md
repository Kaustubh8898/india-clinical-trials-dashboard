# Data Cleaning Module Documentation

Production-grade data cleaning and standardization module for clinical trial datasets.

## Overview

The `clean_trials.py` module provides comprehensive data quality management for clinical trial records:
- Duplicate removal
- Text standardization
- Date parsing and validation
- Geographic normalization
- Therapeutic area categorization
- Feature engineering
- Missing value handling

## Architecture

### Core Class: `TrialDataCleaner`

Main class for orchestrating the data cleaning pipeline.

```python
from src.cleaning.clean_trials import TrialDataCleaner

cleaner = TrialDataCleaner()
cleaned_df = cleaner.clean()
output_file = cleaner.save_cleaned_data()
```

## Cleaning Operations

### 1. Duplicate Removal

Removes duplicate trials based on NCT ID, keeping the first occurrence.

```python
cleaner.remove_duplicates()
```

**Operation**:
- Identifies duplicate `nct_id` values
- Keeps first occurrence
- Reports number of duplicates removed

### 2. Phase Standardization

Normalizes trial phase values to standard format.

**Input Formats** → **Output**:
- "Phase 1", "Phase I", "1" → "Phase 1"
- "Phase 2", "Phase II", "2" → "Phase 2"
- "Phase 3", "Phase III", "3" → "Phase 3"
- "Phase 4", "Phase IV", "4" → "Phase 4"
- "Not Applicable", "N/A", "" → "Unknown"

```python
cleaner.standardize_phase()
```

### 3. Recruitment Status Standardization

Normalizes recruitment status values.

**Supported Status Values**:
- "Recruiting"
- "Active, not recruiting"
- "Enrolling by invitation"
- "Not yet recruiting"
- "Suspended"
- "Terminated"
- "Completed"
- "Withdrawn"
- "Unknown"

```python
cleaner.standardize_recruitment_status()
```

### 4. Sponsor Name Standardization

Cleans and standardizes sponsor organization names.

**Operations**:
- Removes common suffixes (Inc., Ltd., LLC, Corp., etc.)
- Normalizes whitespace
- Converts invalid entries to "Unknown"

```python
cleaner.standardize_sponsor_names()
```

**Example**:
- "Cipla Inc." → "Cipla"
- "Dr. Reddy's Laboratories Ltd." → "Dr. Reddy's Laboratories"

### 5. Therapeutic Area Extraction

Maps condition keywords to standardized therapeutic areas.

**Supported Areas**:
- **Oncology**: cancer, tumor, malignancy
- **Cardiology**: heart, cardiac, cardiovascular, hypertension
- **Respiratory**: lung, asthma, COPD, bronchi
- **Infectious Disease**: infection, COVID, HIV, tuberculosis
- **Gastroenterology**: gastro, digestive
- **Hepatology**: liver, hepatic
- **Neurology**: brain, Parkinson's, Alzheimer's, epilepsy
- **Rheumatology**: joint, arthritis
- **Endocrinology**: diabetes, thyroid, metabolic
- **Immunology**: immune, autoimmune
- **Ophthalmology**: eye, vision
- **Dermatology**: skin, psoriasis
- **Other**: unmapped conditions

```python
cleaner.extract_therapeutic_area()
```

### 6. Date Parsing

Parses start_date and completion_date to datetime format.

```python
cleaner.parse_dates()
```

**Format**: ISO 8601 (YYYY-MM-DD)

### 7. Trial Duration Calculation

Creates `trial_duration_days` column from date fields.

```python
cleaner.create_trial_duration()
```

**Calculation**: `completion_date - start_date` (in days)

### 8. Geographic Normalization

Normalizes city, state, and country text.

**Operations**:
- Title case formatting
- Removes extra whitespace
- Validates Indian states

```python
cleaner.normalize_geographic_data()
```

### 9. India Location Validation

Creates `india_only_trial` boolean column.

```python
cleaner.validate_india_location()
```

**Validation**: Checks if state is in list of 28 Indian states/territories.

### 10. Missing Value Handling

Reports and tracks missing values.

```python
cleaner.handle_missing_values()
```

## Usage Examples

### Basic Cleaning

```python
from src.cleaning.clean_trials import TrialDataCleaner

# Initialize
cleaner = TrialDataCleaner()

# Run complete cleaning pipeline
cleaned_df = cleaner.clean()

# Save cleaned data
output_file = cleaner.save_cleaned_data()

# Get report
report = cleaner.get_cleaning_report()
```

### Custom Cleaning Steps

```python
cleaner = TrialDataCleaner()
cleaner.load_raw_data()
cleaner.remove_duplicates()
cleaner.standardize_phase()
cleaner.standardize_sponsor_names()
# ... additional steps
cleaner.save_cleaned_data()
```

### Inspect Cleaned Data

```python
import pandas as pd

# Load cleaned CSV
df = pd.read_csv("data/processed/india_trials_clean.csv")

# View phase distribution
print(df["phase"].value_counts())

# View therapeutic areas
print(df["therapeutic_area"].value_counts())

# Check data types
print(df.dtypes)
```

### Generate Report

```python
from src.cleaning.clean_trials import print_cleaning_report

report = cleaner.get_cleaning_report()
print_cleaning_report(report)
```

## Output Schema

### Cleaned DataFrame Columns

| Column | Type | Description |
|--------|------|-------------|
| `nct_id` | string | Trial identifier (unique) |
| `brief_title` | string | Trial title |
| `sponsor` | string | Sponsoring organization (standardized) |
| `phase` | string | Trial phase (standardized) |
| `conditions` | string | Medical conditions being studied |
| `therapeutic_area` | string | Mapped therapeutic category |
| `recruitment_status` | string | Current recruitment status (standardized) |
| `start_date` | datetime | Trial start date (ISO format) |
| `completion_date` | datetime | Trial completion date (ISO format) |
| `trial_duration_days` | int64 | Duration in days (derived) |
| `enrollment_count` | int64 | Target enrollment number |
| `city` | string | Study location city (normalized) |
| `state` | string | Study location state (normalized) |
| `country` | string | Study location country |
| `india_only_trial` | bool | Is valid India location? |
| `fetched_date` | string | Data fetch timestamp |

### Output File

**Location**: `data/processed/india_trials_clean.csv`

**Format**: CSV with UTF-8 encoding

**Size**: ~150-500 records (depending on source)

## Data Quality Metrics

### Report Contents

```python
{
    "original_row_count": 150,
    "final_row_count": 145,
    "rows_removed": 5,
    "cleaned_at": "2024-05-19T20:30:45.123456",
    "cleaning_details": {
        "duplicates_removed": 5,
        "phase_distribution": {...},
        "status_distribution": {...},
        "top_sponsors": {...},
        "therapeutic_areas": {...},
        "avg_trial_duration_days": 450.5,
        "india_verified_count": 143,
        "missing_values": {...}
    }
}
```

## Logging

### Log Locations

1. **Console Output**: Real-time status and warnings
2. **File**: `logs/data_cleaning.log`

### Log Levels

- **INFO**: Operation progress and statistics
- **WARNING**: Data quality issues (missing values, parse errors)
- **ERROR**: Failures and exceptions

## Running the Module

### As Standalone Script

```bash
cd ~/clinical_trials_dashboard
source .venv/bin/activate
python -m src.cleaning.clean_trials
```

Output:
```
============================================================
STARTING DATA CLEANING PIPELINE
============================================================
Loaded 150 rows from data/raw/india_trials_raw.csv
Removed 5 duplicate NCT IDs
...
============================================================
DATA CLEANING PIPELINE COMPLETED
============================================================

✓ Cleaning completed successfully
✓ Output file: data/processed/india_trials_clean.csv
```

### As Python Module

```python
from src.cleaning.clean_trials import main

exit_code = main()  # Returns 0 on success, 1 on error
```

### Via Import

```python
from src.cleaning import TrialDataCleaner

cleaner = TrialDataCleaner()
df = cleaner.clean()
```

## Examples

See `examples/cleaning_examples.py` for comprehensive examples:

1. **Basic cleaning** - Complete workflow
2. **Data inspection** - Post-cleaning analysis
3. **Custom steps** - Selective operations
4. **Before/after** - Impact comparison

Run examples:
```bash
python examples/cleaning_examples.py
```

## Performance

### Execution Time
- ~100 records: <1 second
- ~1000 records: 1-2 seconds
- ~10,000 records: 5-10 seconds

### Memory Usage
- Scales linearly with record count
- Typical usage: <100MB for standard datasets

## Standardization Maps

### Supported Mappings

The module includes comprehensive standardization maps for:
- Trial phases (4 formats each)
- Recruitment statuses (9 values)
- Therapeutic areas (40+ keywords)
- Indian states (28 states/territories)
- Major Indian cities (25+ cities)

### Extensibility

To add new standardizations:

```python
# In clinical_trials_api.py

NEW_MAPPING = {
    "old_value_1": "standardized_value_1",
    "old_value_2": "standardized_value_2",
}

def standardize_new_field(self):
    def normalize(value):
        return NEW_MAPPING.get(str(value).lower(), value)
    self.df["field"] = self.df["field"].apply(normalize)
```

## Troubleshooting

### File Not Found

```
ERROR: Input file not found: data/raw/india_trials_raw.csv
```

**Solution**: Run API ingestion first to generate raw data

### Date Parse Errors

```
WARNING: Could not parse X dates in start_date
```

**Solution**: Verify date format is ISO 8601 (YYYY-MM-DD)

### Missing Geographic Data

```
WARNING: No therapeutic_area values extracted
```

**Solution**: Verify conditions column contains data

## API Reference

### TrialDataCleaner Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `load_raw_data()` | DataFrame | Load raw CSV file |
| `remove_duplicates()` | None | Remove duplicate NCT IDs |
| `standardize_phase()` | None | Normalize phase values |
| `standardize_recruitment_status()` | None | Normalize status values |
| `standardize_sponsor_names()` | None | Clean sponsor names |
| `extract_therapeutic_area()` | None | Map conditions to areas |
| `parse_dates()` | None | Parse date columns |
| `create_trial_duration()` | None | Calculate duration |
| `normalize_geographic_data()` | None | Normalize text fields |
| `validate_india_location()` | None | Add India verification |
| `handle_missing_values()` | None | Report missing data |
| `convert_data_types()` | None | Convert to proper types |
| `clean()` | DataFrame | Execute full pipeline |
| `save_cleaned_data()` | Path | Save to CSV file |
| `get_cleaning_report()` | Dict | Get statistics |

## Support

For issues:
1. Check `logs/data_cleaning.log`
2. Review cleaning report output
3. Verify raw data format
4. Ensure all dependencies installed

## References

- Clinical Trial Phases: https://www.fda.gov/patients/lesson-clinical-trials
- NCT ID Format: https://www.nlm.nih.gov/nct/
- ISO 8601 Dates: https://en.wikipedia.org/wiki/ISO_8601
