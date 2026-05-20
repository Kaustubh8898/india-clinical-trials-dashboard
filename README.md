# Clinical Trials Analytics Dashboard

A Python-based Streamlit application for analyzing and visualizing clinical trial data. This dashboard provides interactive visualizations, cohort analysis, and key performance metrics for clinical trial oversight.

## Features

- **Interactive Dashboard**: Real-time metrics and visualizations
- **Cohort Analysis**: Patient segmentation and demographic breakdowns
- **Data Ingestion**: Support for CSV and Excel file uploads
- **KPI Tracking**: Key performance indicators with drill-down capabilities
- **Production-Ready**: Modular, scalable architecture with configuration management

## Project Structure

```
.
├── app.py                    # Streamlit app entry point
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── src/
│   ├── config.py            # Configuration constants
│   ├── ingestion/           # Data loading scripts
│   ├── cleaning/            # Data cleaning utilities
│   ├── analytics/           # Analysis modules
│   ├── visualization/       # Plotly charts
│   └── utils/               # Helper functions
├── data/
│   ├── raw/                 # Original datasets
│   └── processed/           # Cleaned data
└── tests/                   # Unit tests
```

## Getting Started

### Prerequisites

- Python 3.9+
- pip or conda

### Installation

1. Clone or create the project folder:
```bash
cd clinical_trials_dashboard
```

2. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Dashboard

```bash
streamlit run app.py
```

The app will launch at `http://localhost:8501`

## Configuration

Edit `src/config.py` to customize:
- App title and branding
- Default data paths
- API endpoints
- Visualization themes

## Development

### Adding a New Analysis Module

1. Create a Python file in `src/analytics/`
2. Import in `app.py`
3. Add a corresponding sidebar navigation entry
4. Use `src/config.py` for constants

### Running Tests

```bash
pytest tests/
```

## Deployment

For production deployment:
1. Set up environment variables in `.env`
2. Use `streamlit config.toml` for Streamlit settings
3. Deploy via Streamlit Cloud, Docker, or AWS

## License

Proprietary - Clinical Trials Analytics
