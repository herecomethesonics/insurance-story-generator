from types import SimpleNamespace

import anthropic
import httpx
import pytest

from app import story
from app.calculator import calculate
from tests.test_calculator import make_req


class FakeMessages:
    def __init__(self, response=None, error=None):
        self.response, self.error, self.calls = response, error, []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


def use_fake(monkeypatch, **kwargs):
    messages = FakeMessages(**kwargs)
    client = SimpleNamespace(beta=SimpleNamespace(messages=messages))
    monkeypatch.setattr(story, "get_client", lambda: client)
    monkeypatch.setenv("STORY_GENERATOR", "llm")
    return messages


def reply(text, stop_reason="end_turn"):
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)],
    )


@pytest.fixture
def claim():
    req = make_req()
    return req, calculate(req)


def test_llm_narrative_with_code_computed_summary(monkeypatch, claim):
    messages = use_fake(monkeypatch, response=reply("Владелец уронил телефон."))
    text, source = story.generate_story(*claim)
    assert source == "llm"
    assert text.startswith("Владелец уронил телефон.")
    assert "22 000 руб" in text  # сумма из calculator, а не из модели

    call = messages.calls[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["fallbacks"] == "default"
    assert "iPhone 15" in call["messages"][0]["content"]


@pytest.mark.parametrize("kwargs", [
    {"response": reply("", stop_reason="refusal")},
    {"response": reply("Обрезанный текст", stop_reason="max_tokens")},
    {"response": reply("   ")},
    {"error": anthropic.APIConnectionError(request=None)},
    {"error": TypeError("Could not resolve authentication method")},
])
def test_falls_back_to_template(monkeypatch, claim, kwargs):
    use_fake(monkeypatch, **kwargs)
    text, source = story.generate_story(*claim)
    assert source == "template"
    assert "iPhone 15" in text


class FakeOllama:
    """Подменяет httpx.post: отдаёт ответы по очереди и запоминает запросы."""

    def __init__(self, *contents, done_reason="stop", error=None):
        self.contents, self.done_reason, self.error, self.calls = list(contents), done_reason, error, []

    def __call__(self, url, json, timeout):
        self.calls.append((url, json))
        if self.error:
            raise self.error
        body = {"message": {"content": self.contents.pop(0)}, "done_reason": self.done_reason}
        return httpx.Response(200, json=body, request=httpx.Request("POST", url))


def use_ollama(monkeypatch, fake):
    monkeypatch.setattr(story.httpx, "post", fake)
    monkeypatch.setenv("STORY_GENERATOR", "ollama")
    return fake


GOOD = "1 июля 2025 года владелец уронил iPhone 15, купленный 1 января 2025 года."


def test_ollama_narrative(monkeypatch, claim):
    fake = use_ollama(monkeypatch, FakeOllama(GOOD))
    text, source = story.generate_story(*claim)
    assert source == "ollama"
    assert text.startswith(GOOD)
    assert "22 000 руб" in text

    url, payload = fake.calls[0]
    assert url == "http://localhost:11434/api/chat"
    assert payload["model"] == "qwen3:4b-instruct"
    assert "1 июля 2025 года" in payload["messages"][1]["content"]  # дата словами


def test_theft_facts_omit_total_loss():
    req = make_req("theft")
    assert "полная_гибель" not in story._facts(req, calculate(req))
    req = make_req("water_damage", event_date="2027-01-01")
    assert '"полная_гибель": true' in story._facts(req, calculate(req))


def test_ollama_strips_thinking(monkeypatch, claim):
    use_ollama(monkeypatch, FakeOllama("<think>рассуждаю 42</think>\n" + GOOD))
    text, source = story.generate_story(*claim)
    assert source == "ollama"
    assert "рассуждаю" not in text


def test_ollama_retries_after_bad_answer(monkeypatch, claim):
    fake = use_ollama(monkeypatch, FakeOllama("21 июля 2025 года телефон разбился.", GOOD))
    text, source = story.generate_story(*claim)
    assert source == "ollama"
    assert len(fake.calls) == 2


@pytest.mark.parametrize("fake", [
    FakeOllama("Ремонт стоит 5000 руб.", "Ущерб 50% от стоимости."),
    FakeOllama("В 14 часов 30 минут телефон упал.", "Через 3 дня владелец обратился."),
    FakeOllama(GOOD, GOOD, done_reason="length"),
    FakeOllama(error=httpx.ConnectError("connection refused")),
])
def test_ollama_falls_back_to_template(monkeypatch, claim, fake):
    use_ollama(monkeypatch, fake)
    _, source = story.generate_story(*claim)
    assert source == "template"


@pytest.mark.parametrize("text, ok", [
    ("Куплен 01 января 2025 года, событие 1 июля 2025 года.", True),
    ("iPhone 15 упал.", True),
    ("Событие 2 июля 2025 года.", False),
    ("Куплен 1 июля 2025 года.", True),     # день и месяц — от даты события
    ("Куплен 1 марта 2025 года.", False),   # день есть во входных данных, а дата — нет
    ("Стоимость ремонта 100 ₽.", False),
])
def test_check_narrative(claim, text, ok):
    assert (story.check_narrative(text, claim[0]) is None) == ok


def test_template_mode_skips_llm(monkeypatch, claim):
    messages = use_fake(monkeypatch, response=reply("не должно вызываться"))
    monkeypatch.setenv("STORY_GENERATOR", "template")
    _, source = story.generate_story(*claim)
    assert source == "template"
    assert messages.calls == []
