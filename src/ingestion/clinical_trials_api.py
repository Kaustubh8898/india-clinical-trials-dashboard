"""
ClinicalTrials.gov API v2 ingestion for India-located studies.

The API response is nested JSON. This module converts the fields needed by the
dashboard into one row per study and records how many Indian sites were found.
The city/state columns represent the first listed Indian site; site-level
analysis should use a separate one-row-per-site table.
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "api_ingestion.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

API_BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
DEFAULT_PAGE_SIZE = 1000  # ClinicalTrials.gov API v2 supports up to 1,000.
MAX_RETRIES = 3
RETRY_DELAY = 2
REQUEST_TIMEOUT = 30
DATA_OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_FILENAME = "india_trials_raw.csv"
DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# API field names (not the nested JSON paths).
API_FIELDS = ",".join(
    [
        "NCTId",
        "BriefTitle",
        "LeadSponsorName",
        "OverallStatus",
        "Phase",
        "Condition",
        "StartDate",
        "CompletionDate",
        "EnrollmentCount",
        "LocationCity",
        "LocationState",
        "LocationCountry",
    ]
)

STATUS_LABELS = {
    "RECRUITING": "Recruiting",
    "NOT_YET_RECRUITING": "Not yet recruiting",
    "ACTIVE_NOT_RECRUITING": "Active, not recruiting",
    "ENROLLING_BY_INVITATION": "Enrolling by invitation",
    "COMPLETED": "Completed",
    "SUSPENDED": "Suspended",
    "TERMINATED": "Terminated",
    "WITHDRAWN": "Withdrawn",
    "UNKNOWN": "Unknown",
    "NO_LONGER_AVAILABLE": "No longer available",
    "AVAILABLE": "Available",
    "TEMPORARILY_NOT_AVAILABLE": "Temporarily not available",
}

PHASE_LABELS = {
    "EARLY_PHASE1": "Early Phase 1",
    "PHASE1": "Phase 1",
    "PHASE2": "Phase 2",
    "PHASE3": "Phase 3",
    "PHASE4": "Phase 4",
    "NA": "Not Applicable",
}


def normalize_api_status(value: Any) -> str:
    """Convert API enum values into consistent display labels."""
    if value is None or pd.isna(value):
        return "Unknown"
    key = str(value).strip().upper().replace(" ", "_").replace(",", "")
    # API enum ACTIVE_NOT_RECRUITING is the canonical form.
    return STATUS_LABELS.get(key, str(value).strip().replace("_", " ").title())


def normalize_api_phase(value: Any) -> str:
    """Convert API phase enum values into readable labels."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "Unknown"
    key = str(value).strip().upper().replace(" ", "")
    return PHASE_LABELS.get(key, str(value).strip().title() or "Unknown")


