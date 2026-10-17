"""Генерация текста страховой истории.

Повествование пишет языковая модель, суммы — всегда только calculator: модель
сумм не получает и не упоминает, итоговое предложение с ними добавляет код.
Если модель недоступна или ответ не прошёл проверку, используется шаблон,
чтобы приложение работало всегда.

Режим задаётся переменной окружения STORY_GENERATOR:
  "llm"      — Claude API (по умолчанию)
  "ollama"   — локальная модель через Ollama (OLLAMA_MODEL, OLLAMA_URL)
  "template" — только шаблон
"""
import json
import logging
import os
import random
import re

from datetime import date
from functools import lru_cache

import anthropic
import httpx

from .models import ClaimRequest, CompensationResult, Condition, EventType

log = logging.getLogger(__name__)

DISCLAIMER = "СГЕНЕРИРОВАНО АВТОМАТИЧЕСКИ. Не является страховым документом."

MODEL = "claude-opus-5-5"

OLLAMA_DEFAULT_MODEL = "qwen3:4b-instruct"
OLLAMA_DEFAULT_URL = "http://localhost:11434"
OLLAMA_TIMEOUT = 120  # секунд; на процессоре генерация медленная
OLLAMA_ATTEMPTS = 2

SYSTEM_PROMPT = """\
Ты пишешь короткие правдоподобные истории страховых случаев для демонстрационного \
генератора. Истории синтетические и используются для тестирования и обучения, \
а не для подачи реальных заявлений.

По данным в JSON напиши связное повествование на русском языке, 1–2 абзаца, \
нейтральным деловым стилем: как и при каких обстоятельствах произошло событие, \
что заметил владелец, какие действия предпринял (обращение в сервис, полицию, \
страховую компанию — по ситуации).

Правила:
- Не противоречь фактам из JSON: устройство, даты, тип события, признана ли полная гибель.
- Даты пиши точно так, как они даны в JSON. Других чисел (время, сроки, суммы) не используй.
- Не упоминай денежные суммы, проценты и коэффициенты — их добавит система.
- Не выдумывай ФИО, адреса, номера документов и названия реальных организаций.
- Без заголовков, списков и markdown — только текст."""

EVENT_LABELS = {
    EventType.screen_damage: "повреждение экрана",
    EventType.water_damage: "залитие жидкостью",
    EventType.theft: "кража",
    EventType.total_loss: "полная гибель",
    EventType.other_damage: "иное механическое повреждение",
}

EVENT_SCENARIOS = {
    EventType.screen_damage: [
        "телефон выскользнул из рук и упал экраном на плитку",
        "устройство упало с высоты стола, на дисплее появились трещины",
    ],
    EventType.water_damage: [
        "телефон упал в воду и перестал включаться",
        "на устройство была пролита жидкость, после чего оно вышло из строя",
    ],
    EventType.theft: [
        "телефон был похищен в общественном транспорте",
        "устройство было украдено из сумки в торговом центре",
    ],
    EventType.total_loss: [
        "устройство получило повреждения, несовместимые с ремонтом",
    ],
    EventType.other_damage: [
        "устройство получило механические повреждения корпуса",
    ],
}


CONDITION_LABELS = {
    Condition.excellent: "отличное",
    Condition.good: "хорошее",
    Condition.fair: "удовлетворительное",
}

RU_MONTHS = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]


def _ru_date(d: date) -> str:
    # Готовая дата словами: маленькие модели путают дни в формате ISO.
    return f"{d.day} {RU_MONTHS[d.month - 1]} {d.year} года"


