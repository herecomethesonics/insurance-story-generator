# Генератор страховых историй

Генерирует страховую историю по данным об объекте и прогнозирует сумму компенсации.
MVP — смартфоны. План проекта: [docs/PLAN.txt](docs/PLAN.txt).

## Структура

```
backend/
  app/
    models.py      — модели данных (объект, полис, событие, результат)
    calculator.py  — детерминированный расчёт компенсации
    story.py       — генерация текста истории (пока шаблоны, далее — LLM)
    main.py        — FastAPI: POST /api/claims/estimate, страница на /
    static/        — веб-интерфейс
  tests/           — тесты расчёта и API
```

## Быстрый запуск

Двойной щелчок по `start.bat`: запускает сервер с локальной моделью (Ollama) и открывает
браузер. Режим генерации меняется в начале файла (`STORY_GENERATOR`).

## Установка и запуск вручную

Нужен Python 3.10+ (`winget install Python.Python.3.12`).

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd backend
pytest
uvicorn app.main:app --reload
```

Интерфейс: http://127.0.0.1:8000, документация API: http://127.0.0.1:8000/docs

## Локальная модель через Ollama

Бесплатно, без интернета, данные не покидают компьютер. Качество текста ниже, чем у Claude.

```powershell
ollama pull qwen3:4b-instruct
$env:STORY_GENERATOR = "ollama"
# необязательно: $env:OLLAMA_MODEL = "qwen3:4b-instruct"; $env:OLLAMA_URL = "http://localhost:11434"
```

Нужен вариант модели **без рассуждений** (`-instruct`). Обычный `qwen3:4b` всегда
рассуждает: ответ ~100 с вместо ~10 с, отключить это не удаётся.

Ответ локальной модели проверяется: если в тексте есть суммы, проценты или числа,
которых нет во входных данных (например, неверная дата), делается вторая попытка,
затем используется шаблон.
