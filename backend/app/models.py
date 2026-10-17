from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class Condition(str, Enum):
    excellent = "excellent"
    good = "good"
    fair = "fair"


class EventType(str, Enum):
    screen_damage = "screen_damage"
    water_damage = "water_damage"
    theft = "theft"
    total_loss = "total_loss"
    other_damage = "other_damage"


class Phone(BaseModel):
    brand: str = Field(min_length=1)
    model: str = Field(min_length=1)
    purchase_price: float = Field(gt=0, description="Цена покупки, руб.")
    purchase_date: date
    condition: Condition = Condition.good


class Policy(BaseModel):
    sum_insured: float = Field(gt=0, description="Страховая сумма (лимит), руб.")
    deductible: float = Field(default=0, ge=0, description="Безусловная франшиза, руб.")


class Event(BaseModel):
    type: EventType
    date: date
    severity: float = Field(
        default=0.5, ge=0, le=1,
        description="Степень ущерба 0..1, используется для other_damage",
    )


class ClaimRequest(BaseModel):
    phone: Phone
    policy: Policy
    event: Event


class CalcStep(BaseModel):
    label: str
    value: float


class CompensationResult(BaseModel):
    device_value: float
    loss_amount: float
    total_loss: bool
    payout: float
    steps: list[CalcStep]


class ClaimResponse(BaseModel):
    compensation: CompensationResult
    story: str
    story_source: str = Field(description='"llm" — Claude, "ollama" — локальная модель, "template" — шаблон')
    disclaimer: str
