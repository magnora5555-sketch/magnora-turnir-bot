import re

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID
from data.database import (
    get_all_tournaments,
    get_current_tournament,
    get_tournament_by_id,
    get_user_selected_tournament,
    set_user_selected_tournament,
    register_user,
    add_user_to_selected_tournament,
    remove_user_from_tournament,
)
from data.excel_store import add_participant
from keyboards.menu import user_menu, cancel_menu

router = Router()


class UserRegistrationStates(StatesGroup):
    full_name = State()
    phone = State()


class UserSelectTournamentStates(StatesGroup):
    tournament_id = State()


def normalize_text(text: str) -> str:
    text = (text or "").strip().lower()
    text = text.replace("’", "'").replace("‘", "'").replace("`", "'").replace("ʻ", "'")
    text = text.replace("📝", "").replace("📂", "").replace("📌", "").replace("🎯", "")
    text = " ".join(text.split())
    return text


def is_cancel_text(text: str) -> bool:
    return normalize_text(text) in ["❌ bekor qilish", "bekor qilish", "bekor", "cancel"]


def normalize_phone_local(phone: str) -> str:
    phone = (phone or "").strip()
    phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    return phone


def is_valid_full_name(full_name: str) -> bool:
    full_name = " ".join((full_name or "").strip().split())
    parts = full_name.split(" ")
    if len(parts) < 2:
        return False
    return all(len(part) >= 2 for part in parts)


def is_valid_phone(phone: str) -> bool:
    phone = normalize_phone_local(phone)
    return bool(re.fullmatch(r"(\+998\d{9}|\d{9})", phone))


