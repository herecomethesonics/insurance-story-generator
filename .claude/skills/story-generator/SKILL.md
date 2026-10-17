---
name: story-generator
description: Работа с репозиторием «Генератор страховых историй» (FastAPI, C:\ZCPROJ, GitHub herecomethesonics/insurance-story-generator). Использовать при любой задаче в этом проекте — разобраться в структуре, запустить или перезапустить сервис, изменить расчёт, генерацию текста или страницу, добавить тип события, обновить README.md / PROJECT.md, прогнать тесты и проверки, подготовить или выполнить публикацию на GitHub.
---

# Генератор страховых историй

Сервис по данным о смартфоне, полисе и событии выдаёт текст истории страхового случая
и прогноз выплаты. Главный принцип, который нельзя нарушать: **модель рассказывает, код считает.**

Среда: Windows, PowerShell 5.1, Python из `C:\ZCPROJ\.venv`. Git не установлен — публикация
идёт через `gh` (см. «Публикация»). Язык проекта — русский: комментарии, тексты, документация.

## Структура

```
start.bat                 запуск двойным щелчком (режим ollama), CRLF — не менять на LF
README.md                 установка и запуск (для разработчика)
PROJECT.md                описание: название, решение задачи, пользователь
PROFILE_README.md         README профиля GitHub, к сервису не относится
docs/PLAN.txt             исходный план проекта
backend/
  requirements.txt, pytest.ini (pythonpath = ., тесты запускать из backend/)
  app/models.py           Pydantic: Phone, Policy, Event, ClaimRequest, CompensationResult, ClaimResponse
  app/calculator.py       детерминированный расчёт выплаты, все коэффициенты — константы вверху
  app/story.py            текст: llm (Claude) | ollama | template, проверка чисел, DISCLAIMER
  app/main.py             FastAPI: GET / (index.html, no-cache), POST /api/claims/estimate, /static
  app/static/index.html   форма без сборки, весь JS внутри
  tests/conftest.py       autouse: STORY_GENERATOR=template — тесты не ходят в API
  tests/test_calculator.py, tests/test_story.py
```

Поток запроса: `main.estimate` → `calculator.calculate` → `story.generate_story` →
`ClaimResponse(compensation, story, story_source, disclaimer)`.

## Инварианты (проверять при каждом изменении)

1. **Суммы считает только `calculator.py`.** Модель не получает денег: `_facts()` передаёт лишь
   устройство, даты словами, состояние, событие, полную гибель. Итоговое предложение с суммами
   (`_summary`) добавляет код. Не добавлять суммы в `_facts` и `SYSTEM_PROMPT`.
2. **Приложение отвечает всегда.** Любая ошибка модели (сеть, нет ключа → `TypeError`, отказ,
   `max_tokens`, пустой ответ) → шаблон и `story_source="template"`. Новые провайдеры обязаны
   возвращать `None` при сбое, а не бросать исключение.
3. **Ответ локальной модели проверяется** `check_narrative`: нет «руб/₽/%», нет чисел не из
   входных данных, пары «день месяц» совпадают с настоящими датами. Иначе повтор, затем шаблон.
4. **Каждый результат помечен** `DISCLAIMER`; модели запрещено выдумывать ФИО, адреса, номера
   документов и названия реальных организаций. Не ослаблять — это защита от фиктивных заявлений.
5. **Никаких чужих брендов.** Проект публичный и независимый: логотипы, названия и цвета
   реальных страховых компаний не использовать (логотип удалён, тест
   `test_page_served_without_logo` это проверяет).
6. **Тесты не тратят деньги и не требуют сети**: Claude подменяется `use_fake`, Ollama —
   `FakeOllama`. Новые тесты строятся так же.
7. Модель Claude — `MODEL = "claude-opus-5-5"` в `story.py`; тест проверяет имя модели.
   Перед изменением вызова API загрузить скилл `claude-api`.

## Запуск сервиса

Как в `start.bat`, но в фоне (`run_in_background: true`), с абсолютными путями:

```powershell
$env:STORY_GENERATOR="ollama"; $env:OLLAMA_MODEL="qwen3:4b-instruct"; Set-Location C:\ZCPROJ\backend; C:\ZCPROJ\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

- Режим: `ollama` (локально), `llm` (нужен `ANTHROPIC_API_KEY`), `template`.
- После старта подождать ~5 с и проверить: `Invoke-WebRequest http://127.0.0.1:8000/ -UseBasicParsing`.
  Первый запрос сразу после запуска может не пройти — это не ошибка, повторить.
