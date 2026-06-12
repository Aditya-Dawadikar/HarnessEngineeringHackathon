import logging

from app import telemetry


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
