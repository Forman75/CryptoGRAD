# 🔐 CryptoGRAD — обучающий криптографический стенд
---

## 🇷🇺 Описание

**CryptoGRAD** — это настольное приложение на **Python + CustomTkinter** для интерактивного изучения шифров и протоколов: **Цезарь**, **RSA (OAEP)**, **AES (ECB/CBC/CTR/GCM)**.
Акцент — на **образовательных анимациях**, **пошаговой визуализации** и **практических заданиях**.

---

## ✨ Возможности

* 🎞️ **Анимации шифрования и расшифрования**:

  * **Цезарь** — рус/англ алфавиты, подсветка символов и сдвига.
  * **RSA (OAEP/SHA-1)** — от исходного текста до шифртекста и обратно, с диаграммами.
  * **AES (ECB/CBC/CTR/GCM)** — конвейерные схемы, XOR, счётчики, теги GCM.
* 🧪 **Практика**:

  * Задачи по Цезарю (брутфорс-подсказки, проверка ответов).
* 📚 **Учебник**:

* 🧰 **Удобный интерфейс**:

  * Тёмная тема, всплывающие подсказки, контекстное меню (копировать/вставить), отдельные окна с результатами.

---

## 🚀 Установка и запуск

### Требования

* Python **3.10+**
* ОС: Windows / macOS / Linux

### Установка

```bash
# 1) Клонируйте репозиторий
git clone https://github.com/Forman75/CryptoGRAD.git
cd CryptoGRAD

# 2) Создайте окружение (опционально, но рекомендуется)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3) Установите зависимости
pip install -r requirements.txt
```

**requirements.txt**:

```
customtkinter
pycryptodome
```

### Запуск

```bash
python main.py
```

---

## 🧭 Навигация по приложению

* **Шифр Цезаря** — введите текст, задайте сдвиг, запустите анимацию шифрования/расшифрования.
* **RSA (OAEP)** — сгенерируйте ключи или вставьте свои (PEM), введите текст/HEX и запустите анимацию.

  * Результат показывается в отдельном окне (шифртекст/открытый текст).
* **AES** — выберите режим, задайте ключ и IV/Nonce (или сгенерируйте), введите данные и запустите анимацию.

  * Результат также выводится в отдельном окне.
* **Практика** — задания для закрепления (например, угадать сдвиг у Цезаря).
* **Учебник** — справочник с прокруткой, подстраивается под размер окна.

---

## 🔐 Безопасность

* RSA использует **OAEP (SHA-1)** в образовательной анимации, что совместимо с большинством реализаций (в учебных целях).
* AES поддерживает корректные размеры IV/Nonce в соответствующих режимах.
* Валидация ключей и длины шифртекста предотвращает «магические» расшифровки при ошибках.

> Приложение — **учебное**. Для продакшн-сценариев применяйте актуальные практики и требования безопасности.

---

## 🧩 Дорожная карта

* [ ] Расширенные задания (RSA/AES), автогенерация наборов.
* [ ] Поддержка OAEP с SHA-256 в интерактивной анимации.
* [ ] Экспорт анимаций (GIF/видео).

---

## 🤝 Вклад

PR’ы приветствуются!
Сначала создайте issue с описанием улучшений или ошибок, затем присылайте Pull Request.

---

# 🔐 CryptoGRAD — cryptography learning workstation

## 🇬🇧 Overview

**CryptoGRAD** is a **Python + CustomTkinter** desktop app to **learn cryptography interactively**: **Caesar**, **RSA (OAEP)**, and **AES (ECB/CBC/CTR/GCM)**.
It focuses on **step-by-step educational animations**, **clear visual pipelines**, and **practice tasks**.

---

## ✨ Features

* 🎞️ **Animations** for encryption and decryption:

  * **Caesar** — RU/EN alphabets, character shift highlighting.
  * **RSA (OAEP/SHA-1)** — from plaintext to ciphertext and back, with diagrams.
  * **AES (ECB/CBC/CTR/GCM)** — pipeline visuals: XOR, counters, GCM tags.
* 🧪 **Practice**:

  * Caesar challenges (bruteforce hints, answer checks).
* 📚 **Tutor**:

* 🧰 **UX niceties**:

  * Dark theme, tooltips, context menu (copy/paste), separate result windows.

---

## 🚀 Installation & Run

### Requirements

* Python **3.10+**
* OS: Windows / macOS / Linux

### Setup

```bash
git clone https://github.com/Forman75/CryptoGRAD.git
cd CryptoGRAD

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

**requirements.txt**:

```
customtkinter
pycryptodome
```

### Run

```bash
python main.py
```

---

## 📦 One-file build (PyInstaller)

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --add-data "assets;assets" main.py
# Final binary in dist/
```

> Use `resource_path` to access packaged resources.

---

## 🧭 App structure

* **Caesar** — type text, set shift, run animation (encrypt/decrypt).
* **RSA (OAEP)** — generate or paste PEM keys, type text/HEX, run animation.

  * Results appear in a dedicated window (ciphertext/plaintext).
* **AES** — pick mode, set key and IV/Nonce (or generate), type data, run animation.

  * Results appear in a dedicated window as well.
* **Practice** — tasks to test your skills (e.g., Caesar shift challenge).
* **Tutor** — scrollable, non-editable reference that adapts to window size.

---

## 🔐 Security notes

* RSA animation uses **OAEP (SHA-1)** for compatibility in educational context.
* AES modes use proper IV/Nonce sizes.
* Strict key/length checks prevent accidental “lucky” decryptions with wrong keys.

> This is an **educational** tool. Use current best practices for production systems.

---

## 🧩 Roadmap

* [ ] More tasks (RSA/AES) with auto-generated datasets.
* [ ] OAEP with SHA-256 in interactive animation.
* [ ] Export animations (GIF/video).

---

## 🤝 Contributing

PRs are welcome!
Please open an issue to discuss improvements/bugs before submitting a PR.


---

**Happy learning & hacking (the good kind)!** ✨🔐
