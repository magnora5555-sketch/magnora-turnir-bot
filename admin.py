import re
from datetime import datetime
from pathlib import Path

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile

from config import ADMIN_ID
from data.database import (
    create_tournament,
    get_all_tournaments,
    set_current_tournament,
    get_current_tournament,
    set_tournament_stage,
    save_tournament_bracket,
    get_tournament_bracket,
    users,
    register_user,
    add_user_to_tournament,
    remove_user_from_tournament,
    generate_manual_user_id,
    delete_tournament,
    cleanup_user_if_unused,
)
from data.excel_store import (
    ensure_participants_file,
    get_participants_by_tournament,
    add_participant,
    export_tournament_participants,
    normalize_phone,
    delete_participants_by_tournament,
    delete_participant_by_tournament_and_user,
)
from keyboards.menu import admin_menu, tournament_size_menu, stage_size_menu, cancel_menu
from utils.bracket import validate_bracket_request, build_bracket, format_bracket_text
from utils.excel_bracket import create_bracket_excel

router = Router()


class CreateTournamentStates(StatesGroup):
    size = State()
    name = State()
    date = State()
    time = State()
    note = State()


class SelectTournamentStates(StatesGroup):
    tournament_id = State()


class StageStates(StatesGroup):
    stage_size = State()


class AddParticipantStates(StatesGroup):
    full_name = State()
    phone = State()
    username = State()
    telegram_id = State()


class RemoveParticipantStates(StatesGroup):
    telegram_id = State()


def is_admin(message: types.Message) -> bool:
    return message.from_user.id == ADMIN_ID


def normalize_text(text: str) -> str:
    text = (text or "").strip().lower()
    text = text.replace("’", "'").replace("‘", "'").replace("`", "'").replace("ʻ", "'")
    text = text.replace("❌", "").replace("📋", "").replace("📥", "").replace("➕", "")
    text = text.replace("🎯", "").replace("🧩", "").replace("🎲", "").replace("👁", "")
    text = text.replace("🏁", "").replace("ℹ️", "").replace("📂", "").replace("📌", "")
    text = " ".join(text.split())
    return text


def is_cancel_text(text: str) -> bool:
    return normalize_text(text) in ["bekor qilish", "bekor", "cancel"]


def parse_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%d.%m.%Y")
        return True
    except ValueError:
        return False


def parse_time(value: str) -> bool:
    return bool(re.fullmatch(r"([01]\d|2[0-3]):([0-5]\d)", value))


def is_valid_phone(phone: str) -> bool:
    digits = normalize_phone(phone).replace("+", "")
    return 9 <= len(digits) <= 15


