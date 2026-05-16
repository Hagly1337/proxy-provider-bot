# Proxy Provider Bot 🔐

Telegram-бот для автоматического сбора, валидации и выдачи бесплатных **SOCKS5** прокси.

## Возможности

- Автоматический парсинг SOCKS5 из **25 источников** (GitHub + API)
- Валидация каждого прокси connect-тестом перед сохранением
- Обновление каждые **15 минут**
- Выдача прокси через удобное inline-меню
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

Скрипт запросит `BOT_TOKEN` и `ADMIN_ID` интерактивно и создаст `.env` автоматически.

> ⚠️ **Важно:** файл `.env` содержит ваш токен и **НЕ попадает в Git** (есть в `.gitignore`). В репозитории лежит только `.env.example` — шаблон без секретов.

---

## Локальный запуск (без Docker)

```bash
cp .env.example .env
# отредактируйте .env — укажите BOT_TOKEN и ADMIN_ID
pip install -r requirements.txt
python -m bot.main
```

## Структура

```
├── bot/               # Telegram-бот (aiogram 3.x)
│   ├── main.py        # Точка входа
│   ├── config.py      # Конфигурация
│   ├── handlers/      # Обработчики команд
│   └── keyboards/     # Inline-клавиатуры
├── services/          # Парсинг, валидация, планировщик
├── db/                # SQLite база данных
├── Dockerfile
└── docker-compose.yml
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/help` | Справка |
| 🔐 Получить SOCKS5 | 10 проверенных прокси |
| 📋 Все живые | Полный список рабочих |
| ➕ Добавить | Отправить свои прокси |
| 📊 Статистика | Количество прокси в базе |

## Источники (25 шт.)

Proxifly, Thordata, TheSpeedX, monosans, hookzof, roosterkid, prxchk, vakhov, proxygenerator1, ClearProxy, officialputuid, iplocate, B4RC0DE-TM, saschazesiger, mmpx12, HyperBeats, manuGMG, ShiftyTR, BlackSnowDot, ProxyScrape (v1+v2), proxy-list.download, openproxylist, proxyspace.pro

## Технологии

- Python 3.11+
- aiogram 3.x
- aiohttp + aiohttp-socks
- SQLite (aiosqlite)
- APScheduler
- Docker
