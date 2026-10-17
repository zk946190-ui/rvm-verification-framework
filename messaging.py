"""Event publishing over STOMP (or in memory for tests and local runs)."""
import json
import logging

import stomp

logger = logging.getLogger(__name__)

DEPOSIT_QUEUE = "/queue/rvm.deposits"


class PublishError(Exception):
    """Raised when an event cannot be published."""


class EventPublisher:
    def publish(self, destination: str, message: dict) -> None:
        raise NotImplementedError


class InMemoryPublisher(EventPublisher):
    """Stores events in a list. Used for tests and when no broker is running."""

    def __init__(self):
        self.events = []

    def publish(self, destination: str, message: dict) -> None:
        self.events.append((destination, message))


class StompPublisher(EventPublisher):
    """Sends JSON events to a STOMP broker such as ActiveMQ."""

    def __init__(self, host="localhost", port=61613, username="admin", password="admin"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def publish(self, destination: str, message: dict) -> None:
        try:
            conn = stomp.Connection([(self.host, self.port)])
            conn.connect(self.username, self.password, wait=True)
            conn.send(
                destination=destination,
                body=json.dumps(message),
                content_type="application/json",
            )
            conn.disconnect()
        except Exception as exc:  # network or broker problems
            logger.error("STOMP publish failed: %s", exc)
            raise PublishError(f"could not publish to {destination}") from exc
