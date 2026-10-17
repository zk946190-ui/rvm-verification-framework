"""Ties the sensors, rules and event publisher together (the 'machine')."""
from .logic import classify_item, reward_points
from .messaging import DEPOSIT_QUEUE, EventPublisher


class ReverseVendingMachine:
    def __init__(self, load_cell, ir_sensor, metal_sensor, publisher: EventPublisher):
        self.load_cell = load_cell
        self.ir_sensor = ir_sensor
        self.metal_sensor = metal_sensor
        self.publisher = publisher

    def process_deposit(self) -> dict:
        """Read all sensors, classify the item, award points and publish an event."""
        weight = self.load_cell.read()
        transparent = self.ir_sensor.read()
        metal = self.metal_sensor.read()

        material = classify_item(weight, metal, transparent)
        event = {
            "event": "deposit.accepted",
            "material": material,
            "weight_g": weight,
            "points": reward_points(material),
        }
        self.publisher.publish(DEPOSIT_QUEUE, event)
        return event
