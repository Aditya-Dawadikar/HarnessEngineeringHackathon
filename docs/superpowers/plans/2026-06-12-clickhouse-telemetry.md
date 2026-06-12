# BE-7: Real ClickHouse Telemetry Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `Backend/app/telemetry.py`'s console-only `_insert` with a real `clickhouse-connect` client that writes to ClickHouse Cloud, creating the `agent_message_logs` / `agent_tool_executions` tables on first use.

**Architecture:** `telemetry.py` gets a lazy singleton ClickHouse client (`_get_client()`) that, on first successful creation, runs `CREATE DATABASE IF NOT EXISTS` + both table DDLs (now `CREATE TABLE IF NOT EXISTS`). `_insert` coerces row values (None price/quantity -> 0/0.0, ISO timestamp string -> `datetime`) and calls `client.insert(...)`. `_safe_insert`'s "never block the negotiation" contract is unchanged — any failure (including client init failure) is caught, logged, and swallowed. `log_message` / `log_tool_execution` signatures are untouched.

**Tech Stack:** `clickhouse-connect` (official Python client, HTTP interface), `python-dotenv` (loads repo-root `.env` for `CLICKHOUSE_*` config).

**Spec:** `docs/superpowers/specs/2026-06-12-clickhouse-telemetry-design.md`

---

## Reference: connection details for `.env`

```
CLICKHOUSE_HOST=x1hcogy14t.us-east1.gcp.clickhouse.cloud
CLICKHOUSE_PORT=8443
CLICKHOUSE_DATABASE=default
CLICKHOUSE_SECURE=true
```

`CLICKHOUSE_USER` / `CLICKHOUSE_PASSWORD` are already in the repo-root `.env`.

---

### Task 1: Add ClickHouse dependencies

**Files:**
- Modify: `Backend/requirements.txt`

- [ ] **Step 1: Add the two new dependencies**

`Backend/requirements.txt` currently reads:

```
fastapi
uvicorn[standard]
langgraph
langchain-core
pytest
httpx
requests
```

Append two lines so the file reads:

```
fastapi
uvicorn[standard]
langgraph
langchain-core
pytest
httpx
requests
clickhouse-connect
python-dotenv
```

- [ ] **Step 2: Install into the project venv**

Run: `D:\HarnessAgentHackathon\Backend\.venv\Scripts\python.exe -m pip install clickhouse-connect python-dotenv`

Expected: pip resolves and installs `clickhouse-connect`, `python-dotenv`, and their transitive deps (e.g. `certifi`, `lz4`, `zstandard`) with no errors.

- [ ] **Step 3: Verify both import cleanly**

Run: `D:\HarnessAgentHackathon\Backend\.venv\Scripts\python.exe -c "import clickhouse_connect, dotenv; print('ok')"`

Expected: prints `ok`.

- [ ] **Step 4: Commit**

```bash
git add Backend/requirements.txt
git commit -m "[BE-7] Add clickhouse-connect and python-dotenv dependencies"
```

---

### Task 2: Make table DDL idempotent (`IF NOT EXISTS`)

**Files:**
- Modify: `Backend/app/telemetry.py:21-52`
- Test: `Backend/tests/test_telemetry.py:57-59`

- [ ] **Step 1: Write the failing test**

In `Backend/tests/test_telemetry.py`, replace the existing `test_ddl_defines_expected_tables` (lines 57-59):

```python
def test_ddl_defines_expected_tables():
    assert "agent_message_logs" in telemetry.AGENT_MESSAGE_LOGS_DDL
    assert "agent_tool_executions" in telemetry.AGENT_TOOL_EXECUTIONS_DDL
```

with:

```python
def test_ddl_defines_expected_tables():
    assert "agent_message_logs" in telemetry.AGENT_MESSAGE_LOGS_DDL
    assert "agent_tool_executions" in telemetry.AGENT_TOOL_EXECUTIONS_DDL
    assert "IF NOT EXISTS" in telemetry.AGENT_MESSAGE_LOGS_DDL
    assert "IF NOT EXISTS" in telemetry.AGENT_TOOL_EXECUTIONS_DDL
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Backend && .venv\Scripts\python.exe -m pytest tests/test_telemetry.py::test_ddl_defines_expected_tables -v`

