# RVM Verification Framework

A Python test framework and REST API for a **simulated Reverse Vending Machine** (RVM).
It extends my final-year hardware project (Arduino Mega, load cell and IR sensor) with a
software side: mock sensors, a REST API, STOMP event messaging, and an automated test suite.

> This is a software **simulation**. The classification rules in `app/logic.py` are simplified
> and are not the exact logic running on the physical prototype.

## What it demonstrates
- **Python** application code with clear modules
- **Mock components** that simulate hardware sensors, including a fault mode
- **REST API** (FastAPI) with input validation and proper status codes
- **STOMP messaging** (`stomp.py`) for publishing deposit events to a broker
- **Automated tests** with pytest: unit, functional and integration
- **CI**: tests run on every push with GitHub Actions

## Project structure
```
app/
  logic.py       classification and reward rules
  mocks.py       MockLoadCell, MockIRSensor, MockMetalSensor (with fault mode)
  messaging.py   InMemoryPublisher and StompPublisher
  machine.py     reads sensors, classifies, publishes an event
  api.py         REST endpoints (FastAPI)
tests/
  test_unit.py         unit tests (logic and mocks)
  test_api.py          functional tests (REST API)
  test_integration.py  integration tests (machine + mocks + publisher, STOMP patched)
docs/SPRINT_LOG.md     sprint notes
```

## Setup
Requires Python 3.10 or newer.
```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Run the tests
```bash
pytest -v
pytest --cov=app --cov-report=term-missing    # with coverage
```
A `StarletteDeprecationWarning` about `httpx` may appear. It does not affect the results.

## Run the API
```bash
uvicorn app.api:app --reload
```
Open http://127.0.0.1:8000/docs for interactive documentation.

| Method | Path | Description |
|---|---|---|
| POST | `/deposit` | Send sensor readings, get material and points |
| GET | `/status` | Number of deposits and total points |

Example:
```bash
curl -X POST http://127.0.0.1:8000/deposit \
  -H "Content-Type: application/json" \
  -d '{"weight_g": 20, "metal_detected": true, "transparent": false}'
# {"material":"metal","points":5,"event_published":true}
```
Invalid input (for example `weight_g` of 0) returns HTTP 422.

## Optional: real STOMP broker
By default events are kept in memory. To publish to a real broker:
```bash
docker compose up -d
# Windows PowerShell:  $env:RVM_STOMP_ENABLED="true"
# Mac/Linux:           export RVM_STOMP_ENABLED=true
uvicorn app.api:app --reload
```
Events go to the queue `/queue/rvm.deposits`. The ActiveMQ web console is at
http://localhost:8161 (default login admin / admin, for local use only).
If the broker is down, `/deposit` still succeeds and returns `"event_published": false`.

## Test results
Update this section with your own numbers after running the suite.
- Tests: ___ passing (unit, functional, integration)
- Coverage: ___%
