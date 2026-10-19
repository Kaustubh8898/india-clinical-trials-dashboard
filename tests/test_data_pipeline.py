from pathlib import Path

import pandas as pd
import pytest

from src.cleaning.clean_trials import TrialDataCleaner
from src.data_loader import apply_filters, get_data_summary
from src.ingestion.clinical_trials_api import (
    extract_trial_record,
    normalize_api_phase,
    normalize_api_status,
    save_trials_to_csv,
)


def _study_fixture():
    return {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT12345678",
                "briefTitle": "Example study",
            },
            "sponsorCollaboratorsModule": {
                "leadSponsor": {"name": "Example University"}
            },
            "statusModule": {
                "overallStatus": "ACTIVE_NOT_RECRUITING",
                "startDateStruct": {"date": "2022-01-01"},
                "completionDateStruct": {"date": "2024-12"},
            },
            "designModule": {
                "phases": ["PHASE3"],
                "enrollmentInfo": {"count": 120},
            },
            "conditionsModule": {"conditions": ["Condition A", "Condition B"]},
            "contactsLocationsModule": {
                "locations": [
                    {"city": "Pune", "state": "Maharashtra", "country": "India"},
                    {"city": "Boston", "state": "Massachusetts", "country": "United States"},
                    {"city": "Mumbai", "state": "Maharashtra", "country": "India"},
                ]
            },
        }
    }


def test_api_enum_normalization():
    assert normalize_api_status("ACTIVE_NOT_RECRUITING") == "Active, not recruiting"
    assert normalize_api_status("NOT_YET_RECRUITING") == "Not yet recruiting"
    assert normalize_api_phase("PHASE3") == "Phase 3"
    assert normalize_api_phase("EARLY_PHASE1") == "Early Phase 1"


def test_extract_trial_record_keeps_source_and_indian_site_count():
    record = extract_trial_record(_study_fixture())
    assert record["nct_id"] == "NCT12345678"
    assert record["sponsor"] == "Example University"
    assert record["phase"] == "Phase 3"
    assert record["recruitment_status"] == "Active, not recruiting"
    assert record["enrollment_count"] == 120
    assert record["city"] == "Pune"
    assert record["india_site_count"] == 2
    assert record["data_source"] == "ClinicalTrials.gov API v2"
    assert record["source_url"] == "https://clinicaltrials.gov/study/NCT12345678"


def test_save_csv_deduplicates_and_rejects_bad_ids(tmp_path):
    output = tmp_path / "trials.csv"
    record = {"nct_id": "NCT12345678", "brief_title": "One"}
    saved = save_trials_to_csv([record, record.copy()], output)
    assert saved == output
    assert len(pd.read_csv(output)) == 1

    with pytest.raises(ValueError, match="invalid NCT ID"):
        save_trials_to_csv([{"nct_id": "DEMO-0001"}], tmp_path / "bad.csv")


def test_cleaner_tracks_precision_before_calculating_duration():
    cleaner = TrialDataCleaner(input_file=Path("not-used.csv"))
    cleaner.df = pd.DataFrame({
        "start_date": ["2022-01-01", "2022"],
        "completion_date": ["2023-01-01", "2023-12"],
    })

    cleaner.parse_dates()
    cleaner.create_trial_duration()

    assert cleaner.df.loc[0, "start_date_precision"] == "day"
    assert cleaner.df.loc[0, "trial_duration_days"] == 365
    assert cleaner.df.loc[1, "start_date_precision"] == "year"
    assert pd.isna(cleaner.df.loc[1, "trial_duration_days"])


def test_cleaner_marks_presence_of_indian_site_not_india_only():
    cleaner = TrialDataCleaner(input_file=Path("not-used.csv"))
    cleaner.df = pd.DataFrame({
        "country": ["India", "United States"],
        "state": [None, "Massachusetts"],
        "india_site_count": [2, 0],
    })

    cleaner.validate_india_location()
    assert cleaner.df["has_indian_location"].tolist() == [True, False]