Expected: `FAIL` — `assert "IF NOT EXISTS" in telemetry.AGENT_MESSAGE_LOGS_DDL` is `False`.

- [ ] **Step 3: Add `IF NOT EXISTS` to both DDL strings**

In `Backend/app/telemetry.py`, change line 22 from:

```python
CREATE TABLE default.agent_message_logs (
```

to:

```python
CREATE TABLE IF NOT EXISTS default.agent_message_logs (
```

And change line 40 from:

```python
CREATE TABLE default.agent_tool_executions (
```

to:

```python
CREATE TABLE IF NOT EXISTS default.agent_tool_executions (
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Backend && .venv\Scripts\python.exe -m pytest tests/test_telemetry.py -v`

Expected: all 4 existing tests in `test_telemetry.py` `PASS`.

- [ ] **Step 5: Commit**

```bash
git add Backend/app/telemetry.py Backend/tests/test_telemetry.py
git commit -m "[BE-7] Make telemetry table DDL idempotent (CREATE TABLE IF NOT EXISTS)"
```

---

### Task 3: Lazy ClickHouse client with startup DDL + dotenv config

**Files:**
- Modify: `Backend/app/telemetry.py` (imports, module-level config, new `_get_client`)
- Test: `Backend/tests/test_telemetry.py` (new tests + new import)

- [ ] **Step 1: Write the failing tests**

In `Backend/tests/test_telemetry.py`, change the top imports from:

```python
import logging

from app import telemetry
```

to:

```python
import logging
from unittest.mock import Mock

from app import telemetry
```

Then append these two new tests at the end of the file:

```python
def test_get_client_runs_ddl_on_first_call_only(monkeypatch):
    mock_client = Mock()
    get_client_mock = Mock(return_value=mock_client)
    monkeypatch.setattr(telemetry, "_CLIENT", telemetry._UNSET)
    monkeypatch.setattr(telemetry.clickhouse_connect, "get_client", get_client_mock)

    first = telemetry._get_client()
    second = telemetry._get_client()

    assert first is mock_client
    assert second is mock_client
    assert get_client_mock.call_count == 1

    ddl_calls = [call.args[0] for call in mock_client.command.call_args_list]
    assert len(ddl_calls) == 3
    assert any("CREATE DATABASE IF NOT EXISTS" in c for c in ddl_calls)
    assert any("agent_message_logs" in c for c in ddl_calls)
    assert any("agent_tool_executions" in c for c in ddl_calls)


def test_get_client_returns_none_and_logs_error_when_unavailable(monkeypatch, caplog):
    monkeypatch.setattr(telemetry, "_CLIENT", telemetry._UNSET)
    monkeypatch.setattr(
        telemetry.clickhouse_connect,
        "get_client",
        Mock(side_effect=RuntimeError("connection refused")),
    )

    with caplog.at_level(logging.ERROR, logger="telemetry"):
        client = telemetry._get_client()

    assert client is None
    assert any("connection refused" in record.message for record in caplog.records)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd Backend && .venv\Scripts\python.exe -m pytest tests/test_telemetry.py -v`

Expected: the two new tests `FAIL` with `AttributeError: module 'app.telemetry' has no attribute '_CLIENT'` (or `'_UNSET'` / `'clickhouse_connect'` / `'_get_client'`).

- [ ] **Step 3: Add imports, dotenv loading, env config, and `_get_client`**

In `Backend/app/telemetry.py`, replace the import block (lines 13-19):

```python
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("telemetry")
```

with:

```python
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import clickhouse_connect
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

logger = logging.getLogger("telemetry")
```

Then, immediately after the `AGENT_TOOL_EXECUTIONS_DDL = """..."""` block (after line 52, before `def _insert`), insert:

