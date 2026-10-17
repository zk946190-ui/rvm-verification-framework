"""Integration tests: several components working together, with mocks for hardware/broker."""
import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api import app, get_publisher
from app.machine import ReverseVendingMachine
from app.messaging import (DEPOSIT_QUEUE, EventPublisher, InMemoryPublisher,
                           PublishError, StompPublisher)
from app.mocks import MockIRSensor, MockLoadCell, MockMetalSensor, SensorFault


class FailingPublisher(EventPublisher):
    def publish(self, destination, message):
        raise PublishError("broker down")


def make_machine(weight=20, transparent=False, metal=True, publisher=None):
    return ReverseVendingMachine(
        MockLoadCell(weight), MockIRSensor(transparent), MockMetalSensor(metal),
        publisher or InMemoryPublisher(),
    )


def test_machine_processes_deposit_and_publishes_event():
    publisher = InMemoryPublisher()
    event = make_machine(publisher=publisher).process_deposit()
    assert event["material"] == "metal"
    assert event["points"] == 5
    assert publisher.events == [(DEPOSIT_QUEUE, event)]


def test_faulty_load_cell_stops_the_deposit_and_publishes_nothing():
    publisher = InMemoryPublisher()
    machine = ReverseVendingMachine(
        MockLoadCell(20, fault=True), MockIRSensor(False), MockMetalSensor(True), publisher
    )
    with pytest.raises(SensorFault):
        machine.process_deposit()
    assert publisher.events == []


def test_machine_propagates_publish_errors():
    with pytest.raises(PublishError):
        make_machine(publisher=FailingPublisher()).process_deposit()


def test_stomp_publisher_sends_json_to_the_queue():
    with patch("app.messaging.stomp.Connection") as connection_cls:
        StompPublisher().publish(DEPOSIT_QUEUE, {"material": "glass", "points": 3})
    conn = connection_cls.return_value
    conn.connect.assert_called_once()
    conn.send.assert_called_once()
    kwargs = conn.send.call_args.kwargs
    assert kwargs["destination"] == DEPOSIT_QUEUE
    assert json.loads(kwargs["body"]) == {"material": "glass", "points": 3}
    conn.disconnect.assert_called_once()


def test_stomp_publisher_wraps_connection_errors():
    with patch("app.messaging.stomp.Connection") as connection_cls:
        connection_cls.return_value.connect.side_effect = ConnectionRefusedError("no broker")
        with pytest.raises(PublishError):
            StompPublisher().publish(DEPOSIT_QUEUE, {"x": 1})


def test_api_reports_unpublished_event_but_still_counts_deposit():
    app.dependency_overrides[get_publisher] = lambda: FailingPublisher()
    try:
        client = TestClient(app)
        r = client.post("/deposit", json={"weight_g": 20, "metal_detected": True, "transparent": False})
        assert r.status_code == 200
        assert r.json()["event_published"] is False
        assert client.get("/status").json()["deposits"] == 1
    finally:
        app.dependency_overrides.clear()


def test_api_publishes_event_for_each_deposit(client, publisher):
    client.post("/deposit", json={"weight_g": 20, "metal_detected": True, "transparent": False})
    client.post("/deposit", json={"weight_g": 150, "metal_detected": False, "transparent": True})
    assert [e[1]["material"] for e in publisher.events] == ["metal", "glass"]