@router.message(lambda message: message.from_user.id != ADMIN_ID)
async def user_router(message, state: FSMContext):
    text = normalize_text(message.text)
    current_state = await state.get_state()
    user_id = message.from_user.id

    if is_cancel_text(message.text):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=user_menu())
        return

    if current_state == UserSelectTournamentStates.tournament_id.state:
        if not (message.text or "").strip().isdigit():
            await message.answer("Turnir ID raqamini yuboring.", reply_markup=cancel_menu())
            return

        tournament_id = int((message.text or "").strip())
        tournament = get_tournament_by_id(tournament_id)

        if not tournament:
            await message.answer("Bunday ID li turnir topilmadi.", reply_markup=cancel_menu())
            return

        set_user_selected_tournament(user_id, tournament_id)
        await state.clear()

        stage = tournament.get("selected_stage")
        stage_text = str(stage) if stage else "tanlanmagan"

        await message.answer(
            f"✅ Turnir tanlandi:\n\n"
            f"ID: {tournament['id']}\n"
            f"Nomi: {tournament['name']}\n"
            f"Sana: {tournament['date'] or '-'}\n"
            f"Soat: {tournament['time'] or '-'}\n"
            f"Hajmi: {tournament['max_players']}\n"
            f"Setka: {stage_text}\n"
            f"Band joy: {len(tournament['players'])}/{tournament['max_players']}",
            reply_markup=user_menu()
        )
        return

    if current_state == UserRegistrationStates.full_name.state:
        full_name = " ".join((message.text or "").strip().split())
        if not is_valid_full_name(full_name):
            await message.answer(
                "Ism familiya majburiy.\nKamida 2 ta so‘z kiriting.\nMasalan: Zohidjon Tursunov",
                reply_markup=cancel_menu()
            )
            return

        await state.update_data(full_name=full_name)
        await state.set_state(UserRegistrationStates.phone)
        await message.answer(
            "Telefon raqamingizni kiriting:\n"
            "Masalan: +998908315888\n"
            "yoki: 908315888",
            reply_markup=cancel_menu()
        )
        return

    if current_state == UserRegistrationStates.phone.state:
        phone = normalize_phone_local(message.text)

        if not is_valid_phone(phone):
            await message.answer(
                "Telefon raqam noto‘g‘ri.\n"
                "Faqat shu formatlar qabul qilinadi:\n"
                "+998908315888\n"
                "yoki\n"
                "908315888",
                reply_markup=cancel_menu()
            )
            return

        tournament = get_user_selected_tournament(user_id)
        if not tournament:
            await state.clear()
            await message.answer("Avval turnirni tanlang.", reply_markup=user_menu())
            return

        data = await state.get_data()
        full_name = data["full_name"]
        username = message.from_user.username or ""

        register_user(
            user_id=user_id,
            full_name=full_name,
            username=username,
            phone=phone,
        )

        success_db, msg_db = add_user_to_selected_tournament(user_id)
        if not success_db:
            await state.clear()
            await message.answer(msg_db, reply_markup=user_menu())
            return

        success_xlsx, msg_xlsx = add_participant(
            telegram_id=user_id,
            full_name=full_name,
            phone=phone,
            username=username,
            tournament_id=tournament["id"],
            tournament_name=tournament["name"],
        )

        if not success_xlsx:
            remove_user_from_tournament(tournament["id"], user_id)
            await state.clear()
            await message.answer(msg_xlsx, reply_markup=user_menu())
            return

        await state.clear()
        await message.answer(
            f"Siz '{tournament['name']}' turniriga muvaffaqiyatli ro‘yxatdan o‘tdingiz ✅",
            reply_markup=user_menu()
        )
        return

    if "ochiq turnirlar" in text:
        tournaments = get_all_tournaments()

        if not tournaments:
            await message.answer("Hozircha turnirlar yo‘q.", reply_markup=user_menu())
            return

        text_out = "📂 Ochiq turnirlar:\n\n"
        for tournament in tournaments:
            stage = tournament.get("selected_stage")
            stage_text = str(stage) if stage else "tanlanmagan"

            text_out += (
                f"ID: {tournament['id']}\n"
                f"Nomi: {tournament['name']}\n"
                f"Sana: {tournament['date'] or '-'}\n"
                f"Soat: {tournament['time'] or '-'}\n"
                f"Hajmi: {tournament['max_players']}\n"
                f"Setka: {stage_text}\n"
                f"Band joy: {len(tournament['players'])}/{tournament['max_players']}\n\n"
            )

        await message.answer(text_out, reply_markup=user_menu())
        return

    if "turnirni tanlash" in text:
        tournaments = get_all_tournaments()

        if not tournaments:
            await message.answer("Tanlash uchun turnir yo‘q.", reply_markup=user_menu())
            return

        text_out = "Tanlash uchun turnir ID sini yuboring:\n\n"
        for tournament in tournaments:
            text_out += (
                f"ID: {tournament['id']} | "
                f"{tournament['name']} | "
                f"{tournament['date']} {tournament['time']} | "
                f"{len(tournament['players'])}/{tournament['max_players']}\n"
            )

        await state.clear()
        await state.set_state(UserSelectTournamentStates.tournament_id)
        await message.answer(text_out, reply_markup=cancel_menu())
        return

    if "tanlangan turnirim" in text or "joriy turnir" in text:
        tournament = get_user_selected_tournament(user_id)

        if not tournament:
            await message.answer("Siz hali turnir tanlamagansiz.", reply_markup=user_menu())
            return

        stage = tournament.get("selected_stage")
        stage_text = str(stage) if stage else "tanlanmagan"

        text_out = (
            "📌 Tanlangan turniringiz:\n\n"
            f"ID: {tournament['id']}\n"
            f"Nomi: {tournament['name']}\n"
            f"Sana: {tournament['date'] or '-'}\n"
            f"Soat: {tournament['time'] or '-'}\n"
            f"Eslatma: {tournament['note'] or 'yo‘q'}\n"
            f"Hajmi: {tournament['max_players']}\n"
            f"Setka: {stage_text}\n"
            f"Ishtirokchilar: {len(tournament['players'])}/{tournament['max_players']}"
        )
        await message.answer(text_out, reply_markup=user_menu())
        return

    if "turnirga yozilish" in text:
        tournament = get_user_selected_tournament(user_id)

        if not tournament:
            await message.answer("Avval turnirni tanlang.", reply_markup=user_menu())
            return

        await state.clear()
        await state.set_state(UserRegistrationStates.full_name)
        await message.answer(
            "Ism familiyangizni kiriting.\nMasalan: Zohidjon Tursunov",
            reply_markup=cancel_menu()
        )
        return

    await message.answer("Tugmalardan foydalaning.", reply_markup=user_menu())