```python

def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(name, default)


CLICKHOUSE_HOST = _env("CLICKHOUSE_HOST")
CLICKHOUSE_PORT = int(_env("CLICKHOUSE_PORT", "8443"))
CLICKHOUSE_DATABASE = _env("CLICKHOUSE_DATABASE", "default")
CLICKHOUSE_USER = _env("CLICKHOUSE_USER")
CLICKHOUSE_PASSWORD = _env("CLICKHOUSE_PASSWORD")
CLICKHOUSE_SECURE = _env("CLICKHOUSE_SECURE", "true").lower() == "true"


_UNSET = object()
_CLIENT = _UNSET


def _get_client():
    global _CLIENT
    if _CLIENT is _UNSET:
        try:
            client = clickhouse_connect.get_client(
                host=CLICKHOUSE_HOST,
                port=CLICKHOUSE_PORT,
                username=CLICKHOUSE_USER,
                password=CLICKHOUSE_PASSWORD,
                database=CLICKHOUSE_DATABASE,
                secure=CLICKHOUSE_SECURE,
            )
            client.command(f"CREATE DATABASE IF NOT EXISTS {CLICKHOUSE_DATABASE}")
            client.command(AGENT_MESSAGE_LOGS_DDL)
            client.command(AGENT_TOOL_EXECUTIONS_DDL)
            _CLIENT = client
        except Exception as exc:
            logger.error("ClickHouse client initialization failed: %s", exc)
            _CLIENT = None
    return _CLIENT

```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Backend && .venv\Scripts\python.exe -m pytest tests/test_telemetry.py -v`

Expected: all 6 tests `PASS`.

- [ ] **Step 5: Commit**

```bash
git add Backend/app/telemetry.py Backend/tests/test_telemetry.py
git commit -m "[BE-7] Add lazy ClickHouse client with startup DDL and dotenv config"
```

---

### Task 4: Real inserts via `clickhouse-connect` with type coercion

**Files:**
- Modify: `Backend/app/telemetry.py` (the `_insert` function, plus new `_coerce_row`)
- Test: `Backend/tests/test_telemetry.py` (rewrite 2 tests, add 1 new test)

- [ ] **Step 1: Write the failing tests**

In `Backend/tests/test_telemetry.py`, replace `test_log_message_logs_to_console` (current lines 6-20):

```python
def test_log_message_logs_to_console(caplog):
    with caplog.at_level(logging.INFO, logger="telemetry"):
        telemetry.log_message(
            transaction_id="txn-1",
            conversation_turn=1,
            sender_type="BuyerAgent",
            sender_id="BuyerAgent",
            receiver_id="VendorAgent",
            raw_message="hello",
            extracted_price=9.0,
            extracted_quantity=200,
            llm_metadata={"model": "mock"},
        )

    assert any("agent_message_logs" in record.message for record in caplog.records)
```

with:

```python
def test_log_message_inserts_into_clickhouse(monkeypatch):
    mock_client = Mock()
    monkeypatch.setattr(telemetry, "_CLIENT", telemetry._UNSET)
    monkeypatch.setattr(telemetry.clickhouse_connect, "get_client", lambda **kwargs: mock_client)

    telemetry.log_message(
        transaction_id="txn-1",
        conversation_turn=1,
        sender_type="BuyerAgent",
        sender_id="BuyerAgent",
        receiver_id="VendorAgent",
        raw_message="hello",
        extracted_price=9.0,
        extracted_quantity=200,
        llm_metadata={"model": "mock"},
    )

    mock_client.insert.assert_called_once()
    table, rows = mock_client.insert.call_args[0]
    column_names = mock_client.insert.call_args[1]["column_names"]
    row = rows[0]

    assert table == "default.agent_message_logs"
    assert column_names == [
        "message_id", "transaction_id", "timestamp", "conversation_turn",
        "sender_type", "sender_id", "receiver_id", "raw_message",
        "extracted_price", "extracted_quantity", "llm_metadata",
    ]
    assert row[column_names.index("extracted_price")] == 9.0
    assert row[column_names.index("extracted_quantity")] == 200
    assert isinstance(row[column_names.index("timestamp")], datetime)
```

Replace `test_log_tool_execution_logs_to_console` (current lines 23-33):

```python
def test_log_tool_execution_logs_to_console(caplog):
    with caplog.at_level(logging.INFO, logger="telemetry"):
        telemetry.log_tool_execution(
            transaction_id="txn-1",
            agent_id="VendorAgent",
            tool_name="payment_request",
            payload={"amount": 100},
            execution_status="Success",
        )

    assert any("agent_tool_executions" in record.message for record in caplog.records)
