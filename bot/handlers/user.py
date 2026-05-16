import logging

from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import back_menu, main_menu
from db.database import get_alive_proxies, get_all_alive_proxies, get_stats

router = Router()
logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "👋 <b>Proxy Provider Bot</b>\n\n"
    "Бот автоматически собирает и проверяет бесплатные <b>SOCKS5</b> прокси "
    "из 25 открытых источников.\n\n"
    "Выберите действие:"
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=main_menu, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = (
        "ℹ️ <b>Помощь</b>\n\n"
        "/start — главное меню\n"
        "/help — эта справка\n\n"
        "🔐 <b>Получить SOCKS5</b> — выдаёт 10 проверенных прокси\n"
        "📋 <b>Все живые</b> — выдаёт полный список рабочих прокси\n"
        "➕ <b>Добавить</b> — отправьте прокси в формате ip:port\n"
        "📊 <b>Статистика</b> — текущее количество прокси в базе"
    )
    await message.answer(text, reply_markup=main_menu, parse_mode="HTML")


@router.callback_query(F.data == "back_menu")
async def cb_back_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        WELCOME_TEXT, reply_markup=main_menu, parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "get_socks5_10")
async def cb_get_socks5_10(callback: CallbackQuery) -> None:
    proxies = await get_alive_proxies(limit=10)
    if not proxies:
        await callback.message.edit_text(
            "😔 Пока нет проверенных прокси. Попробуйте позже.",
            reply_markup=back_menu,
            parse_mode="HTML",
        )
        await callback.answer()
        return

    lines = [f"<code>{ip}:{port}</code>" for ip, port in proxies]
    text = f"🔐 <b>SOCKS5 прокси ({len(proxies)} шт):</b>\n\n" + "\n".join(lines)
    await callback.message.edit_text(text, reply_markup=back_menu, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "get_socks5_all")
async def cb_get_socks5_all(callback: CallbackQuery) -> None:
    proxies = await get_all_alive_proxies()
    if not proxies:
        await callback.message.edit_text(
            "😔 Пока нет проверенных прокси. Попробуйте позже.",
            reply_markup=back_menu,
            parse_mode="HTML",
        )
        await callback.answer()
        return

    lines = [f"{ip}:{port}" for ip, port in proxies]
    full_text = "\n".join(lines)

    if len(full_text) > 3500:
        chunks = []
        current_chunk: list[str] = []
        current_len = 0
        for line in lines:
            if current_len + len(line) + 1 > 3500:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_len = 0
            current_chunk.append(line)
            current_len += len(line) + 1
        if current_chunk:
            chunks.append("\n".join(current_chunk))

        await callback.message.edit_text(
            f"📋 <b>Всего живых SOCKS5: {len(proxies)}</b>\n"
            "Список слишком длинный, отправляю частями…",
            reply_markup=back_menu,
            parse_mode="HTML",
        )
        for i, chunk in enumerate(chunks, 1):
            await callback.message.answer(
                f"<b>Часть {i}/{len(chunks)}:</b>\n<code>{chunk}</code>",
                parse_mode="HTML",
            )
    else:
        text = (
            f"📋 <b>Все живые SOCKS5 ({len(proxies)} шт):</b>\n\n"
            f"<code>{full_text}</code>"
        )
        await callback.message.edit_text(
            text, reply_markup=back_menu, parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data == "stats")
async def cb_stats(callback: CallbackQuery) -> None:
    stats = await get_stats()
    text = (
        f"📊 <b>Статистика</b>\n\n"
        f"Всего прокси в базе: <b>{stats['total']}</b>\n"
        f"Из них живых: <b>{stats['alive']}</b>\n"
        f"Источников: <b>25</b>"
    )
    await callback.message.edit_text(text, reply_markup=back_menu, parse_mode="HTML")
    await callback.answer()
