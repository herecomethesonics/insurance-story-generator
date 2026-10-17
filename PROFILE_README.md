<div align="center">

# 👋 Привет! Я herecomesthesonics

### Превращаю сухие данные в живые истории, а истории — в работающий код

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=20&pause=1000&color=36BCF7&center=true&vCenter=true&width=600&lines=Python+%E2%80%A2+FastAPI+%E2%80%A2+LLM;%D0%9B%D0%BE%D0%BA%D0%B0%D0%BB%D1%8C%D0%BD%D1%8B%D0%B5+%D0%BC%D0%BE%D0%B4%D0%B5%D0%BB%D0%B8+%D0%B8+Claude+API;%D0%A2%D0%B5%D0%BA%D1%81%D1%82+%D0%BF%D0%B8%D1%88%D0%B5%D1%82+%D0%BC%D0%BE%D0%B4%D0%B5%D0%BB%D1%8C%2C+%D1%86%D0%B8%D1%84%D1%80%D1%8B+%E2%80%94+%D0%BA%D0%BE%D0%B4" alt="Typing SVG" />

</div>

---

## 🧭 Кто я

Я разработчик, которому интересно, где заканчивается «магия» нейросетей и начинается честная инженерия.
Люблю проекты, в которых языковая модель делает то, что умеет лучше всего — пишет понятный человеческий текст, —
а всё, что требует точности, остаётся за детерминированным, покрытым тестами кодом.

- 🔭 Сейчас работаю над **генератором историй страховых случаев**: по данным об объекте и событии сервис
  рассказывает, что произошло, и прогнозирует сумму компенсации
- 🧠 Изучаю, как подружить облачные LLM и локальные модели так, чтобы приложение работало **всегда** —
  даже без интернета и ключей API
- 🛡️ Верю, что модели нельзя доверять цифры: каждое число в сгенерированном тексте должно сверяться с исходными данными
- ⚡ Забавный факт: я знаю, почему `.bat`-файл с переводами строк LF может молча пропускать команды — и больше никогда на это не попадусь

---

## 🚀 Флагманский проект

### 📖 Story Generator

> *Опишите смартфон, полис и что случилось — получите связную историю и обоснованную сумму выплаты.*

| Что внутри | Как устроено |
|---|---|
| ✍️ **Генерация текста** | Claude API, локальная модель через Ollama или шаблоны — на выбор |
| 🧮 **Расчёт компенсации** | Чистая детерминированная логика, никаких «галлюцинаций» в деньгах |
| 🔍 **Проверка ответа модели** | Если в тексте появились числа, которых нет во входных данных, — повторная попытка, затем надёжный шаблон |
| 🌐 **API и интерфейс** | FastAPI, автодокументация, лёгкий веб-интерфейс |
| ✅ **Тесты** | pytest для расчётов, генерации и API — без обращений к внешним сервисам |
| 🖱️ **Запуск** | Один двойной щелчок по `start.bat` — и браузер уже открыт |

**Принцип проекта:** *модель рассказывает, код считает.*

---

## 🛠️ Технологии

<p>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white" />
  <img src="https://img.shields.io/badge/pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white" />
  <img src="https://img.shields.io/badge/Claude_API-D97757?style=for-the-badge&logo=anthropic&logoColor=white" />
  <img src="https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white" />
  <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" />
  <img src="https://img.shields.io/badge/PowerShell-5391FE?style=for-the-badge&logo=powershell&logoColor=white" />
  <img src="https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" />
</p>

---

## 💡 Во что я верю

```python
def good_software(idea):
    text   = llm.write_story(idea)        # пусть модель будет красноречивой
    amount = calculator.compute(idea)     # а цифры — точными
    assert numbers_in(text) <= numbers_in(idea), "Модель, не выдумывай!"
    return text, amount
```

1. **Надёжность важнее эффектности.** Если модель недоступна — приложение всё равно отвечает.
2. **Приватность по умолчанию.** Локальная модель = данные не покидают компьютер.
3. **Тесты — это документация, которая не врёт.**
4. **Простой запуск — уважение к пользователю.** Никто не должен читать три страницы, чтобы нажать «Старт».

---

## 📊 Статистика

<div align="center">

<img height="165" src="https://github-readme-stats.vercel.app/api?username=herecomesthesonics&show_icons=true&theme=tokyonight&hide_border=true" />
<img height="165" src="https://github-readme-stats.vercel.app/api/top-langs/?username=herecomesthesonics&layout=compact&theme=tokyonight&hide_border=true" />

<img src="https://github-readme-streak-stats.herokuapp.com/?user=herecomesthesonics&theme=tokyonight&hide_border=true" />

</div>

---

## 🤝 Давайте общаться

Открыт к обсуждению идей на стыке **LLM, бэкенда и прикладной автоматизации**.
Есть интересная задача, где тексту нужна душа, а цифрам — точность? Открывайте issue или заглядывайте в мои репозитории!

<div align="center">

---

*«Хорошая история начинается с точных данных»* ✨

<img src="ttps://komarev.com/ghpvc/?username=herecomesthesonics&color=blueviolet&style=flat-square&label=Просмотры+профилhя" />

</div>