@router.message(lambda message: message.from_user.id == ADMIN_ID)
async def admin_router(message: types.Message, state: FSMContext):
    text = normalize_text(message.text)
    current_state = await state.get_state()

    if is_cancel_text(message.text):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        return

    if current_state == CreateTournamentStates.size.state:
        if message.text not in ["32", "64", "128", "256"]:
            await message.answer("Faqat 32, 64, 128 yoki 256 tanlang.", reply_markup=tournament_size_menu())
            return
        await state.update_data(size=int(message.text))
        await state.set_state(CreateTournamentStates.name)
        await message.answer("Turnir nomini kiriting:", reply_markup=cancel_menu())
        return

    if current_state == CreateTournamentStates.name.state:
        name = " ".join((message.text or "").strip().split())
        if len(name) < 2:
            await message.answer("Turnir nomini to‘g‘ri kiriting.", reply_markup=cancel_menu())
            return
        await state.update_data(name=name)
        await state.set_state(CreateTournamentStates.date)
        await message.answer("Boshlanish sanasini kiriting:\nMasalan: 20.03.2026", reply_markup=cancel_menu())
        return

    if current_state == CreateTournamentStates.date.state:
        value = (message.text or "").strip()
        if not parse_date(value):
            await message.answer("Sana noto‘g‘ri. To‘g‘ri format: 20.03.2026", reply_markup=cancel_menu())
            return
        await state.update_data(date=value)
        await state.set_state(CreateTournamentStates.time)
        await message.answer("Boshlanish vaqtini kiriting:\nMasalan: 18:30", reply_markup=cancel_menu())
        return

    if current_state == CreateTournamentStates.time.state:
        value = (message.text or "").strip()
        if not parse_time(value):
            await message.answer("Vaqt noto‘g‘ri. To‘g‘ri format: 18:30", reply_markup=cancel_menu())
            return
        await state.update_data(time=value)
        await state.set_state(CreateTournamentStates.note)
        await message.answer("Eslatma yozing yoki yo‘q bo‘lsa - yuboring:", reply_markup=cancel_menu())
        return

    if current_state == CreateTournamentStates.note.state:
        data = await state.get_data()
        note = None if (message.text or "").strip() == "-" else (message.text or "").strip()
        tournament = create_tournament(
            name=data["name"],
            max_players=data["size"],
            date=data["date"],
            time=data["time"],
            note=note,
        )
        await state.clear()
        await message.answer(
            f"✅ Turnir yaratildi:\n\n"
            f"ID: {tournament['id']}\n"
            f"Nomi: {tournament['name']}\n"
            f"Sana: {tournament['date']}\n"
            f"Soat: {tournament['time']}\n"
            f"Eslatma: {tournament['note'] or 'yo‘q'}\n"
            f"Hajmi: {tournament['max_players']}",
            reply_markup=admin_menu()
        )
        return

    if current_state == SelectTournamentStates.tournament_id.state:
        if not (message.text or "").strip().isdigit():
            await message.answer("Turnir ID raqamini yuboring.", reply_markup=cancel_menu())
            return

        tournament_id = int(message.text.strip())
        selected = None
        for tournament in get_all_tournaments():
            if tournament["id"] == tournament_id:
                selected = tournament
                break

        if not selected:
            await message.answer("Bunday ID li turnir topilmadi.", reply_markup=cancel_menu())
            return

        set_current_tournament(tournament_id)
        ensure_participants_file()
        await state.clear()

        await message.answer(
            f"✅ Joriy turnir tanlandi:\n\n"
            f"ID: {selected['id']}\n"
            f"Nomi: {selected['name']}\n"
            f"Sana: {selected['date']}\n"
            f"Soat: {selected['time']}\n"
            f"Hajmi: {selected['max_players']}",
            reply_markup=admin_menu()
        )
        return

    if current_state == StageStates.stage_size.state:
        tournament = get_current_tournament()
        if not tournament:
            await state.clear()
            await message.answer("Avval joriy turnirni tanlang.", reply_markup=admin_menu())
            return

        if not (message.text or "").strip().isdigit():
            await message.answer("Setka formatini tugmadan tanlang.", reply_markup=stage_size_menu(tournament["max_players"]))
            return

        stage_size = int(message.text.strip())
        if not validate_bracket_request(tournament["max_players"], stage_size):
            await message.answer("Bu turnir hajmi uchun noto‘g‘ri setka formati tanlandi.", reply_markup=stage_size_menu(tournament["max_players"]))
            return

        set_tournament_stage(tournament["id"], stage_size)
        await state.clear()
        await message.answer(f"✅ Setka formati saqlandi: {stage_size}", reply_markup=admin_menu())
        return

    if current_state == AddParticipantStates.full_name.state:
        full_name = " ".join((message.text or "").strip().split())
        if len(full_name.split()) < 2:
            await message.answer("Ism familiya kiriting. Masalan: Akram Dusov", reply_markup=cancel_menu())
            return
        await state.update_data(full_name=full_name)
        await state.set_state(AddParticipantStates.phone)
        await message.answer("Telefon raqamini yuboring:", reply_markup=cancel_menu())
        return

    if current_state == AddParticipantStates.phone.state:
        phone = normalize_phone((message.text or "").strip())
        if not is_valid_phone(phone):
            await message.answer("Telefon noto‘g‘ri. Masalan: +998901234567", reply_markup=cancel_menu())
            return
        await state.update_data(phone=phone)
        await state.set_state(AddParticipantStates.username)
        await message.answer("Username yuboring yoki yo‘q bo‘lsa - yuboring:", reply_markup=cancel_menu())
        return

    if current_state == AddParticipantStates.username.state:
        username = "" if (message.text or "").strip() == "-" else (message.text or "").strip().lstrip("@")
        await state.update_data(username=username)
        await state.set_state(AddParticipantStates.telegram_id)
        await message.answer("Telegram ID yuboring yoki yo‘q bo‘lsa - yuboring:", reply_markup=cancel_menu())
        return

    if current_state == AddParticipantStates.telegram_id.state:
        tournament = get_current_tournament()
        if not tournament:
            await state.clear()
            await message.answer("Avval joriy turnirni tanlang.", reply_markup=admin_menu())
            return

        data = await state.get_data()
        raw = (message.text or "").strip()

        if raw == "-":
            telegram_id = generate_manual_user_id()
        elif raw.isdigit():
            telegram_id = int(raw)
        else:
            await message.answer("Telegram ID faqat raqam yoki - bo‘lishi kerak.", reply_markup=cancel_menu())
            return

        register_user(
            user_id=telegram_id,
            full_name=data["full_name"],
            username=data["username"],
            phone=data["phone"],
        )

        success_db, msg_db = add_user_to_tournament(tournament["id"], telegram_id)
        if not success_db:
            await state.clear()
            await message.answer(msg_db, reply_markup=admin_menu())
            return

        success_xlsx, msg_xlsx = add_participant(
            telegram_id=telegram_id,
            full_name=data["full_name"],
            phone=data["phone"],
            username=data["username"],
            tournament_id=tournament["id"],
            tournament_name=tournament["name"],
        )

        if not success_xlsx:
            remove_user_from_tournament(tournament["id"], telegram_id)
            cleanup_user_if_unused(telegram_id)
            await state.clear()
            await message.answer(msg_xlsx, reply_markup=admin_menu())
            return

        await state.clear()
        await message.answer("Ishtirokchi muvaffaqiyatli qo‘shildi ✅", reply_markup=admin_menu())
        return

    if current_state == RemoveParticipantStates.telegram_id.state:
        raw = (message.text or "").strip()
        if not raw.isdigit() and not (raw.startswith("-") and raw[1:].isdigit()):
            await message.answer("Telegram ID faqat raqam bo‘lishi kerak.", reply_markup=cancel_menu())
            return

        tournament = get_current_tournament()
        if not tournament:
            await state.clear()
            await message.answer("Avval joriy turnirni tanlang.", reply_markup=admin_menu())
            return

        telegram_id = int(raw)
        success, reply_text = remove_user_from_tournament(tournament["id"], telegram_id)

        if success:
            delete_participant_by_tournament_and_user(tournament["id"], telegram_id)
            cleanup_user_if_unused(telegram_id)

        await state.clear()
        await message.answer(reply_text, reply_markup=admin_menu())
        return

    if "turnir yaratish" in text:
        await state.clear()
        await state.set_state(CreateTournamentStates.size)
        await message.answer("Turnir hajmini tanlang:", reply_markup=tournament_size_menu())
        return

    if "turnirni tanlash" in text:
        tournaments = get_all_tournaments()
        if not tournaments:
            await message.answer("Tanlash uchun turnir yo‘q.", reply_markup=admin_menu())
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
        await state.set_state(SelectTournamentStates.tournament_id)
        await message.answer(text_out, reply_markup=cancel_menu())
        return

    if "joriy turnir" in text:
        tournament = get_current_tournament()
        if not tournament:
            await message.answer("Hozircha joriy turnir tanlanmagan.", reply_markup=admin_menu())
            return

        stage = tournament.get("selected_stage")
        stage_text = str(stage) if stage else "tanlanmagan"

        await message.answer(
            f"ℹ️ Joriy turnir:\n\n"
            f"ID: {tournament['id']}\n"
            f"Nomi: {tournament['name']}\n"
            f"Sana: {tournament['date']}\n"
            f"Soat: {tournament['time']}\n"
            f"Eslatma: {tournament['note'] or 'yo‘q'}\n"
            f"Hajmi: {tournament['max_players']}\n"
            f"Setka formati: {stage_text}\n"
            f"Ishtirokchilar: {len(tournament['players'])}/{tournament['max_players']}",
            reply_markup=admin_menu()
        )
        return

    if "ishtirokchilar ro'yxati" in text or "ishtirokchilar royxati" in text:
        tournament = get_current_tournament()
        if not tournament:
            await message.answer("Avval joriy turnirni tanlang.", reply_markup=admin_menu())
            return

        players = get_participants_by_tournament(tournament["id"])
        if not players:
            await message.answer("Hozircha ishtirokchilar yo‘q.", reply_markup=admin_menu())
            return

        text_out = f"📋 {tournament['name']} ishtirokchilari:\n\n"
        for i, player in enumerate(players, start=1):
            username = f"@{player['username']}" if player["username"] else "username yo‘q"
            telegram_id = player["telegram_id"] or "-"
            text_out += (
                f"{i}. {player['full_name']}\n"
                f"   📞 {player['phone']}\n"
                f"   👤 {username}\n"
                f"   🆔 {telegram_id}\n\n"
            )

        await message.answer(text_out, reply_markup=admin_menu())
        return

    if "ishtirokchilar excel" in text:
        tournament = get_current_tournament()
        if not tournament:
            await message.answer("Avval joriy turnirni tanlang.", reply_markup=admin_menu())
            return

        file_path = export_tournament_participants(tournament)
        if not Path(file_path).exists():
            await message.answer("Ishtirokchilar faylini yaratib bo‘lmadi.", reply_markup=admin_menu())
            return

        await message.answer_document(
            document=FSInputFile(file_path),
            caption=f"✅ Ishtirokchilar ro‘yxati: {tournament['name']}"
        )
        return

    if "ishtirokchi qo'shish" in text or "ishtirokchi qo‘shish" in text:
        tournament = get_current_tournament()
        if not tournament:
            await message.answer("Avval joriy turnirni tanlang.", reply_markup=admin_menu())
            return

        await state.clear()
        await state.set_state(AddParticipantStates.full_name)
        await message.answer("Ishtirokchi ism familiyasini yuboring:", reply_markup=cancel_menu())
        return

    if "ishtirokchini o'chirish" in text or "ishtirokchini o‘chirish" in text:
        tournament = get_current_tournament()
        if not tournament:
            await message.answer("Avval joriy turnirni tanlang.", reply_markup=admin_menu())
            return

        await state.clear()
        await state.set_state(RemoveParticipantStates.telegram_id)
        await message.answer("O‘chiriladigan ishtirokchi Telegram ID sini yuboring:", reply_markup=cancel_menu())
        return

    if "setka formatini tanlash" in text:
        tournament = get_current_tournament()
        if not tournament:
            await message.answer("Avval joriy turnirni tanlang.", reply_markup=admin_menu())
            return

        await state.clear()
        await state.set_state(StageStates.stage_size)
        await message.answer(
            f"{tournament['max_players']} talik turnir uchun setka formatini tanlang:",
            reply_markup=stage_size_menu(tournament["max_players"])
        )
        return

    if "jiribovka" in text:
        tournament = get_current_tournament()
        if not tournament:
            await message.answer("Avval joriy turnirni tanlang.", reply_markup=admin_menu())
            return

        stage_size = tournament.get("selected_stage")
        if not stage_size:
            await message.answer("Avval setka formatini tanlang.", reply_markup=admin_menu())
            return

        players = tournament["players"]
        if len(players) == 0:
            await message.answer("Setka yaratish uchun kamida 1 ta ishtirokchi kerak.", reply_markup=admin_menu())
            return

        if len(players) > stage_size:
            await message.answer(
                f"Ishtirokchilar soni ({len(players)}) tanlangan setkadan ({stage_size}) ko‘p.",
                reply_markup=admin_menu()
            )
            return

        bracket_pairs = build_bracket(players, stage_size)
        save_tournament_bracket(tournament["id"], bracket_pairs)
        await message.answer("✅ Jiribovka bajarildi va setka saqlandi.", reply_markup=admin_menu())
        return

    if "setka fayli" in text:
        tournament = get_current_tournament()
        if not tournament:
            await message.answer("Avval joriy turnirni tanlang.", reply_markup=admin_menu())
            return

        bracket_pairs = get_tournament_bracket(tournament["id"])
        if not bracket_pairs:
            await message.answer("Avval jiribovka qiling.", reply_markup=admin_menu())
            return

        participants = get_participants_by_tournament(tournament["id"])
        exported_path = create_bracket_excel(tournament, bracket_pairs, participants)

        if Path(exported_path).exists():
            await message.answer_document(
                document=FSInputFile(exported_path),
                caption=f"✅ Tayyor setka fayli: {tournament['name']}"
            )
        else:
            await message.answer("Setka faylini yaratib bo‘lmadi.", reply_markup=admin_menu())
        return

    if "turnirni tugatish" in text:
        tournament = get_current_tournament()
        if not tournament:
            await message.answer("Avval joriy turnirni tanlang.", reply_markup=admin_menu())
            return

        tournament_id = tournament["id"]
        player_ids = tournament["players"][:]

        delete_participants_by_tournament(tournament_id)
        delete_tournament(tournament_id)

        for user_id in player_ids:
            cleanup_user_if_unused(user_id)

        await state.clear()
        await message.answer(
            "🏁 Turnir butunlay o‘chirildi.\n"
            "Ishtirokchilar ham o‘chirildi.\n"
            "Foydalanuvchi ma’lumotlari ham tozalandi.\n"
            "Endi yangi turnir yaratishingiz mumkin.",
            reply_markup=admin_menu()
        )
        return

    await message.answer("Admin tugmalaridan foydalaning.", reply_markup=admin_menu())