@echo off
chcp 65001 >nul
title Генератор страховых историй

rem Запуск генератора страховых историй.
rem Режим генерации текста: ollama (локальная модель), llm (Claude API) или template.
set STORY_GENERATOR=ollama
set OLLAMA_MODEL=qwen3:4b-instruct

cd /d "%~dp0backend"

if not exist "..\.venv\Scripts\python.exe" (
    echo Не найдено виртуальное окружение .venv. Порядок установки описан в README.md.
    pause
    exit /b 1
)

curl -s -o nul http://localhost:11434/api/version
if errorlevel 1 (
    echo ВНИМАНИЕ: Ollama не отвечает. Запустите Ollama, иначе текст будет по шаблону.
    echo.
)

echo Адрес: http://127.0.0.1:8000
echo Для остановки закройте это окно или нажмите Ctrl+C.
echo.

rem Браузер открывается через 3 секунды, когда сервер уже успеет запуститься.
start "" /b cmd /c "timeout /t 3 >nul & start http://127.0.0.1:8000"

"..\.venv\Scripts\python.exe" -m uvicorn app.main:app --port 8000
pause
