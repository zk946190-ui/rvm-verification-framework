"""Unit tests: one function at a time, no API and no network."""
import pytest

from app.logic import MAX_WEIGHT_G, classify_item, reward_points
from app.mocks import MockIRSensor, MockLoadCell, MockMetalSensor, SensorFault


@pytest.mark.parametrize(
    "weight,metal,transparent,expected",
    [
        (20, True, False, "metal"),
        (150, False, True, "glass"),
        (15, False, False, "plastic"),
        (MAX_WEIGHT_G, False, False, "plastic"),  # boundary value
    ],
)
def test_classify_item(weight, metal, transparent, expected):
    assert classify_item(weight, metal, transparent) == expected


@pytest.mark.parametrize("bad_weight", [0, -5, MAX_WEIGHT_G + 1, None])
def test_classify_rejects_invalid_weight(bad_weight):
    with pytest.raises(ValueError):
        classify_item(bad_weight, False, False)


def test_classify_rejects_conflicting_readings():
    with pytest.raises(ValueError, match="conflicting"):
        classify_item(50, True, True)


@pytest.mark.parametrize("material,points", [("plastic", 2), ("metal", 5), ("glass", 3)])
def test_reward_points(material, points):
    assert reward_points(material) == points


def test_reward_points_unknown_material():
    with pytest.raises(ValueError):
        reward_points("paper")


def test_mock_sensors_return_configured_values():
    assert MockLoadCell(42.5).read() == 42.5
    assert MockIRSensor(True).read() is True
    assert MockMetalSensor(False).read() is False


def test_mock_sensor_fault_mode_raises():
    with pytest.raises(SensorFault):
        MockLoadCell(10, fault=True).read()
