# Telegram-бот: учёт личных финансов

Бот на Python (aiogram 3) с асинхронной БД PostgreSQL и деплоем через Docker.

## Возможности

- Запись **расходов** и **доходов** с категориями и комментарием
- **Баланс**, расходы за 7 дней
- **Статистика** за текущий месяц по категориям
- **История** последних 15 операций
- Данные каждого пользователя Telegram изолированы по `telegram_id`

## Быстрый старт (Windows / локально)

1. Создайте бота у [@BotFather](https://t.me/BotFather) и скопируйте токен.

2. Запустите PostgreSQL (один раз или после перезагрузки):

```powershell
docker compose up db -d
```

3. Скопируйте пример окружения и укажите токен:

```powershell
copy .env.example .env
# Отредактируйте .env: BOT_TOKEN=...
```

4. Установите зависимости и запустите бота:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m bot.main
```

База по умолчанию: `postgresql+asyncpg://finance:finance@localhost:5432/finance` (порт 5432 проброшен из `docker-compose.yml`).

### Миграция из SQLite

Если раньше использовался файл `data/finance.db`:

1. Убедитесь, что PostgreSQL запущен (`docker compose up db -d`).
2. Проверьте, что в `.env` указан `DATABASE_URL` для PostgreSQL.
3. Выполните перенос:

```powershell
python -m scripts.migrate_sqlite_to_postgres
# только посмотреть объём данных:
python -m scripts.migrate_sqlite_to_postgres --dry-run
# другой путь к SQLite:
python -m scripts.migrate_sqlite_to_postgres --sqlite-path D:\backup\finance.db
```

Скрипт сохраняет `id` и даты, пропускает пользователей с тем же `telegram_id`, уже существующих в PostgreSQL, и обновляет sequences. Повторный запуск безопасен (дубликаты транзакций по `id` не создаются).

### Нет доступа к api.telegram.org

Если при запуске ошибка `Cannot connect to host api.telegram.org:443` — с вашей сети Telegram API недоступен (блокировка/провайдер).

**Варианты:**

1. **VPN** на компьютере — включите и снова `python -m bot.main`.
2. **Локальный прокси** (Clash, v2rayN, Hiddify и т.п.) — узнайте порт (часто `7890` для HTTP или `1080` для SOCKS5) и добавьте в `.env`:
   ```
   BOT_PROXY=http://127.0.0.1:7890
   ```
   или
   ```
   BOT_PROXY=socks5://127.0.0.1:1080
   ```
3. **VPS за рубежом** — бот на сервере (см. ниже) обычно работает без прокси.

После смены `.env` установите зависимость: `pip install -r requirements.txt`.

## Деплой на VPS (Docker + PostgreSQL)

### 1. Подготовка сервера

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
sudo systemctl enable --now docker
```

### 2. Загрузка проекта

```bash
sudo mkdir -p /opt/finance-bot
sudo chown $USER:$USER /opt/finance-bot
cd /opt/finance-bot
# git clone <your-repo> .   или scp файлы на сервер
```

### 3. Настройка `.env`

```bash
cp .env.example .env
nano .env
```

Минимум:

```
BOT_TOKEN=123456:ABC...
```

В `docker-compose.yml` для сервиса `bot` URL PostgreSQL задан как `postgresql+asyncpg://finance:finance@db:5432/finance`. Менять не нужно, если не меняли пользователя/пароль в compose.

### 4. Запуск

```bash
docker compose up -d --build
docker compose logs -f bot
```

### 5. Автозапуск (systemd)

```bash
sudo cp deploy/finance-bot.service /etc/systemd/system/
# В unit-файле проверьте WorkingDirectory=/opt/finance-bot
sudo systemctl daemon-reload
sudo systemctl enable finance-bot
sudo systemctl start finance-bot
```

## Команды бота

| Команда / кнопка | Действие |
|------------------|----------|
| `/start` | Приветствие и меню |
| `/expense`, «➕ Расход» | Добавить расход |
| `/income`, «➕ Доход» | Добавить доход |
| `/balance`, «💰 Баланс» | Баланс |
| `/stats`, «📊 Статистика» | Статистика за месяц |
| `/history`, «📋 История» | Последние операции |

## Структура проекта

```
bot/
  main.py           # точка входа
  config.py         # настройки из .env
  handlers/         # обработчики команд
  database/         # модели SQLAlchemy
  services/         # бизнес-логика
  keyboards/        # клавиатуры
docker-compose.yml  # бот + PostgreSQL
Dockerfile
```

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен от @BotFather |
| `DATABASE_URL` | `postgresql+asyncpg://finance:finance@localhost:5432/finance` (локально) или `@db:5432` в Docker |
| `BOT_PROXY` | Опционально: `http://127.0.0.1:7890` или `socks5://127.0.0.1:1080` |

## Задачи вместо финансов

Тот же каркас (aiogram + SQLAlchemy + Docker) можно расширить отдельной сущностью `Task` и хендлерами `/add_task`, `/list`. Сейчас реализован именно **финансовый** трекер.
