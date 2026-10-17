"""Functional tests: exercise the REST API the way an end user would."""


def test_deposit_metal_item(client):
    r = client.post("/deposit", json={"weight_g": 20, "metal_detected": True, "transparent": False})
    assert r.status_code == 200
    assert r.json() == {"material": "metal", "points": 5, "event_published": True}


def test_deposit_glass_item(client):
    r = client.post("/deposit", json={"weight_g": 150, "metal_detected": False, "transparent": True})
    assert r.status_code == 200
    assert r.json()["material"] == "glass"


def test_zero_weight_is_rejected(client):
    r = client.post("/deposit", json={"weight_g": 0, "metal_detected": False, "transparent": False})
    assert r.status_code == 422


def test_missing_field_is_rejected(client):
    r = client.post("/deposit", json={"weight_g": 10, "metal_detected": False})
    assert r.status_code == 422


def test_conflicting_readings_are_rejected(client):
    r = client.post("/deposit", json={"weight_g": 10, "metal_detected": True, "transparent": True})
    assert r.status_code == 422
    assert "conflicting" in r.json()["detail"]


def test_status_starts_empty(client):
    assert client.get("/status").json() == {"status": "ok", "deposits": 0, "total_points": 0}


def test_status_counts_deposits_and_points(client):
    client.post("/deposit", json={"weight_g": 20, "metal_detected": True, "transparent": False})
    client.post("/deposit", json={"weight_g": 15, "metal_detected": False, "transparent": False})
    assert client.get("/status").json() == {"status": "ok", "deposits": 2, "total_points": 7}


def test_rejected_deposit_is_not_counted(client):
    client.post("/deposit", json={"weight_g": -1, "metal_detected": False, "transparent": False})
    assert client.get("/status").json()["deposits"] == 0
