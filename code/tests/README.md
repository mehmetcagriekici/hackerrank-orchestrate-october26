# tests/

Tests for each stage, checked against `dataset/sample_deletion_requests.csv` and `dataset/sample_output.csv`.

- **gate:** sanity checks and authorization decisions
- **link builder / organizer:** recall, meaning every `resource_id` and `evidence_id` cited in a sample answer is found (no LLM needed)
- **audit:** status, step, field and sequence accuracy against the samples
