import io
import logging

from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.config import ADMIN_ID
from bot.keyboards.inline import back_menu, main_menu
from db.database import (
    get_alive_by_country,
    get_alive_proxies,
    get_all_alive_proxies,
    get_countries,
    get_stats,
)
from services.proxy_scraper import SOCKS5_SOURCES

router = Router()
logger = logging.getLogger(__name__)

_SRC_COUNT = len(SOCKS5_SOURCES)

WELCOME_TEXT = (
    "👋 <b>Proxy Provider Bot</b>\n\n"
    f"Бот автоматически собирает и проверяет бесплатные <b>SOCKS5</b> прокси "
    f"из {_SRC_COUNT} открытых источников.\n\n"
    "Выберите действие:"
)


def _get_menu(user_id: int) -> InlineKeyboardMarkup:
    buttons = list(main_menu.inline_keyboard)
    if ADMIN_ID != 0 and user_id == ADMIN_ID:
        buttons.append(
            [InlineKeyboardButton(text="🛠 Админ-панель", callback_data="admin_panel")]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=_get_menu(message.from_user.id), parse_mode="HTML")


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
    await message.answer(text, reply_markup=_get_menu(message.from_user.id), parse_mode="HTML")


@router.callback_query(F.data == "back_menu")
async def cb_back_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        WELCOME_TEXT, reply_markup=_get_menu(callback.from_user.id), parse_mode="HTML"
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
        f"Источников: <b>{_SRC_COUNT}</b>"
    )
    await callback.message.edit_text(text, reply_markup=back_menu, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "download_txt")
async def cb_download_txt(callback: CallbackQuery) -> None:
    proxies = await get_all_alive_proxies()
    if not proxies:
        await callback.message.edit_text(
            "😔 Пока нет проверенных прокси.",
            reply_markup=back_menu,
            parse_mode="HTML",
        )
        await callback.answer()
        return

    content = "\n".join(f"{ip}:{port}" for ip, port in proxies)
    file = BufferedInputFile(
        content.encode("utf-8"),
        filename=f"socks5_alive_{len(proxies)}.txt",
    )
    await callback.message.answer_document(
        file,
        caption=f"📄 <b>SOCKS5 прокси — {len(proxies)} шт</b>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "countries")
async def cb_countries(callback: CallbackQuery) -> None:
    countries = await get_countries()
    if not countries:
        await callback.message.edit_text(
            "🌍 Данные о странах пока не определены.\nПодождите завершения цикла проверки.",
            reply_markup=back_menu,
            parse_mode="HTML",
        )
        await callback.answer()
        return

    buttons = []
    for country_code, count in countries[:30]:
        buttons.append([
            InlineKeyboardButton(
                text=f"{country_code} — {count} шт",
                callback_data=f"country_{country_code}",
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_menu")
    ])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        "🌍 <b>Выберите страну:</b>",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("country_"))
async def cb_country_proxies(callback: CallbackQuery) -> None:
    country_code = callback.data.replace("country_", "")
    proxies = await get_alive_by_country(country_code)

    if not proxies:
        await callback.message.edit_text(
            f"😔 Нет живых прокси для <b>{country_code}</b>.",
            reply_markup=back_menu,
            parse_mode="HTML",
        )
        await callback.answer()
        return

    if len(proxies) > 50:
        content = "\n".join(f"{ip}:{port}" for ip, port in proxies)
        file = BufferedInputFile(
            content.encode("utf-8"),
            filename=f"socks5_{country_code}_{len(proxies)}.txt",
        )
        await callback.message.answer_document(
            file,
            caption=f"🌍 <b>{country_code}</b> — {len(proxies)} прокси",
            parse_mode="HTML",
        )
    else:
        lines = [f"<code>{ip}:{port}</code>" for ip, port in proxies]
        text = f"🌍 <b>{country_code} — {len(proxies)} шт:</b>\n\n" + "\n".join(lines)
        await callback.message.edit_text(text, reply_markup=back_menu, parse_mode="HTML")

    await callback.answer()
