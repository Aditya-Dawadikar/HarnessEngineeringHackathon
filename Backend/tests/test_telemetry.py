import logging
from datetime import datetime
from unittest.mock import Mock

from app import telemetry


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


def test_insert_failure_is_logged_and_does_not_raise(monkeypatch, caplog):
    def boom(table, row):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(telemetry, "_insert", boom)

    with caplog.at_level(logging.ERROR, logger="telemetry"):
        telemetry.log_message(
            transaction_id="txn-1",
            conversation_turn=1,
            sender_type="BuyerAgent",
            sender_id="BuyerAgent",
            receiver_id="VendorAgent",
            raw_message="hello",
            extracted_price=None,
            extracted_quantity=None,
        )

    assert any("connection refused" in record.message for record in caplog.records)


def test_ddl_defines_expected_tables():
    assert "agent_message_logs" in telemetry.AGENT_MESSAGE_LOGS_DDL
    assert "agent_tool_executions" in telemetry.AGENT_TOOL_EXECUTIONS_DDL
    assert "IF NOT EXISTS" in telemetry.AGENT_MESSAGE_LOGS_DDL
    assert "IF NOT EXISTS" in telemetry.AGENT_TOOL_EXECUTIONS_DDL


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
