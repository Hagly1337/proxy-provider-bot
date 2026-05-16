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
                text="📄 Скачать .txt",
                callback_data="download_txt",
            ),
            InlineKeyboardButton(
                text="🌍 По странам",
                callback_data="countries",
            ),
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

admin_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="▶️ Запустить проверку",
                callback_data="admin_start_job",
            )
        ],
        [
            InlineKeyboardButton(
                text="⏹ Остановить проверку",
                callback_data="admin_cancel_job",
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Обновить статус",
                callback_data="admin_panel",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад в меню",
                callback_data="back_menu",
            )
        ],
    ]
)
