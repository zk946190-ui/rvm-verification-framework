"""Mock sensors that simulate the real hardware (load cell, IR sensor, metal sensor)."""


class SensorFault(Exception):
    """Raised when a (mock) sensor is in a fault state."""


class _MockSensor:
    def __init__(self, value, fault: bool = False):
        self.value = value
        self.fault = fault

    def read(self):
        if self.fault:
            raise SensorFault(f"{self.__class__.__name__} fault")
        return self.value


class MockLoadCell(_MockSensor):
    """Returns a weight in grams."""


class MockIRSensor(_MockSensor):
    """Returns True if the item is transparent."""


class MockMetalSensor(_MockSensor):
    """Returns True if metal is detected."""
