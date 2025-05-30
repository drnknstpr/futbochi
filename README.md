# Futbotchi

Telegram-болельщик-менеджер, вдохновлённый Тамагочи.

## 🚀 Деплой на Railway

1. Перейди на [https://railway.app](https://railway.app) и авторизуйся через GitHub
2. Создай новый проект → выбери репозиторий `futbotchi`
3. Укажи Root Directory: `railway` (или ту папку, куда скопируешь эти файлы)
4. Добавь переменную окружения `BOT_TOKEN`
5. Убедись, что есть файлы:

- `requirements.txt`
- `Procfile`
- `bot_main_futbotchi.py`
- `start.sh` (опционально)

6. Нажми "Deploy"

Готово — бот будет доступен через Telegram!

## 🛠 Локальный запуск

```bash
pip install -r requirements.txt
python bot_main_futbotchi.py
```
