"""
Generate realistic mock clinical trial data for India.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_clinical_trials_data(n_trials: int = 150) -> pd.DataFrame:
    """Generate realistic mock Indian clinical trials data."""
    
    np.random.seed(42)
    
    sponsors = [
        "Cipla Ltd", "Sun Pharmaceutical", "Dr. Reddy's Laboratories",
        "Lupin Limited", "Aurobindo Pharma", "Glenmark Pharmaceuticals",
        "Torrent Pharmaceuticals", "Cadila Healthcare", "Biocon Limited",
        "Mylan Pharmaceuticals", "Hetero Drugs", "Natco Pharma",
        "Apotex Inc", "Abbott India", "Pfizer India", "Merck Sharp & Dohme",
        "GlaxoSmithKline", "Novartis India", "Sanofi India", "Roche India"
    ]
    
    therapeutic_areas = [
        "Oncology", "Cardiology", "Respiratory", "Infectious Disease",
        "Gastroenterology", "Neurology", "Rheumatology", "Endocrinology",
        "Immunology", "Ophthalmology", "Dermatology", "Hepatology"
    ]
    
    phases = ["Phase I", "Phase II", "Phase III", "Phase IV"]
    
    recruitment_statuses = [
        "Recruiting", "Active, not recruiting", "Enrolling by invitation",
        "Completed", "Suspended", "Terminated"
    ]
    
    cities = [
        "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata",
        "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Chandigarh", "Kochi"
    ]
    
    states = [
        "Maharashtra", "Delhi", "Karnataka", "Telangana", "Tamil Nadu",
        "West Bengal", "Gujarat", "Rajasthan", "Uttar Pradesh", "Punjab",
        "Kerala", "Haryana"
    ]
    
    trials = []
    base_date = datetime(2020, 1, 1)
    
    for i in range(n_trials):
        start_date = base_date + timedelta(days=np.random.randint(0, 1800))
        duration_days = np.random.randint(90, 1095)
        completion_date = start_date + timedelta(days=duration_days)
        
        trial = {
            "nct_id": f"NCT{datetime.now().year % 100}{str(i).zfill(6)}",
            "sponsor": np.random.choice(sponsors),
            "therapeutic_area": np.random.choice(therapeutic_areas),
            "phase": np.random.choice(phases),
            "recruitment_status": np.random.choice(recruitment_statuses),
            "start_date": start_date,
            "completion_date": completion_date,
            "city": np.random.choice(cities),
            "state": np.random.choice(states),
            "enrollment": np.random.randint(20, 1000),
            "trial_duration_days": duration_days
        }
        trials.append(trial)
    
    df = pd.DataFrame(trials)
    df["is_active"] = df["recruitment_status"].isin(["Recruiting", "Active, not recruiting"])
    
    return df


def get_trial_statistics(df: pd.DataFrame) -> dict:
    """Calculate key statistics from trial data."""
    return {
        "total_trials": len(df),
        "active_trials": df["is_active"].sum(),
        "recruiting_trials": (df["recruitment_status"] == "Recruiting").sum(),
        "active_sponsors": df["sponsor"].nunique(),
        "avg_duration_days": df["trial_duration_days"].mean(),
        "most_active_area": df[df["is_active"]]["therapeutic_area"].value_counts().index[0]
            if df["is_active"].any() else df["therapeutic_area"].value_counts().index[0]
    }
