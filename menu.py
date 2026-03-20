from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def user_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📂 Ochiq turnirlar"), KeyboardButton(text="🎯 Turnirni tanlash")],
            [KeyboardButton(text="📌 Tanlangan turnirim"), KeyboardButton(text="📝 Turnirga yozilish")],
        ],
        resize_keyboard=True
    )


def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Turnir yaratish"), KeyboardButton(text="🎯 Turnirni tanlash")],
            [KeyboardButton(text="ℹ️ Joriy turnir"), KeyboardButton(text="📋 Ishtirokchilar ro‘yxati")],
            [KeyboardButton(text="📥 Ishtirokchilar Excel"), KeyboardButton(text="➕ Ishtirokchi qo‘shish")],
            [KeyboardButton(text="❌ Ishtirokchini o‘chirish"), KeyboardButton(text="🧩 Setka formatini tanlash")],
            [KeyboardButton(text="🎲 Jiribovka"), KeyboardButton(text="📥 Setka fayli")],
            [KeyboardButton(text="🏁 Turnirni tugatish")],
        ],
        resize_keyboard=True
    )


def tournament_size_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="32"), KeyboardButton(text="64")],
            [KeyboardButton(text="128"), KeyboardButton(text="256")],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def stage_size_menu(max_players: int):
    mapping = {
        32: [["8", "16"]],
        64: [["16", "32"]],
        128: [["32", "64"]],
        256: [["64", "128"]],
    }

    rows = mapping.get(max_players, [])
    keyboard = [[KeyboardButton(text=value) for value in row] for row in rows]
    keyboard.append([KeyboardButton(text="❌ Bekor qilish")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )


def cancel_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )