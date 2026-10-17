"""REST API for the RVM verification framework (FastAPI)."""
import os

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .logic import MAX_WEIGHT_G, classify_item, reward_points
from .messaging import (
    DEPOSIT_QUEUE,
    EventPublisher,
    InMemoryPublisher,
    PublishError,
    StompPublisher,
)

app = FastAPI(title="RVM Verification Framework")


class DepositRequest(BaseModel):
    weight_g: float = Field(gt=0, le=MAX_WEIGHT_G)
    metal_detected: bool
    transparent: bool


class DepositResponse(BaseModel):
    material: str
    points: int
    event_published: bool


class Store:
    """Very small in-memory state."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.deposits = 0
        self.total_points = 0


store = Store()
_default_publisher = None


def get_publisher() -> EventPublisher:
    """Use STOMP if RVM_STOMP_ENABLED=true, otherwise keep events in memory."""
    global _default_publisher
    if _default_publisher is None:
        if os.getenv("RVM_STOMP_ENABLED", "false").lower() == "true":
            _default_publisher = StompPublisher(
                host=os.getenv("RVM_STOMP_HOST", "localhost"),
                port=int(os.getenv("RVM_STOMP_PORT", "61613")),
            )
        else:
            _default_publisher = InMemoryPublisher()
    return _default_publisher


@app.post("/deposit", response_model=DepositResponse)
def deposit(req: DepositRequest, publisher: EventPublisher = Depends(get_publisher)):
    try:
        material = classify_item(req.weight_g, req.metal_detected, req.transparent)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    points = reward_points(material)
    store.deposits += 1
    store.total_points += points

    published = True
    try:
        publisher.publish(
            DEPOSIT_QUEUE,
            {"event": "deposit.accepted", "material": material,
             "weight_g": req.weight_g, "points": points},
        )
    except PublishError:
        published = False  # the deposit still counts; the event can be retried

    return DepositResponse(material=material, points=points, event_published=published)


@app.get("/status")
def status():
    return {"status": "ok", "deposits": store.deposits, "total_points": store.total_points}