```

with:

```python
def test_log_tool_execution_inserts_into_clickhouse(monkeypatch):
    mock_client = Mock()
    monkeypatch.setattr(telemetry, "_CLIENT", telemetry._UNSET)
    monkeypatch.setattr(telemetry.clickhouse_connect, "get_client", lambda **kwargs: mock_client)

    telemetry.log_tool_execution(
        transaction_id="txn-1",
        agent_id="VendorAgent",
        tool_name="payment_request",
        payload={"amount": 100},
        execution_status="Success",
    )

    mock_client.insert.assert_called_once()
    table, rows = mock_client.insert.call_args[0]
    column_names = mock_client.insert.call_args[1]["column_names"]
    row = rows[0]

    assert table == "default.agent_tool_executions"
    assert column_names == [
        "tool_execution_id", "transaction_id", "timestamp", "agent_id",
        "tool_name", "payload", "execution_status", "error_message",
    ]
    assert row[column_names.index("tool_name")] == "payment_request"
    assert row[column_names.index("execution_status")] == "Success"
    assert isinstance(row[column_names.index("timestamp")], datetime)
```

Add `from datetime import datetime` to the top imports — change:

```python
import logging
from unittest.mock import Mock

from app import telemetry
```

to:

```python
import logging
from datetime import datetime
from unittest.mock import Mock

from app import telemetry
```

Finally, append a new test for the `None` -> `0`/`0.0` coercion (this exercises the case used by `test_guardrail_validator_logs_system_message_via_telemetry` in `test_graph.py`, where a "System" message has no parsed price/quantity):

```python
def test_log_message_coerces_none_price_and_quantity_to_zero(monkeypatch):
    mock_client = Mock()
    monkeypatch.setattr(telemetry, "_CLIENT", telemetry._UNSET)
    monkeypatch.setattr(telemetry.clickhouse_connect, "get_client", lambda **kwargs: mock_client)

    telemetry.log_message(
        transaction_id="txn-1",
        conversation_turn=1,
        sender_type="System",
        sender_id="System",
        receiver_id="System",
        raw_message="guardrail check",
        extracted_price=None,
        extracted_quantity=None,
    )

    table, rows = mock_client.insert.call_args[0]
    column_names = mock_client.insert.call_args[1]["column_names"]
    row = rows[0]

    assert row[column_names.index("extracted_price")] == 0.0
    assert row[column_names.index("extracted_quantity")] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd Backend && .venv\Scripts\python.exe -m pytest tests/test_telemetry.py -v`

Expected: `test_log_message_inserts_into_clickhouse`, `test_log_tool_execution_inserts_into_clickhouse`, and `test_log_message_coerces_none_price_and_quantity_to_zero` all `FAIL` with `AssertionError: Expected 'insert' to have been called once. Called 0 times.` (current `_insert` only logs, never calls `client.insert`).

- [ ] **Step 3: Add `_coerce_row` and rewrite `_insert`**

In `Backend/app/telemetry.py`, replace the current `_insert` function (lines 55-57):

```python
def _insert(table: str, row: dict) -> None:
    logger.info("[telemetry] %s: %s", table, json.dumps(row, default=str))
```

with:

```python
def _coerce_row(row: dict) -> dict:
    row = dict(row)
    if "extracted_price" in row and row["extracted_price"] is None:
        row["extracted_price"] = 0.0
    if "extracted_quantity" in row and row["extracted_quantity"] is None:
        row["extracted_quantity"] = 0
    if isinstance(row.get("timestamp"), str):
        row["timestamp"] = datetime.fromisoformat(row["timestamp"])
    return row


