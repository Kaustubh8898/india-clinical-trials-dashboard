# Clinical Trials API Ingestion Module

Production-grade module for fetching clinical trial data from ClinicalTrials.gov API v2.

## Overview

The ingestion module provides a complete pipeline for:
- Fetching clinical trials from ClinicalTrials.gov API v2
- Filtering for trials with study locations in India
- Handling pagination, retries, and timeouts
- Validating and cleaning data
- Exporting to CSV format

## Architecture

### Core Components

**`clinical_trials_api.py`**
- `ClinicalTrialsAPIClient`: Main API client class
- Retry logic with exponential backoff
- Automatic pagination handling
- Comprehensive error handling and logging
- Rate limiting to be respectful to the API

**`validators.py`**
- `TrialValidator`: Record-level validation
- Data cleaning functions
- DataFrame validation utilities
- Quality checks on clinical trial data

## Installation

### Prerequisites

```bash
pip install requests pandas
```

All dependencies are included in `requirements.txt`.

## Usage

### Method 1: Run as Standalone Module

```bash
cd ~/clinical_trials_dashboard
source .venv/bin/activate
python -m src.ingestion.clinical_trials_api
```

This will:
1. Fetch all Indian clinical trials from ClinicalTrials.gov
2. Extract and parse the data
3. Save to `data/raw/india_trials_raw.csv`
4. Generate a summary report

### Method 2: Import as Python Module

```python
from src.ingestion.clinical_trials_api import (
    ClinicalTrialsAPIClient,
    extract_trial_record,
    save_trials_to_csv
)

# Initialize client
client = ClinicalTrialsAPIClient(page_size=100)

# Fetch trials
studies = client.fetch_india_trials()

# Process studies
trials = [extract_trial_record(study) for study in studies]

# Save to CSV
output_file = save_trials_to_csv(trials)

client.close()
```

### Method 3: With Validation and Cleaning

```python
from src.ingestion.clinical_trials_api import ClinicalTrialsAPIClient, extract_trial_record
from src.ingestion.validators import TrialValidator, clean_trial_data

# Fetch
client = ClinicalTrialsAPIClient()
studies = client.fetch_india_trials()

# Extract
trials = [extract_trial_record(study) for study in studies]

# Validate
validator = TrialValidator()
valid, invalid = validator.validate_batch(trials)
print(f"Valid: {valid}, Invalid: {invalid}")

# Clean
clean_trials = clean_trial_data(trials)

client.close()
```

## API Configuration

Edit configuration constants in `clinical_trials_api.py`:

```python
API_BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
DEFAULT_PAGE_SIZE = 100  # Records per API page
MAX_RETRIES = 3          # Retry attempts
RETRY_DELAY = 2          # Seconds between retries
REQUEST_TIMEOUT = 30     # Request timeout in seconds
```

## Data Fields Extracted

| Field | Description | Source |
|-------|-------------|--------|
| `nct_id` | Trial ID (e.g., NCT04234567) | Identification |
| `brief_title` | Trial title | Identification |
| `sponsor` | Sponsoring organization | Identification |
| `phase` | Trial phase (I-IV) | Design |
| `conditions` | Conditions being studied | Conditions Module |
| `recruitment_status` | Current recruitment status | Status |
| `start_date` | Trial start date (ISO format) | Status |
| `completion_date` | Trial completion date (ISO format) | Status |
| `enrollment_count` | Target enrollment number | Recruitment |
| `city` | Study location city | Locations |
| `state` | Study location state | Locations |
| `country` | Study location country (India) | Locations |
| `fetched_date` | Data fetch timestamp | System |

## Output Format

### CSV Output

Saved to: `data/raw/india_trials_raw.csv`

```
nct_id,brief_title,sponsor,phase,conditions,recruitment_status,start_date,completion_date,enrollment_count,city,state,country,fetched_date
NCT04234567,Study Title,Sponsor Inc.,Phase 2,Condition1; Condition2,Recruiting,2023-01-15,2024-12-31,200,Mumbai,Maharashtra,India,2024-05-19T20:30:45.123456
```

## Error Handling

### Automatic Retries

The client automatically retries failed requests with exponential backoff:

```python
# Connection error → retry after 2 seconds
# Timeout → retry after 2 seconds
# HTTP 5xx → retry (not 4xx)
```

### Logging

All operations are logged to:
- **Console**: Real-time status messages
- **File**: `logs/api_ingestion.log`

### Failed Requests Tracking

```python
client.failed_requests  # List of failed requests with error details
```

## Examples

See `examples/api_ingestion_examples.py` for:
- Basic fetch and save
- Fetch with validation
- Partial fetch (for testing)
- Error handling demonstrations

Run examples:
```bash
python examples/api_ingestion_examples.py
```

## Performance Considerations

### Rate Limiting
- Built-in 0.5s delay between pages
- Respects ClinicalTrials.gov API guidelines
- Typical fetch: 150 trials ≈ 2-3 minutes

### Pagination
- Automatic handling of API pagination tokens
- Configurable page size (default: 100 records)
- Handles empty result sets gracefully

### Memory
- Processes studies incrementally
- Scales to 1000+ trials without issues

## Troubleshooting

### Connection Errors
```
WARNING: Connection error - Retrying...
```
**Solution**: Check internet connection, retry later

### Timeouts
```
WARNING: Request timeout - Retrying...
```
**Solution**: Increase `REQUEST_TIMEOUT` in config

### Empty Results
```
ERROR: No trials fetched from API
```
**Solution**: Verify India location filter in API params

### Invalid JSON Response
```
ERROR: JSON decode error
```
**Solution**: API may be temporarily unavailable, retry later

## API Limits

- **Rate Limit**: Reasonable usage (implemented via pagination delays)
- **Record Limit**: None (pagination handles all available data)
- **Timeout**: 30 seconds per request

## Development

### Running Tests

```bash
pytest tests/test_ingestion.py -v
```

### Code Quality

```bash
flake8 src/ingestion/
pylint src/ingestion/
```

## Support

For issues or feature requests:
1. Check logs in `logs/api_ingestion.log`
2. Review failed requests in client output
3. Verify API endpoint status: https://clinicaltrials.gov/api/v2/studies

## License

Proprietary - Clinical Trials Analytics Dashboard

## References

- ClinicalTrials.gov API Docs: https://clinicaltrials.gov/api/v2
- NCT ID Format: https://www.nlm.nih.gov/nct/
- Clinical Trial Phases: https://www.fda.gov/patients/lesson-clinical-trials
