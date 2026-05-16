import logging
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import back_menu, main_menu
from db.database import upsert_proxies
from services.proxy_validator import validate_proxies

router = Router()
logger = logging.getLogger(__name__)

_IP_PORT_RE = re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{2,5})")


class AddProxyState(StatesGroup):
    waiting_for_proxies = State()


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
