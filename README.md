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

Параметры PostgreSQL задаются переменными `POSTGRES_*` в `.env` (см. `.env.example`). Порт `5432` проброшен в `docker-compose.yml` для локального доступа к контейнеру `db`.

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

Для сервиса `bot` в `docker-compose.yml` переопределены `POSTGRES_HOST=db` и остальные `POSTGRES_*` (в согласовании с сервисом `db`). При смене пользователя или пароля в блоке `db` обновите и блок `environment` у `bot`.

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
| `POSTGRES_HOST` | Хост БД (локально обычно `localhost`, в Docker для бота задаётся `db` в compose) |
| `POSTGRES_PORT` | Порт (по умолчанию `5432`) |
| `POSTGRES_USER` | Имя пользователя БД |
| `POSTGRES_PASS` | Пароль пользователя БД |
| `POSTGRES_DB` | Имя базы данных |
| `BOT_PROXY` | Опционально: URL HTTP или SOCKS5-прокси для сессии Telegram |

## Задачи вместо финансов

Тот же каркас (aiogram + SQLAlchemy + Docker) можно расширить отдельной сущностью `Task` и хендлерами `/add_task`, `/list`. Сейчас реализован именно **финансовый** трекер.
