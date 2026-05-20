# Dashboard Refactoring - Real Data Integration

## Summary

The India Clinical Trials Intelligence Dashboard has been successfully refactored to load and use the real cleaned clinical trials dataset instead of mock data.

## Key Changes

### 1. New Data Loading Module (`src/data_loader.py`)

**Purpose**: Centralized, production-grade data loading with caching and validation.

**Features**:
- ✅ `@st.cache_data` decorator with 1-hour TTL
- ✅ File existence validation
- ✅ Empty file detection
- ✅ Schema validation (15 required columns)
- ✅ Automatic date parsing (ISO 8601)
- ✅ Year column extraction for filtering
- ✅ Comprehensive error handling with user-friendly messages
- ✅ File metadata (last modified, record count, timestamp)
- ✅ Logging to console and logs/data_loading.log

**Functions**:
- `load_clinical_trials_data()` - Load and validate CSV data
- `get_unique_values()` - Extract sorted unique values for filters
- `get_data_summary()` - Calculate statistics (KPIs)
- `apply_filters()` - Apply user-selected filters to dataset
- `validate_and_log_data()` - Quality checks and logging
- `clear_data_cache()` - Force data reload

**Input**: `data/processed/india_trials_clean.csv` (from cleaning pipeline)

**Output**: DataFrame with 15 columns + 2 derived columns (start_year, completion_year)

### 2. Refactored Main App (`app.py`)

#### Data Loading
```python
# OLD: Mock data generation
@st.cache_data
def load_trial_data():
    return generate_clinical_trials_data(n_trials=150)

# NEW: Real data loading with validation
df, metadata = load_clinical_trials_data()
if not validate_and_log_data(df, metadata):
    # Show error state with instructions
```

#### Error Handling
- Graceful error states for:
  - Missing data file (with troubleshooting steps)
  - Empty CSV
  - Invalid schema
  - Shows clear instructions to run ingestion/cleaning pipelines

#### Session State Management
```python
if "filters" not in st.session_state:
    st.session_state.filters = {
        "therapeutic_areas": [],
        "phases": [],
        "statuses": [],
        "sponsor": "All Sponsors",
        "states": [],
        "year_range": (2020, 2027)
    }
```

### 3. Sidebar Filters

**Added comprehensive filtering system:**

```
🔍 Global Filters (apply to all pages):
├── Therapeutic Areas (multiselect)
├── Trial Phases (multiselect)
├── Recruitment Status (multiselect)
├── Sponsor (single select)
├── States (multiselect)
├── Trial Start Year (range slider)
├── 🔄 Reset All Filters button
```

**Filter Persistence**: Filters maintained across page navigation via `st.session_state`

### 4. Data Refresh Controls

**Sidebar Controls**:
- `🔄 Refresh Data` button - Clears cache and reloads CSV
- `ℹ️ Data Info` button - Shows dataset status
- Dataset information display with:
  - Total records loaded
  - Last updated timestamp
  - File path

### 5. Dynamic KPIs

All KPIs now update based on applied filters:

**Overview Dashboard**:
- Total Active Trials (filtered)
- Active Sponsors (filtered)
- Recruiting Trials (filtered)
- Avg Trial Duration (filtered)
- Most Active Therapeutic Area (filtered)

**Other pages**: All metrics dynamically calculated from filtered dataset

### 6. All Dashboard Pages Updated

#### Overview Dashboard
- ✅ Uses filtered data for all metrics and charts
- ✅ Shows recruiting trial percentage
- ✅ Dynamic therapeutic area analysis

#### Sponsor Intelligence
- ✅ Filter-aware sponsor rankings
- ✅ Portfolio diversity calculations
- ✅ Dynamic sponsor detail table

#### Therapeutic Area Analysis
- ✅ Area count reflects filtered data
- ✅ Most recruiting area based on filters
- ✅ Phase distribution per therapeutic area

#### Geographic Analysis
- ✅ State/city distributions filtered
- ✅ State-wise trial details
- ✅ City rankings updated

#### Trial Explorer
- ✅ Local filters within page
- ✅ Enrollment range slider
- ✅ Multi-select filters
- ✅ Sponsor-specific filtering
- ✅ CSV export of filtered results

### 7. Error States

**User-Friendly Error Handling**:
```
⚠️ Error Loading Data
┌─────────────────────────────────────────┐
│ Error Details:                          │
│ • Issue description                     │
│ • Solution steps                        │
│                                         │
│ Quick Links:                            │
│ 1. Run API Ingestion                    │
│ 2. Run Data Cleaning                    │
│ 3. 🔄 Retry Loading Data               │
└─────────────────────────────────────────┘
```

