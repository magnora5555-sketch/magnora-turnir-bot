from aiogram import Router, types
from aiogram.filters import Command

from config import ADMIN_ID
from keyboards.menu import admin_menu, user_menu
from data.excel_store import ensure_participants_file

router = Router()


@router.message(Command("start"))
async def start_handler(message: types.Message):
    ensure_participants_file()

    if message.from_user.id == ADMIN_ID:
        await message.answer("Admin panelga xush kelibsiz.", reply_markup=admin_menu())
    else:
        await message.answer("Turnir botiga xush kelibsiz.", reply_markup=user_menu())