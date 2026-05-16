# Proxy Provider Bot 🔐

Telegram-бот для автоматического сбора, валидации и выдачи бесплатных **SOCKS5** прокси из **39 источников** с поддержкой распределённой проверки через worker-ноды.

## Возможности

- Автоматический парсинг SOCKS5 из **39 источников** (GitHub + API)
- Валидация до **7 000 прокси за цикл** (200 параллельных проверок)
- Обновление каждые **15 минут**
- **Распределённая валидация** — подключай worker-ноды для ускорения
- **GeoIP** — автоматическое определение страны каждого прокси
- **Скачивание .txt** — все живые прокси одним файлом
- **Фильтр по странам** — выбирай прокси нужной страны
- Дедупликация по IP — один IP = одна запись
- Админ-панель с управлением задачами и мониторингом диска
- Любой пользователь может добавить свои прокси через ЛС

## Деплой на VPS — одна команда

Работает на чистом Ubuntu/Debian. Скрипт сам установит **Docker**, **Docker Compose**, **Git**, склонирует репо, спросит токен и запустит бота:

```bash
curl -fsSL https://raw.githubusercontent.com/Hagly1337/proxy-provider-bot/main/setup.sh | bash
```

Или вручную:

```bash
git clone https://github.com/Hagly1337/proxy-provider-bot.git
cd proxy-provider-bot
bash setup.sh
```

Скрипт запросит `BOT_TOKEN`, `ADMIN_ID` и `API_SECRET` интерактивно и создаст `.env` автоматически.

> ⚠️ **Важно:** файл `.env` содержит ваш токен и **НЕ попадает в Git** (есть в `.gitignore`). В репозитории лежит только `.env.example` — шаблон без секретов.

---

## Распределённая валидация (Worker-ноды)

Master сервер раздаёт батчи прокси через HTTP API. Workers берут, проверяют, отдают результаты.

```
┌─────────────────────┐
│   MASTER (основной)  │
│  Бот + БД + API:8080 │◄── Workers подключаются
│  + своя валидация    │
└──────────┬──────────┘
     ┌─────┴─────┐
     ▼           ▼
 Worker #1   Worker #2  ... N
```

### Запуск worker на дополнительном VPS

```bash
git clone https://github.com/Hagly1337/proxy-provider-bot.git
cd proxy-provider-bot/worker
nano docker-compose.yml   # указать IP мастера и API_SECRET
docker compose up -d --build
```

---

## Локальный запуск (без Docker)

```bash
cp .env.example .env
# отредактируйте .env — укажите BOT_TOKEN, ADMIN_ID, API_SECRET
pip install -r requirements.txt
python -m bot.main
```

## Структура

```
├── bot/               # Telegram-бот (aiogram 3.x)
│   ├── main.py        # Точка входа + API сервер
│   ├── config.py      # Конфигурация
│   ├── handlers/      # Обработчики команд
│   └── keyboards/     # Inline-клавиатуры
├── services/          # Парсинг, валидация, GeoIP, планировщик, API
├── db/                # SQLite база данных
├── worker/            # Worker-нода для распределённой проверки
├── Dockerfile
└── docker-compose.yml
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/help` | Справка |
| `/admin` | Админ-панель (только для ADMIN_ID) |
| 🔐 Получить SOCKS5 | 10 проверенных прокси |
| 📋 Все живые | Полный список рабочих |
| 📄 Скачать .txt | Скачать все живые прокси файлом |
| 🌍 По странам | Фильтр прокси по стране |
| ➕ Добавить | Отправить свои прокси |
| 📊 Статистика | Количество прокси в базе |

## Админ-панель

- ▶️ Запуск / ⏹ Остановка цикла проверки
- 🔄 Прогресс валидации в реальном времени
- 💾 Свободное место на диске
- 📊 Статистика БД

## Источники (39 шт.)

Proxifly, ClearProxy, prxchk, r00tee, VPSLabCloud, Thordata, iplocate, gfpcom, TheSpeedX (2 репо), monosans (2 списка), jetkai, thenasty1337, proxygenerator1, hookzof, roosterkid, vakhov, officialputuid, B4RC0DE-TM, saschazesiger, mmpx12, HyperBeats, manuGMG, ShiftyTR, BlackSnowDot, ebrasha/abdal-proxy-hub, ProxyScrape (v1+v2), proxy-list.download, openproxylist, proxyspace.pro, Geonode API, sunny9577

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен Telegram-бота |
| `ADMIN_ID` | Telegram ID администратора |
| `API_PORT` | Порт API для worker-нод (по умолчанию 8080) |
| `API_SECRET` | Секретный ключ для авторизации worker-нод |

## Технологии

- Python 3.11+
- aiogram 3.x
- aiohttp + aiohttp-socks
- SQLite (aiosqlite)
- APScheduler
- GeoIP2 (GeoLite2)
- Docker + Docker Compose