### 8. Column Name Updates

**Updated all references from mock data columns to real data columns:**

| Old Column | New Column | Reason |
|-----------|-----------|--------|
| `enrollment` | `enrollment_count` | Real data from API |
| `is_active` | (calculated from `recruitment_status`) | More accurate |
| N/A | `trial_duration_days` | Derived in cleaning |
| N/A | `india_only_trial` | Validation from cleaning |
| N/A | `start_year` | Derived for filtering |
| N/A | `completion_year` | Derived for filtering |

## Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                  ClinicalTrials.gov API                 │
│              (via src/ingestion/clinical_trials_api.py) │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
            ┌──────────────────────┐
            │ data/raw/            │
            │ india_trials_raw.csv │
            └──────────────────────┘
                       │
                       ↓
        ┌─────────────────────────────────┐
        │ src/cleaning/clean_trials.py    │
        │ (Standardization & Cleaning)    │
        └─────────────────────────────────┘
                       │
                       ↓
            ┌──────────────────────┐
            │ data/processed/      │
            │ india_trials_clean.  │
            │ csv (15 cols)        │
            └──────────────────────┘
                       │
                       ↓
        ┌─────────────────────────────────┐
        │ src/data_loader.py              │
        │ (Load + Cache + Filter)         │
        └─────────────────────────────────┘
                       │
                       ↓
                ┌──────────────┐
                │ Streamlit    │
                │ Dashboard    │
                │ (app.py)     │
                └──────────────┘
```

## Testing

### Data Loader Test Results
```
✓ Data loaded successfully
  Records: 11
  Last modified: 2026-05-19 21:39:35
  
Summary Statistics:
  total_trials: 11
  recruiting_trials: 5
  active_trials: 5
  completed_trials: 1
  total_sponsors: 11
  total_areas: 11
  total_states: 10
  total_cities: 10
  avg_duration_days: 716
  total_enrollment: 1855
```

### Import Test Results
```
✓ All imports successful
✓ Data loaded: 11 records
✓ Columns: ['nct_id', 'brief_title', 'sponsor', 'phase', 'conditions']...
```

## Usage

### Starting the Dashboard

```bash
cd ~/clinical_trials_dashboard
source .venv/bin/activate
streamlit run app.py
```

Opens at: `http://localhost:8501`

### Refreshing Data

1. Run API ingestion:
   ```bash
   python -m src.ingestion.clinical_trials_api
   ```

2. Run data cleaning:
   ```bash
   python -m src.cleaning.clean_trials
   ```

3. In dashboard sidebar, click `🔄 Refresh Data`

### Using Filters

1. Use sidebar filters to narrow dataset
2. All pages update automatically
3. Click `🔄 Reset All Filters` to clear
4. Filters persist across page navigation

## Architecture Benefits

1. **Modularity**: Data loading separated from visualization
2. **Caching**: 1-hour TTL prevents excessive file reads
3. **Error Handling**: User-friendly messages for all failure modes
4. **Flexibility**: Easy to swap data sources (API, database, etc.)
5. **Testability**: Each component independently testable
6. **Scalability**: Ready for larger datasets (10k+ records)
7. **Production-Ready**: Logging, validation, error handling
8. **Dynamic**: All visualizations respond to filter changes

## Next Steps

### Immediate Enhancements
- [ ] Add real trial data (100+ records from API)
- [ ] Add unit tests for data_loader functions
- [ ] Add performance testing with larger datasets

### Future Enhancements
- [ ] Database integration (replace CSV)
- [ ] Real-time API sync (scheduled pipeline)
- [ ] User authentication
- [ ] Custom report generation
- [ ] Data export to PDF/Excel
- [ ] Trend analysis and forecasting

## File Structure

```
clinical_trials_dashboard/
├── app.py (REFACTORED - now uses real data)
├── src/
│   ├── config.py
│   ├── data_loader.py (NEW)
│   ├── visualizations.py
│   ├── ingestion/
│   │   ├── clinical_trials_api.py
│   │   └── validators.py
│   └── cleaning/
│       └── clean_trials.py
├── data/
│   ├── raw/
│   │   └── india_trials_raw.csv
│   └── processed/
│       └── india_trials_clean.csv ⬅️ Used by new app
├── logs/
│   ├── api_ingestion.log
│   ├── data_cleaning.log
│   └── data_loading.log
└── requirements.txt
```

## Version History

- **v2.0**: Original Streamlit dashboard with mock data
- **v2.1**: Real data integration with filtering and refresh controls (CURRENT)
- **v2.2**: (Planned) Database backend integration