class ClinicalTrialsAPIClient:
    """Small, retrying client for the public ClinicalTrials.gov API v2."""

    def __init__(
        self,
        base_url: str = API_BASE_URL,
        page_size: int = DEFAULT_PAGE_SIZE,
        max_retries: int = MAX_RETRIES,
        retry_delay: int = RETRY_DELAY,
        timeout: int = REQUEST_TIMEOUT,
    ) -> None:
        if not 1 <= page_size <= 1000:
            raise ValueError("page_size must be between 1 and 1000")
        self.base_url = base_url
        self.page_size = page_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept": "application/json", "User-Agent": "india-clinical-trials-dashboard/2.2"}
        )
        self.total_records_fetched = 0
        self.failed_requests: List[Dict[str, Any]] = []

    def _make_request(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """GET one API page with bounded retries for transient failures."""
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(
                    self.base_url, params=params, timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                retryable = status == 429 or (status is not None and status >= 500)
                logger.warning("HTTP error %s on attempt %s", status, attempt + 1)
                if not retryable or attempt >= self.max_retries:
                    self.failed_requests.append(
                        {"params": params.copy(), "error": f"HTTP {status}"}
                    )
                    return None
            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                json.JSONDecodeError,
            ) as exc:
                logger.warning("Transient API error on attempt %s: %s", attempt + 1, exc)
                if attempt >= self.max_retries:
                    self.failed_requests.append(
                        {"params": params.copy(), "error": str(exc)}
                    )
                    return None
            except requests.exceptions.RequestException as exc:
                self.failed_requests.append(
                    {"params": params.copy(), "error": str(exc)}
                )
                return None

            time.sleep(self.retry_delay * (attempt + 1))

        return None

    def fetch_india_trials(self) -> List[Dict[str, Any]]:
        """
        Fetch every page matching an Indian study location.

        If any page fails, raise an error rather than silently returning a
        partial dataset and presenting it as complete.
        """
        all_trials: List[Dict[str, Any]] = []
        page_token: Optional[str] = None
        expected_total: Optional[int] = None
        page_number = 1

        while True:
            params: Dict[str, Any] = {
                "pageSize": self.page_size,
                "filter.advanced": 'AREA[LocationCountry]"India"',
                "fields": API_FIELDS,
                "format": "json",
                "countTotal": "true",
            }
            if page_token:
                params["pageToken"] = page_token
                params.pop("countTotal", None)

            response = self._make_request(params)
            if response is None:
                raise RuntimeError(
                    f"ClinicalTrials.gov request failed on page {page_number}; "
                    "the existing dataset was not replaced."
                )

            studies = response.get("studies", [])
            if page_number == 1 and response.get("totalCount") is not None:
                expected_total = int(response["totalCount"])
                logger.info("API reports %s matching records", expected_total)

            all_trials.extend(studies)
            self.total_records_fetched += len(studies)
            logger.info("Fetched %s records on page %s", len(studies), page_number)

            page_token = response.get("nextPageToken")
            if not page_token:
                break
            page_number += 1
            time.sleep(0.2)

        if not all_trials:
            raise RuntimeError(
                "The API returned no studies with Indian locations. "
                "The existing dataset was not replaced."
            )

        # Do not replace a previous snapshot when paging returned an incomplete
        # result set or the API unexpectedly repeated/missed a study identifier.
        nct_ids = [
            study.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
            for study in all_trials
        ]
        if any(not nct_id for nct_id in nct_ids):
            raise RuntimeError("At least one API result is missing its NCT ID.")
        if len(set(nct_ids)) != len(nct_ids):
            raise RuntimeError("API pagination returned duplicate NCT IDs.")
        if expected_total is not None and len(all_trials) != expected_total:
            raise RuntimeError(
                f"Expected {expected_total} studies from API totalCount, but fetched "
                f"{len(all_trials)}. The existing dataset was not replaced."
            )

        logger.info("Fetched %s study records in total", len(all_trials))
        return all_trials

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()


def parse_study_locations(study_data: Dict[str, Any]) -> Dict[str, Any]:
    """Return the first listed Indian site and the number of Indian sites."""
    protocol = study_data.get("protocolSection", {})
    locations = (
        protocol.get("contactsLocationsModule", {}).get("locations", []) or []
    )
    india_locations = [
        location
        for location in locations
        if str(location.get("country", "")).strip().casefold() == "india"
    ]

    selected = india_locations[0] if india_locations else {}
    return {
        "city": selected.get("city"),
        "state": selected.get("state"),
        "country": selected.get("country") or ("India" if india_locations else None),
        "india_site_count": len(india_locations),
    }


def extract_trial_record(study: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a ClinicalTrials.gov v2 study object into a dashboard record."""
    protocol = study.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    design = protocol.get("designModule", {})
    conditions_module = protocol.get("conditionsModule", {})
    sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
    lead_sponsor = sponsor_module.get("leadSponsor", {}) or {}
    enrollment_info = design.get("enrollmentInfo", {}) or {}
    locations = parse_study_locations(study)

    phases = design.get("phases") or []
    conditions = conditions_module.get("conditions") or []

    return {
        "nct_id": identification.get("nctId"),
        "brief_title": identification.get("briefTitle"),
        "sponsor": lead_sponsor.get("name"),
        "phase": normalize_api_phase(phases[0] if phases else None),
        "conditions": "; ".join(str(item) for item in conditions),
        "recruitment_status": normalize_api_status(status.get("overallStatus")),
        "start_date": (status.get("startDateStruct") or {}).get("date"),
        "completion_date": (status.get("completionDateStruct") or {}).get("date"),
        "enrollment_count": enrollment_info.get("count"),
        "city": locations["city"],
        "state": locations["state"],
        "country": locations["country"],
        "india_site_count": locations["india_site_count"],
        "fetched_date": datetime.now().isoformat(timespec="seconds"),
        "data_source": "ClinicalTrials.gov API v2",
        "source_url": (
            f"https://clinicaltrials.gov/study/{identification.get('nctId')}"
            if identification.get("nctId") else None
        ),
    }


def save_trials_to_csv(
    trials: List[Dict[str, Any]], output_path: Optional[Path] = None
) -> Optional[Path]:
    """Atomically save extracted raw records as CSV."""
    if not trials:
        raise ValueError("Refusing to save an empty API result.")
    output_path = output_path or (DATA_OUTPUT_DIR / OUTPUT_FILENAME)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")

    try:
        df = pd.DataFrame(trials)
        if "nct_id" not in df.columns or df["nct_id"].isna().any():
            raise ValueError("API records are missing required NCT IDs.")
        df["nct_id"] = df["nct_id"].astype(str).str.strip()
        if not df["nct_id"].str.fullmatch(r"NCT\d{8}").all():
            raise ValueError("One or more API records have an invalid NCT ID.")
        df = df.drop_duplicates(subset=["nct_id"], keep="first")
        df.to_csv(temporary_path, index=False)
        temporary_path.replace(output_path)
        logger.info("Saved %s raw study records to %s", len(df), output_path)
        return output_path
    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()
        raise


def generate_ingestion_report(
    total_fetched: int,
    total_parsed: int,
    failed_requests: List[Dict[str, Any]],
    output_file: Optional[Path],
) -> str:
    """Create an accurate summary of ingestion outcomes."""
    success_rate = (total_parsed / total_fetched * 100) if total_fetched else 0.0
    report = (
        "CLINICAL TRIALS API INGESTION REPORT\n"
        f"Execution date: {datetime.now().isoformat(timespec='seconds')}\n"
        f"Records fetched: {total_fetched}\n"
        f"Records parsed: {total_parsed}\n"
        f"Parse success rate: {success_rate:.1f}%\n"
        f"Failures: {len(failed_requests)}\n"
        f"Output file: {output_file}\n"
        f"API endpoint: {API_BASE_URL}\n"
    )
    if failed_requests:
        report += "First errors:\n" + "\n".join(
            f"- {failure}" for failure in failed_requests[:5]
        )
    logger.info("\n%s", report)
    print(report)
    return report


def main() -> int:
    """Fetch and save raw records; run the cleaning step separately."""
    client = ClinicalTrialsAPIClient()
    raw_studies: List[Dict[str, Any]] = []
    parsed: List[Dict[str, Any]] = []
    try:
        raw_studies = client.fetch_india_trials()
        parsed = [extract_trial_record(study) for study in raw_studies]

        missing_ids = sum(not record.get("nct_id") for record in parsed)
        if missing_ids:
            message = (
                f"{missing_ids} of {len(raw_studies)} studies lacked an NCT ID; "
                "refusing to write a partial dataset."
            )
            client.failed_requests.append({"error": message})
            raise ValueError(message)

        output_path = save_trials_to_csv(parsed)
        generate_ingestion_report(
            len(raw_studies), len(parsed), client.failed_requests, output_path
        )
        return 0
    except Exception as exc:
        logger.exception("Ingestion failed: %s", exc)
        generate_ingestion_report(
            client.total_records_fetched, len(parsed), client.failed_requests, None
        )
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
