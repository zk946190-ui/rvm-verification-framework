"""Core classification and reward rules for the simulated Reverse Vending Machine.

NOTE: These rules are a simplified simulation. Adjust them to match how your
real prototype decides between plastic, metal and glass.
"""

MAX_WEIGHT_G = 2000.0
MATERIAL_POINTS = {"plastic": 2, "metal": 5, "glass": 3}


def classify_item(weight_g: float, metal_detected: bool, transparent: bool) -> str:
    """Return 'plastic', 'metal' or 'glass' from the sensor readings.

    Raises ValueError for impossible or conflicting readings.
    """
    if weight_g is None or weight_g <= 0:
        raise ValueError("weight_g must be greater than 0")
    if weight_g > MAX_WEIGHT_G:
        raise ValueError(f"weight_g must not exceed {MAX_WEIGHT_G} g")
    if metal_detected and transparent:
        raise ValueError("conflicting readings: an item cannot be both metal and transparent")
    if metal_detected:
        return "metal"
    if transparent:
        return "glass"
    return "plastic"


def reward_points(material: str) -> int:
    """Return the reward points for one accepted item of the given material."""
    try:
        return MATERIAL_POINTS[material]
    except KeyError:
        raise ValueError(f"unknown material: {material!r}") from None