def test_summary_uses_active_sponsors_and_active_area():
    frame = pd.DataFrame({
        "nct_id": ["NCT12345678", "NCT12345679", "NCT12345680", "NCT12345681"],
        "brief_title": ["A", "B", "C", "D"],
        "sponsor": ["Acme", "Acme", "Beta", "Gamma"],
        "phase": ["Phase 3", "Phase 2", "Phase 1", "Unknown"],
        "conditions": ["c1", "c2", "c3", "c4"],
        "recruitment_status": ["Recruiting", "Active, not recruiting", "Completed", "Enrolling by invitation"],
        "start_date": pd.to_datetime(["2022-01-01"] * 4),
        "completion_date": pd.to_datetime(["2023-01-01"] * 4),
        "enrollment_count": [5, 10, 20, None],
        "city": ["Pune", "Mumbai", "Delhi", "Chennai"],
        "state": ["Maharashtra", "Maharashtra", "Delhi", "Tamil Nadu"],
        "country": ["India"] * 4,
        "fetched_date": ["2026-01-01"] * 4,
        "therapeutic_area": ["Oncology", "Oncology", "Cardiology", "Other"],
        "trial_duration_days": [365, 730, None, None],
        "has_indian_location": [True] * 4,
        "start_year": [2022] * 4,
    })

    summary = get_data_summary(frame)
    assert summary["total_trials"] == 4
    assert summary["active_trials"] == 3
    assert summary["recruiting_trials"] == 1
    assert summary["total_sponsors"] == 3
    assert summary["active_sponsors"] == 2
    assert summary["most_active_area"] == "Oncology"
    assert summary["avg_duration_days"] == 548
    assert summary["total_enrollment"] == 35


def test_filters_apply_year_and_sponsor():
    frame = pd.DataFrame({
        "therapeutic_area": ["Oncology", "Cardiology"],
        "phase": ["Phase 3", "Phase 2"],
        "recruitment_status": ["Recruiting", "Completed"],
        "sponsor": ["Acme", "Beta"],
        "state": ["Maharashtra", "Delhi"],
        "start_year": [2022, 2024],
    })
    result = apply_filters(frame, {
        "therapeutic_areas": ["Oncology"],
        "phases": [],
        "statuses": [],
        "sponsor": "Acme",
        "states": [],
        "year_range": (2021, 2023),
    })
    assert len(result) == 1
    assert result.iloc[0]["sponsor"] == "Acme"


def test_unknown_sponsor_is_not_counted_as_a_distinct_sponsor():
    frame = pd.DataFrame({
        "sponsor": ["Acme", "Unknown"],
        "recruitment_status": ["Recruiting", "Recruiting"],
        "therapeutic_area": ["Oncology", "Oncology"],
        "state": ["Maharashtra", "Delhi"],
        "city": ["Pune", "Delhi"],
        "trial_duration_days": [100, 200],
        "enrollment_count": [10, 20],
    })
    summary = get_data_summary(frame)
    assert summary["total_sponsors"] == 1
    assert summary["active_sponsors"] == 1

def test_fetch_rejects_incomplete_pagination(monkeypatch):
    client = ClinicalTrialsAPIClient(page_size=1)
    first_page = {"totalCount": 2, "studies": [_study_fixture()]}
    monkeypatch.setattr(client, "_make_request", lambda params: first_page)
    try:
        with pytest.raises(RuntimeError, match="Expected 2 studies"):
            client.fetch_india_trials()
    finally:
        client.close()


def test_cleaner_preserves_legal_suffixes_in_sponsor_names():
    cleaner = TrialDataCleaner(input_file=Path("not-used.csv"))
    cleaner.df = pd.DataFrame({"sponsor": ["Example Ltd.", "  Example   Ltd.  "]})
    cleaner.standardize_sponsor_names()
    assert cleaner.df["sponsor"].tolist() == ["Example Ltd.", "Example Ltd."]
