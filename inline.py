from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def tournaments_inline(tournaments):
    buttons = []
    for t in tournaments:
        text = f"{t['id']} | {t['name']} ({len(t['players'])}/{t['max_players']})"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"t_select:{t['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def stage_inline(max_players: int):
    mapping = {
        32: [8, 16],
        64: [16, 32],
        128: [32, 64],
        256: [64, 128],
    }
    rows = []
    for s in mapping.get(max_players, []):
        rows.append([InlineKeyboardButton(text=str(s), callback_data=f"stage:{s}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)