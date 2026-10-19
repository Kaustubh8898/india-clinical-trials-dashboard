# Refactoring Notes — Historical Status Superseded

This file contains historical implementation notes from the prototype phase. It should not be interpreted as evidence that the repository data was verified against ClinicalTrials.gov or that the application is production-ready.

Current authoritative documentation:
- README.md — setup, refresh, and usage.
- DATA_QUALITY.md — provenance checks and interpretation cautions.
- IMPLEMENTATION_SUMMARY.md — implemented changes versus work not yet validated.

The current branch requires an explicit ClinicalTrials.gov API v2 source marker and a registry URL matching each NCT ID before the dashboard draws charts. The original committed CSV does not meet that requirement and must be refreshed with the ingestion and cleaning commands. Test success must be determined from the automated test run, not from the claims in this historical file.
