import pytest


@pytest.fixture(autouse=True)
def no_real_llm(monkeypatch):
    # Тесты не должны ходить в Claude API и тратить деньги.
    monkeypatch.setenv("STORY_GENERATOR", "template")
