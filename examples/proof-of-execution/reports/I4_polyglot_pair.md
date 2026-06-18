# I4 Report — proof artifact

## service_summary

FastAPI POST /convert + GET /health with Pydantic validation and CORS.

## client_summary

Node CLI calls the service and prints formatted output.

## ui_summary

React Vite UI for live conversion against the local API.

## validation_rules

Pydantic: amount > 0, known currency codes → 422 otherwise

## service_tests

`pytest service/test_service.py` — 4 passed

## client_tests

`bash client/test_client.sh`

## run_instructions

See `artifacts/I4/README.md`