def _insert(table: str, row: dict) -> None:
    client = _get_client()
    if client is None:
        raise RuntimeError("ClickHouse client is not available")

    row = _coerce_row(row)
    logger.debug("[telemetry] %s: %s", table, json.dumps(row, default=str))
    client.insert(
        f"{CLICKHOUSE_DATABASE}.{table}",
        [list(row.values())],
        column_names=list(row.keys()),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Backend && .venv\Scripts\python.exe -m pytest tests/test_telemetry.py -v`

Expected: all 7 tests in `test_telemetry.py` `PASS`.

- [ ] **Step 5: Run the full backend suite**

Run: `cd Backend && .venv\Scripts\python.exe -m pytest -v`

Expected: all tests pass (47 total — the original 46 plus the 1 net-new test added in this task; `test_log_message_logs_to_console` and `test_log_tool_execution_logs_to_console` were renamed, not added). In particular, `test_buyer_agent_logs_message_via_telemetry` and `test_guardrail_validator_logs_system_message_via_telemetry` in `test_graph.py` should still pass unchanged — they monkeypatch `app.graph.telemetry.log_message`/`log_tool_execution` directly and never reach `_insert`.

- [ ] **Step 6: Commit**

```bash
git add Backend/app/telemetry.py Backend/tests/test_telemetry.py
git commit -m "[BE-7] Insert telemetry rows into ClickHouse with type coercion"
```

---

### Task 5: Configure real connection and verify on ClickHouse Cloud

**Files:**
- Modify: `D:\HarnessAgentHackathon\.env` (gitignored — not committed)

- [ ] **Step 1: Add ClickHouse connection details to the root `.env`**

`D:\HarnessAgentHackathon\.env` currently ends with:

```
# ClickHouse (BE-7) -- from clickhouse_credentials.txt
# CLICKHOUSE_HOST/PORT/DATABASE still needed before BE-7 can connect.
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=r~zlMQM5QZ_CR
```

Replace the two comment lines and append the new vars so it reads:

```
# ClickHouse (BE-7) -- from clickhouse_credentials.txt
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=r~zlMQM5QZ_CR
CLICKHOUSE_HOST=x1hcogy14t.us-east1.gcp.clickhouse.cloud
CLICKHOUSE_PORT=8443
CLICKHOUSE_DATABASE=default
CLICKHOUSE_SECURE=true
```

- [ ] **Step 2: Run the full backend suite once more (sanity check)**

Run: `cd Backend && .venv\Scripts\python.exe -m pytest -v`

Expected: all tests still pass — `clickhouse_connect.get_client` is mocked in every telemetry test, so adding real credentials to `.env` has no effect on the suite.

- [ ] **Step 3: Live-verify against the real ClickHouse Cloud instance**

Run (from the repo root, Git Bash):

```bash
cd Backend && .venv/Scripts/python.exe - <<'EOF'
from app import telemetry

telemetry.log_message(
    transaction_id="00000000-0000-0000-0000-0000000000be7",
    conversation_turn=1,
    sender_type="System",
    sender_id="System",
    receiver_id="System",
    raw_message="BE-7 ClickHouse live verification",
    extracted_price=9.5,
    extracted_quantity=200,
    llm_metadata={"source": "be7-verification"},
)
telemetry.log_tool_execution(
    transaction_id="00000000-0000-0000-0000-0000000000be7",
    agent_id="System",
    tool_name="payment_request",
    payload={"note": "BE-7 ClickHouse live verification"},
    execution_status="Success",
)
print("done")
EOF
```

Expected: prints `done` with no errors logged. This is the real `_get_client()` path — it will create the `default` database (if missing) and both tables (if missing) via `CREATE ... IF NOT EXISTS`, then insert one row into each.

- [ ] **Step 4: Check the ClickHouse dashboard**

In the ClickHouse Cloud SQL console for `x1hcogy14t.us-east1.gcp.clickhouse.cloud`, run:

```sql
SELECT * FROM default.agent_message_logs WHERE transaction_id = '00000000-0000-0000-0000-0000000000be7';
SELECT * FROM default.agent_tool_executions WHERE transaction_id = '00000000-0000-0000-0000-0000000000be7';
```

Expected: one row in each table with `raw_message = 'BE-7 ClickHouse live verification'` / `tool_name = 'payment_request'`.

No commit needed for this task (`.env` is gitignored and not tracked).

---

## Self-Review Notes

- **Spec coverage:** Connection config + dotenv (Task 3), lazy client + idempotent DDL on first use (Tasks 2-3), `_insert` rewrite with type coercion (Task 4), unchanged `log_message`/`log_tool_execution` signatures and `_safe_insert` semantics (untouched throughout), mocked-only test strategy (Tasks 3-4), live verification (Task 5) — all covered.
- **`_coerce_row` correctness:** guarded with `"key" in row` checks so it doesn't inject `extracted_price`/`extracted_quantity` into `agent_tool_executions` rows (which don't have those keys and would otherwise get spurious columns passed to `client.insert`).
- **Type consistency:** `_get_client`, `_UNSET`, `_CLIENT`, `_coerce_row`, `CLICKHOUSE_DATABASE`, `clickhouse_connect` are referenced consistently across Tasks 3-5 with the same names/signatures.
