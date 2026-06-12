# BE-7: Real ClickHouse Telemetry Integration

## Context

`Backend/app/telemetry.py` currently has a placeholder `_insert()` that only
logs to console (see `INSTRUCTIONS.md` Section 7, `TICKETS.md` BE-7). This
replaces it with a real `clickhouse-connect` client writing to ClickHouse
Cloud, while preserving the `log_message` / `log_tool_execution` public
signatures used by `graph.py` (BE-2/BE-4) unchanged, and preserving the
"telemetry must never block the negotiation" guarantee.

## Connection details

- `CLICKHOUSE_HOST=x1hcogy14t.us-east1.gcp.clickhouse.cloud`
- `CLICKHOUSE_PORT=8443`
- `CLICKHOUSE_SECURE=true` (HTTPS on 8443 = ClickHouse Cloud's secure HTTP interface)
- `CLICKHOUSE_DATABASE=default`
- `CLICKHOUSE_USER` / `CLICKHOUSE_PASSWORD` — already present in repo-root `.env`
  (from `clickhouse_credentials.txt`, gitignored)

All six are configurable via env vars per BE-7; the values above become the
defaults / `.env` entries.

## 1. Config & env loading

- Add `python-dotenv` to `Backend/requirements.txt`.
- At the top of `telemetry.py`, call `load_dotenv()` pointed at the repo-root
  `.env` (two directories up from `Backend/app/telemetry.py`), so
  `CLICKHOUSE_*` vars are available without manual shell exports. This
  mirrors the existing `_env()`-style fallback pattern in `llm_client.py`.
- Read `CLICKHOUSE_HOST`, `CLICKHOUSE_PORT` (int, default `8443`),
  `CLICKHOUSE_DATABASE` (default `"default"`), `CLICKHOUSE_USER`,
  `CLICKHOUSE_PASSWORD`, `CLICKHOUSE_SECURE` (bool, default `true`).

## 2. Client lifecycle

- `_get_client()`: lazy singleton (module-level cache). On first call:
  - Build the client via `clickhouse_connect.get_client(host=..., port=...,
    username=..., password=..., secure=..., database=...)`.
  - Run `CREATE DATABASE IF NOT EXISTS {database}`, then both table DDLs
    (with `IF NOT EXISTS` added to the existing `AGENT_MESSAGE_LOGS_DDL` /
    `AGENT_TOOL_EXECUTIONS_DDL` strings in `telemetry.py`) via `client.command(...)`.
  - On any exception (connection failure, auth failure, DDL error): log the
    error, cache `None` as the client, and return `None`.
- Every subsequent call returns the cached client (or `None`) without
  retrying — consistent with "no fallback/retry infrastructure" (POC scope).

## 3. Insert path

- `_insert(table, row)`:
  - `client = _get_client()`; if `None`, raise (so `_safe_insert` logs it the
    same way it logs any other insert failure — no special-casing).
  - Coerce `row` values to ClickHouse-friendly types before inserting:
    - `extracted_price`: `None` -> `0.0` (column is non-nullable `Decimal(18,4)`)
    - `extracted_quantity`: `None` -> `0` (column is non-nullable `UInt32`)
    - `timestamp`: parse the existing ISO string into a `datetime` object
      (DateTime64 columns need `datetime`, not `str`)
  - Call `client.insert(f"{DATABASE}.{table}", [list(row.values())],
    column_names=list(row.keys()))`. Row dict key order already matches DDL
    column order for both tables.
  - Keep a `logger.debug(...)` line for console visibility (existing
    `logger.info` becomes `logger.debug` to reduce noise, since "logs to
    console" is no longer the primary behavior).
- `_safe_insert` unchanged: catches any exception from `_insert`, logs via
  `logger.error`, never raises.

## 4. Testing

- `clickhouse_connect.get_client` is **always mocked** — no test talks to
  real ClickHouse.
- Update existing tests in `Backend/tests/test_telemetry.py`:
  - `test_log_message_logs_to_console` / `test_log_tool_execution_logs_to_console`:
    monkeypatch `telemetry._get_client` to return a `Mock()`, assert
    `client.insert(...)` was called with the expected table name and that
    `row` values were coerced correctly (no `None`s, `timestamp` is a
    `datetime`).
  - `test_insert_failure_is_logged_and_does_not_raise`: unchanged (already
    monkeypatches `_insert` directly).
  - `test_ddl_defines_expected_tables`: unchanged, but also assert
    `IF NOT EXISTS` is present in both DDL strings.
- New tests:
  - `_get_client()` returns `None` (and logs an error) when
    `clickhouse_connect.get_client` raises.
  - `_get_client()` runs `CREATE DATABASE IF NOT EXISTS` + both table DDLs via
    `client.command(...)` on first successful creation, and does not re-run
    them on a second call (singleton caching).
  - `_insert` coerces `None` price/quantity to `0`/`0.0` and `timestamp` to a
    `datetime` before calling `client.insert`.

## Out of scope

- No retry/backoff/buffering (matches `INSTRUCTIONS.md` Section 10).
- No changes to `graph.py` call sites — signatures unchanged.
- No changes to DDL column types/structure beyond adding `IF NOT EXISTS`.
