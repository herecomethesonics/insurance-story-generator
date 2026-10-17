"""Детерминированный расчёт компенсации для смартфонов.

Все коэффициенты — стартовые допущения MVP, их нужно калибровать
на реальных данных.
"""
from datetime import date

from .models import CalcStep, ClaimRequest, CompensationResult, Condition, EventType

DEPRECIATION_FIRST_YEAR_MONTHLY = 0.02
DEPRECIATION_LATER_MONTHLY = 0.01
MAX_DEPRECIATION = 0.70

CONDITION_FACTOR = {
    Condition.excellent: 1.0,
    Condition.good: 0.9,
    Condition.fair: 0.75,
}

# Стоимость ремонта как доля цены покупки (запчасти дешевеют медленнее устройства).
REPAIR_SHARE = {
    EventType.screen_damage: 0.25,
    EventType.water_damage: 0.60,
}

# Если ремонт дороже этой доли от текущей стоимости — признаём полную гибель.
TOTAL_LOSS_THRESHOLD = 0.8


def months_between(start: date, end: date) -> int:
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    return max(months, 0)


def depreciation_rate(months: int) -> float:
    first_year = min(months, 12) * DEPRECIATION_FIRST_YEAR_MONTHLY
    later = max(months - 12, 0) * DEPRECIATION_LATER_MONTHLY
    return min(first_year + later, MAX_DEPRECIATION)


def calculate(req: ClaimRequest) -> CompensationResult:
    phone, policy, event = req.phone, req.policy, req.event
    if event.date < phone.purchase_date:
        raise ValueError("Дата события раньше даты покупки")

    months = months_between(phone.purchase_date, event.date)
    dep = depreciation_rate(months)
    cond = CONDITION_FACTOR[phone.condition]
    device_value = phone.purchase_price * (1 - dep) * cond

    steps = [
        CalcStep(label="Цена покупки", value=phone.purchase_price),
        CalcStep(label=f"Износ за {months} мес., %", value=round(dep * 100, 2)),
        CalcStep(label="Коэффициент состояния", value=cond),
        CalcStep(label="Стоимость на дату события", value=round(device_value, 2)),
    ]

    total_loss = False
    if event.type in (EventType.theft, EventType.total_loss):
        loss = device_value
        total_loss = True
    elif event.type in REPAIR_SHARE:
        repair = phone.purchase_price * REPAIR_SHARE[event.type]
        steps.append(CalcStep(label="Оценка стоимости ремонта", value=round(repair, 2)))
        if repair >= TOTAL_LOSS_THRESHOLD * device_value:
            loss = device_value
            total_loss = True
        else:
            loss = repair
    else:
        loss = device_value * event.severity
        steps.append(CalcStep(label="Степень ущерба", value=event.severity))

    steps.append(CalcStep(label="Размер ущерба", value=round(loss, 2)))

    insured = min(loss, policy.sum_insured)
    if insured < loss:
        steps.append(CalcStep(label="Ограничение страховой суммой", value=policy.sum_insured))
    steps.append(CalcStep(label="Франшиза", value=-policy.deductible))

    payout = max(insured - policy.deductible, 0)
    steps.append(CalcStep(label="К выплате", value=round(payout, 2)))

    return CompensationResult(
        device_value=round(device_value, 2),
        loss_amount=round(loss, 2),
        total_loss=total_loss,
        payout=round(payout, 2),
        steps=steps,
    )
