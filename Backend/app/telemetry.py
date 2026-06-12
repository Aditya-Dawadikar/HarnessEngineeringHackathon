"""ClickHouse telemetry for agent messages and tool executions.

[PLACEHOLDER] ClickHouse connection details (host, port, database,
credentials) are not yet known -- see INSTRUCTIONS.md Section 7. Ask
the user for these before wiring up a real client.

Until then, `log_message` / `log_tool_execution` write to the console
via `_insert`. There is no fallback buffer/queue: if `_insert` raises,
the error is logged and execution continues -- telemetry must never
block the negotiation.
"""

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import clickhouse_connect
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

logger = logging.getLogger("telemetry")

AGENT_MESSAGE_LOGS_DDL = """
CREATE TABLE IF NOT EXISTS default.agent_message_logs (
    message_id UUID,
    transaction_id UUID,
    timestamp DateTime64(3, 'UTC'),
    conversation_turn UInt32,
    sender_type Enum8('VendorAgent' = 1, 'BuyerAgent' = 2, 'System' = 3),
    sender_id String,
    receiver_id String,
    raw_message String,
    extracted_price Decimal(18, 4),
    extracted_quantity UInt32,
    llm_metadata String  -- JSON string: token count, latency, model name
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (transaction_id, timestamp);
"""

AGENT_TOOL_EXECUTIONS_DDL = """
CREATE TABLE IF NOT EXISTS default.agent_tool_executions (
    tool_execution_id UUID,
    transaction_id UUID,
    timestamp DateTime64(3, 'UTC'),
    agent_id String,
    tool_name LowCardinality(String), -- 'payment_request' or 'payment_authorization'
    payload String,
    execution_status Enum8('Success' = 1, 'Failed' = 2, 'ValidationError' = 3),
    error_message String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (tool_name, transaction_id, timestamp);
"""


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
_CLIENT_LOCK = threading.Lock()


def _get_client():
    global _CLIENT
    with _CLIENT_LOCK:
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


def _insert(table: str, row: dict) -> None:
    logger.info("[telemetry] %s: %s", table, json.dumps(row, default=str))


def _safe_insert(table: str, row: dict) -> None:
    try:
        _insert(table, row)
    except Exception as exc:
        logger.error("telemetry insert into %s failed: %s", table, exc)


def log_message(
    *,
    transaction_id: str,
    conversation_turn: int,
    sender_type: str,
    sender_id: str,
    receiver_id: str,
    raw_message: str,
    extracted_price: Optional[float],
    extracted_quantity: Optional[int],
    llm_metadata: Optional[dict] = None,
) -> None:
    row = {
        "message_id": str(uuid.uuid4()),
        "transaction_id": transaction_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "conversation_turn": conversation_turn,
        "sender_type": sender_type,
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "raw_message": raw_message,
        "extracted_price": extracted_price,
        "extracted_quantity": extracted_quantity,
        "llm_metadata": json.dumps(llm_metadata or {}),
    }
    _safe_insert("agent_message_logs", row)


def log_tool_execution(
    *,
    transaction_id: str,
    agent_id: str,
    tool_name: str,
    payload: dict,
    execution_status: str,
    error_message: str = "",
) -> None:
    row = {
        "tool_execution_id": str(uuid.uuid4()),
        "transaction_id": transaction_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_id": agent_id,
        "tool_name": tool_name,
        "payload": json.dumps(payload, default=str),
        "execution_status": execution_status,
        "error_message": error_message,
    }
    _safe_insert("agent_tool_executions", row)
