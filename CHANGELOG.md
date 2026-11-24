# Changelog

All notable changes to `bipkit-python` are documented in this file.

## [0.1.0] - 2026-11-24

### Added
- Synchronous (`Bipkit`) and asynchronous (`AsyncBipkit`) clients covering all 22 public Bipkit API paths (`evaluate`, `decide`, `feedback`, `engines`, `api_keys`, `usage`, `provenance`, `health`).
- Typed Pydantic v2 request/response models aligned with `spec/openapi.public.json`.
- Enterprise HTTP transport with `BIPKIT_API_KEY` env fallback, exponential backoff + jitter retries, `Retry-After` support, and typed error hierarchy.
- Decision-safety helpers (`should_escalate`) and Decision Provenance Ledger (DPL) verification helpers.
- Optional LangChain/LangGraph integration extra (`pip install "bipkit[langchain]"`).
