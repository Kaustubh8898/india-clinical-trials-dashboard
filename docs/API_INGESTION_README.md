# ClinicalTrials.gov API Ingestion

The ingestion module uses the public ClinicalTrials.gov API v2 endpoint to retrieve studies with listed locations in India. It does not require an API key.

## Run

    python -m src.ingestion.clinical_trials_api

Raw output is written to data/raw/india_trials_raw.csv. Run the cleaning step afterward:

    python -m src.cleaning.clean_trials

## Pipeline behavior

- Requests the study fields used by the dashboard.
- Uses the advanced location-country filter and follows nextPageToken pagination.
- Retries transient timeouts, connection failures, rate limiting, and server errors with bounded delays.
- Stops on failed pagination instead of representing a partial pull as complete.
- Extracts one row per study, the first listed Indian site, and the count of Indian sites.
- Adds data_source, source_url, and fetched_date provenance fields.
- Deduplicates NCT IDs and validates ID shape before writing.
- Writes via a temporary file and replaces the previous raw CSV only after a successful non-empty response.

## Notes

A study matching an Indian location can also have locations outside India. City and state are the first Indian site, not a complete site-level dataset. The ingestion process is a snapshot, not a live feed; include fetched_date when sharing metrics.

The source marker and URL aid traceability, but they do not independently verify that every registry field is clinically accurate. Check specific records at their source URL for research or business-critical work.
