import pytest
from fastapi.testclient import TestClient

from app.api import app, get_publisher, store
from app.messaging import InMemoryPublisher


@pytest.fixture(autouse=True)
def reset_store():
    store.reset()
    yield
    store.reset()


@pytest.fixture
def publisher():
    return InMemoryPublisher()


@pytest.fixture
def client(publisher):
    app.dependency_overrides[get_publisher] = lambda: publisher
    yield TestClient(app)
    app.dependency_overrides.clear()
