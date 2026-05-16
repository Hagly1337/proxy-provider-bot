import asyncio
import logging
import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.config import ADMIN_ID
from bot.keyboards.inline import admin_menu, back_menu, main_menu
from db.database import get_stats, upsert_proxies
from services.proxy_validator import validate_proxies
from services.scheduler import (
    cancel_job,
    get_next_run,
    job_status,
    scrape_and_validate_job,
)

router = Router()
logger = logging.getLogger(__name__)

_IP_PORT_RE = re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{2,5})")


class AddProxyState(StatesGroup):
    waiting_for_proxies = State()


def _is_admin(user_id: int) -> bool:
    return ADMIN_ID != 0 and user_id == ADMIN_ID


PHASE_NAMES = {
    "idle": "✅ Ожидание",
    "scraping": "🔍 Сбор прокси",
    "validating": "🧪 Проверка",
    "cleanup": "🧹 Очистка мёртвых",
}


async def _build_admin_text() -> str:
    stats = await get_stats()
    phase_text = PHASE_NAMES.get(job_status.phase, job_status.phase)

    text = (
        "🛠 <b>Админ-панель</b>\n\n"
        f"📊 <b>БД:</b> {stats['total']} всего / {stats['alive']} живых\n"
        f"🔄 <b>Статус:</b> {phase_text}\n"
    )

    if job_status.is_running:
        if job_status.phase == "scraping":
            text += f"🔍 <b>Собрано:</b> {job_status.scraped} прокси\n"
        elif job_status.phase == "validating":
            text += (
                f"🧪 <b>Проверено:</b> {job_status.checked}/{job_status.total}\n"
                f"✅ <b>Живых найдено:</b> {job_status.alive_found}\n"
            )
        if job_status.cancel_requested:
            text += "⚠️ <b>Отмена запрошена…</b>\n"
    else:
        text += (
            f"📅 <b>Посл. запуск:</b> {job_status.last_run}\n"
            f"⏱ <b>Длительность:</b> {job_status.last_duration or '—'}\n"
            f"⏭ <b>След. запуск:</b> {get_next_run()}\n"
        )

    return text


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    text = await _build_admin_text()
    await message.answer(text, reply_markup=admin_menu, parse_mode="HTML")


@router.callback_query(F.data == "admin_panel")
async def cb_admin_panel(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    text = await _build_admin_text()
    await callback.message.edit_text(text, reply_markup=admin_menu, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_start_job")
async def cb_admin_start(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    if job_status.is_running:
        await callback.answer("⚠️ Проверка уже идёт!", show_alert=True)
        return
    asyncio.create_task(scrape_and_validate_job())
    await callback.answer("▶️ Проверка запущена!", show_alert=True)
    # Refresh panel after short delay
    await asyncio.sleep(1)
    text = await _build_admin_text()
    await callback.message.edit_text(text, reply_markup=admin_menu, parse_mode="HTML")


@router.callback_query(F.data == "admin_cancel_job")
async def cb_admin_cancel(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    if cancel_job():
        await callback.answer("⏹ Отмена запрошена…", show_alert=True)
    else:
        await callback.answer("ℹ️ Проверка не запущена.", show_alert=True)
    text = await _build_admin_text()
    await callback.message.edit_text(text, reply_markup=admin_menu, parse_mode="HTML")


@router.callback_query(F.data == "add_proxy")
async def cb_add_proxy(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddProxyState.waiting_for_proxies)
    await callback.message.edit_text(
        "➕ <b>Добавление прокси</b>\n\n"
        "Отправьте SOCKS5 прокси в формате <code>ip:port</code>\n"
        "Можно несколько — каждый с новой строки.\n\n"
        "Пример:\n"
        "<code>1.2.3.4:1080\n5.6.7.8:9050</code>",
        reply_markup=back_menu,
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AddProxyState.waiting_for_proxies)
async def handle_proxy_input(message: Message, state: FSMContext) -> None:
    text = message.text or ""
    matches = _IP_PORT_RE.findall(text)

    if not matches:
        await message.answer(
            "⚠️ Не найдено прокси в формате <code>ip:port</code>. Попробуйте ещё раз.",
            reply_markup=back_menu,
            parse_mode="HTML",
        )
        return

    proxies = [(ip, int(port)) for ip, port in matches if 1 <= int(port) <= 65535]

    await message.answer(
        f"⏳ Проверяю {len(proxies)} прокси… Это может занять до минуты.",
        parse_mode="HTML",
    )

    results = await validate_proxies(proxies)
    alive = [(ip_port, a) for ip_port, a in results if a]
    dead = [(ip_port, a) for ip_port, a in results if not a]

    if alive:
        alive_list = [p for p, _ in alive]
        await upsert_proxies(alive_list, source="user", is_alive=True)

    alive_text = "\n".join(f"✅ {ip}:{port}" for (ip, port), _ in alive) if alive else ""
    dead_text = "\n".join(f"❌ {ip}:{port}" for (ip, port), _ in dead) if dead else ""

    result_msg = f"📝 <b>Результат проверки:</b>\n\n"
    if alive_text:
        result_msg += f"<b>Рабочие ({len(alive)}):</b>\n{alive_text}\n\n"
    if dead_text:
        result_msg += f"<b>Нерабочие ({len(dead)}):</b>\n{dead_text}\n\n"
    if not alive:
        result_msg += "😔 Ни один прокси не прошёл проверку."

    await state.clear()
    await message.answer(result_msg, reply_markup=main_menu, parse_mode="HTML")
