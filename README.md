# Proxy Provider Bot 🔐

Telegram-бот для автоматического сбора, валидации и выдачи бесплатных **SOCKS5** прокси.

## Возможности

- Автоматический парсинг SOCKS5 из **25 источников** (GitHub + API)
- Валидация каждого прокси connect-тестом перед сохранением
- Обновление каждые **15 минут**
- Выдача прокси через удобное inline-меню
- Любой пользователь может добавить свои прокси через ЛС

## Деплой на VPS одной командой

Требования: VPS с установленным **Docker** и **Docker Compose**.

```bash
git clone https://github.com/Hagly1337/proxy-provider-bot.git && cd proxy-provider-bot && cp .env.example .env && nano .env
```

В `nano` вставьте ваш токен и ID, сохраните (`Ctrl+O`, `Enter`, `Ctrl+X`), затем:

```bash
docker-compose up -d --build
```

**Готово!** Бот работает в фоне. Логи: `docker-compose logs -f`

> ⚠️ **Важно:** файл `.env` содержит ваш токен и **НЕ попадает в Git** (есть в `.gitignore`). В репозитории лежит только `.env.example` — шаблон без секретов.

### Альтернатива: одна строка (если токен известен)

```bash
git clone https://github.com/Hagly1337/proxy-provider-bot.git && cd proxy-provider-bot && echo "BOT_TOKEN=123456:ABC-DEF" > .env && echo "ADMIN_ID=your_id" >> .env && docker-compose up -d --build
```

Замените `123456:ABC-DEF` на реальный токен и `your_id` на ваш Telegram ID.

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
