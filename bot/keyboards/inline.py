from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

main_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔐 Получить SOCKS5 (10 шт)",
                callback_data="get_socks5_10",
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Получить все живые",
                callback_data="get_socks5_all",
            )
        ],
        [
            InlineKeyboardButton(
                text="➕ Добавить прокси",
                callback_data="add_proxy",
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data="stats",
            )
        ],
    ]
)

back_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⬅️ Назад в меню",
                callback_data="back_menu",
            )
        ]
    ]
)