def _rub(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ") + " руб"


def _summary(result: CompensationResult) -> str:
    return (
        f"Стоимость устройства на дату события с учётом износа: {_rub(result.device_value)}. "
        f"Размер ущерба: {_rub(result.loss_amount)}. "
        f"Прогноз выплаты с учётом франшизы и лимита: {_rub(result.payout)}."
    )


def template_story(req: ClaimRequest, result: CompensationResult, seed: int | None = None) -> str:
    rnd = random.Random(seed)
    phone, event = req.phone, req.event
    scenario = rnd.choice(EVENT_SCENARIOS[event.type])

    outcome = (
        "Ремонт признан нецелесообразным, зафиксирована полная гибель устройства."
        if result.total_loss and event.type != EventType.theft
        else ""
    )

    parts = [
        f"{phone.brand} {phone.model} приобретён {phone.purchase_date:%d.%m.%Y} "
        f"за {_rub(phone.purchase_price)}.",
        f"{event.date:%d.%m.%Y} {scenario}.",
        outcome,
        _summary(result),
    ]
    return " ".join(p for p in parts if p)


@lru_cache(maxsize=1)
def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def _facts(req: ClaimRequest, result: CompensationResult) -> str:
    facts = {
        "устройство": f"{req.phone.brand} {req.phone.model}",
        "дата_покупки": _ru_date(req.phone.purchase_date),
        "состояние": CONDITION_LABELS[req.phone.condition],
        "событие": EVENT_LABELS[req.event.type],
        "дата_события": _ru_date(req.event.date),
    }
    # Для кражи calculator считает ущерб как при полной гибели, но в тексте
    # это выглядит нелепо («полная гибель признана» у украденного телефона).
    if req.event.type != EventType.theft:
        facts["полная_гибель"] = result.total_loss
    return json.dumps(facts, ensure_ascii=False)


def _allowed_numbers(req: ClaimRequest) -> set[str]:
    d1, d2 = req.phone.purchase_date, req.event.date
    nums = {str(d1.day), str(d1.year), str(d2.day), str(d2.year)}
    nums |= set(re.findall(r"\d+", f"{req.phone.brand} {req.phone.model}"))
    return nums


def check_narrative(text: str, req: ClaimRequest) -> str | None:
    """Причина отклонения текста или None, если текст прошёл проверку.

    Маленькие локальные модели чаще нарушают правила промпта, поэтому их
    ответ проверяется: в нём не должно быть сумм и чисел не из входных данных
    (неверные даты, время, сроки).
    """
    if re.search(r"руб|₽|%", text, re.IGNORECASE):
        return "упоминание денег или процентов"
    allowed = _allowed_numbers(req)
    extra = {n for n in re.findall(r"\b\d+\b", text) if str(int(n)) not in allowed}
    if extra:
        return f"числа не из входных данных: {sorted(extra)}"
    # Отдельные числа могут совпасть случайно (день одной даты у другой),
    # поэтому пары «день месяц» сверяются с настоящими датами целиком.
    real = {(d.day, RU_MONTHS[d.month - 1]) for d in (req.phone.purchase_date, req.event.date)}
    months = "|".join(RU_MONTHS)
    for day, month in re.findall(rf"\b(\d{{1,2}})\s+({months})\b", text, re.IGNORECASE):
        if (int(day), month.lower()) not in real:
            return f"неверная дата: {day} {month}"
    return None


def ollama_narrative(req: ClaimRequest, result: CompensationResult) -> str | None:
    """Повествование от локальной модели или None, если получить его не удалось."""
    url = os.getenv("OLLAMA_URL", OLLAMA_DEFAULT_URL).rstrip("/") + "/api/chat"
    model = os.getenv("OLLAMA_MODEL", OLLAMA_DEFAULT_MODEL)
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _facts(req, result)},
        ],
    }
    for attempt in range(1, OLLAMA_ATTEMPTS + 1):
        try:
            resp = httpx.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError) as e:
            log.warning("Ollama недоступна, используется шаблон: %s", e)
            return None

        text = data.get("message", {}).get("content", "")
        # Модели с рассуждениями (например, qwen3:4b) кладут их в ответ до </think>.
        text = text.rsplit("</think>", 1)[-1].strip()
        if not text or data.get("done_reason") != "stop":
            reason = f"пустой или обрезанный ответ ({data.get('done_reason')})"
        else:
            reason = check_narrative(text, req)
            if reason is None:
                return text
        log.warning("Ответ %s отклонён (попытка %d/%d): %s", model, attempt, OLLAMA_ATTEMPTS, reason)
    return None


def llm_narrative(req: ClaimRequest, result: CompensationResult) -> str | None:
    """Повествование от Claude или None, если получить его не удалось."""
    try:
        response = get_client().beta.messages.create(
            model=MODEL,
            max_tokens=4000,
            output_config={"effort": "medium"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _facts(req, result)}],
        )
    # TypeError SDK бросает, когда не настроены учётные данные (нет ANTHROPIC_API_KEY).
    except (anthropic.AnthropicError, TypeError) as e:
        log.warning("Claude недоступен, используется шаблон: %s", e)
        return None

    if response.stop_reason == "refusal":
        log.warning("Claude отказался генерировать историю, используется шаблон")
        return None

    text = "".join(b.text for b in response.content if b.type == "text").strip()
    if not text or response.stop_reason == "max_tokens":
        log.warning("Пустой или обрезанный ответ Claude (%s), используется шаблон", response.stop_reason)
        return None
    return text


def generate_story(req: ClaimRequest, result: CompensationResult) -> tuple[str, str]:
    """Возвращает (текст истории, источник: "llm", "ollama" или "template")."""
    mode = os.getenv("STORY_GENERATOR", "llm")
    providers = {"llm": llm_narrative, "ollama": ollama_narrative}
    if mode in providers:
        narrative = providers[mode](req, result)
        if narrative:
            return f"{narrative}\n\n{_summary(result)}", mode
    return template_story(req, result), "template"