- Ollama: `Invoke-WebRequest http://localhost:11434/api/version`. Если не отвечает — текст будет
  по шаблону; сообщить пользователю, расчёт работает.
- Перезапуск: остановить фоновую задачу (`TaskStop`), запустить заново. Порт занят → найти
  процесс: `Get-NetTCPConnection -LocalPort 8000 -State Listen`.
- Сервер без `--reload`: после правок в `app/*.py` нужен перезапуск; `index.html` отдаётся
  с диска сразу. Если пользователь видит старую страницу — сначала проверить, что отдаёт сервер,
  затем советовать Ctrl+F5.
- Открыть браузер: `Start-Process http://127.0.0.1:8000`. API-документация: `/docs`.

## Внесение изменений

- Стиль: как в окружающем коде — короткие русские комментарии «почему», type hints,
  константы вверху модуля, без лишних абстракций.
- **Новый тип события** затрагивает все слои сразу:
  1. `models.EventType` — значение;
  2. `calculator.py` — ветка расчёта (`REPAIR_SHARE` или своя логика);
  3. `story.EVENT_LABELS` и `story.EVENT_SCENARIOS` — иначе `KeyError`;
  4. `index.html` — `<option>` в «Тип»;
  5. тесты расчёта и шаблона; `PROJECT.md` — список ущерба по типам.
- **Новое поле запроса**: `models.py` → форма и `payload` в `index.html` → `_facts` (только если
  это не сумма) → `_allowed_numbers`, если поле может появиться в тексте числом.
- **Коэффициенты** меняются только в константах `calculator.py`; обновить ожидаемые суммы
  в тестах (`22_000` в `test_api_estimate` и `test_story.py`) и описание в `PROJECT.md`.
- После изменения — тесты и перезапуск сервера, если он запущен.

## Документация

- `README.md` — для разработчика: структура, быстрый запуск, ручная установка, режимы Claude
  и Ollama. Обновлять при изменении файлов, команд запуска, переменных окружения, зависимостей.
- `PROJECT.md` — для читателя репозитория: «Название», «Какую задачу решает» (включая правила
  расчёта), «Пользователь». Обновлять при изменении коэффициентов, режимов, типов объектов
  и событий, ограничений.
- Писать по-русски, коротко, без маркетинга; не обещать того, чего нет (это MVP, коэффициенты
  условные, не страховой документ). Команды — для PowerShell.
- Сверять документацию с кодом: имена переменных окружения, модель по умолчанию, порт, пути.

## Проверка ошибок

Запускать скрипт проверки — он прогоняет тесты, компиляцию и проверки перед публикацией:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ZCPROJ\.claude\skills\story-generator\scripts\check.ps1
```

Только тесты: `Set-Location C:\ZCPROJ\backend; C:\ZCPROJ\.venv\Scripts\python.exe -m pytest -q`.

Если падает — читать вывод, чинить причину, а не тест. Тест менять, только когда поведение
изменено намеренно, и сказать об этом пользователю. Ошибку в работающем сервисе искать
в выводе фоновой задачи uvicorn (предупреждения `story.py` пишет через `log.warning`).

## Публикация

Репозиторий: `herecomethesonics/insurance-story-generator` (public, ветка `main`).
Публикация — действие наружу: выполнять только по просьбе пользователя.

1. `check.ps1` без ошибок (тесты, нет ключей, нет логотипов и лишних файлов).
2. Документация соответствует коду (см. выше).
3. Список файлов — всё, кроме `.venv/`, `__pycache__/`, `.pytest_cache/`, `*.pyc`, `.env`, `*.db`.
   Скилл `.claude/skills/story-generator/` публикуется вместе с проектом.
4. Загрузка без Git — через Contents API, по файлу; для изменения существующего файла нужен
   его `sha`: `gh api repos/herecomethesonics/insurance-story-generator/contents/<путь> --jq .sha`,
   затем `PUT` с полями `message`, `content` (base64 байтов файла) и `sha`. JSON-тело писать во
   временный файл в UTF-8 без BOM и передавать через `--input`.
   Удаление файла — `DELETE` с `message` и `sha`.
5. Проверить результат: `gh repo view herecomethesonics/insurance-story-generator --json visibility`
   и список файлов в дереве `git/trees/HEAD?recursive=1`.
6. Если Git установлен (`git --version`), лучше обычный путь: `git init`, `git remote add origin`,
   коммит и `git push` — один коммит вместо коммита на файл.

`PROFILE_README.md` относится к профилю: работает только в репозитории
`herecomethesonics/herecomethesonics`, а в нём ещё указано имя `herecomesthesonics` (с лишней «s»).
При публикации профиля напомнить об этом пользователю.
