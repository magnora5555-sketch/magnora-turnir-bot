users = {}
tournaments = []
current_tournament_id = None

# user_id -> tournament_id
user_selected_tournaments = {}


def create_tournament(name: str, max_players: int, date=None, time=None, note=None):
    tournament_id = len(tournaments) + 1
    tournament = {
        "id": tournament_id,
        "name": name,
        "max_players": max_players,
        "players": [],
        "selected_stage": None,
        "bracket_pairs": [],
        "date": date,
        "time": time,
        "note": note,
        "status": "active",
    }
    tournaments.append(tournament)
    return tournament


def get_all_tournaments():
    return tournaments


def get_tournament_by_id(tournament_id: int):
    for tournament in tournaments:
        if tournament["id"] == tournament_id:
            return tournament
    return None


def set_current_tournament(tournament_id: int):
    global current_tournament_id
    current_tournament_id = tournament_id


def clear_current_tournament():
    global current_tournament_id
    current_tournament_id = None


def get_current_tournament():
    if current_tournament_id is None:
        return None
    return get_tournament_by_id(current_tournament_id)


def set_user_selected_tournament(user_id: int, tournament_id: int):
    user_selected_tournaments[user_id] = tournament_id


def get_user_selected_tournament(user_id: int):
    tournament_id = user_selected_tournaments.get(user_id)
    if tournament_id is None:
        return None
    return get_tournament_by_id(tournament_id)


def clear_user_selected_tournament(user_id: int):
    if user_id in user_selected_tournaments:
        del user_selected_tournaments[user_id]


def register_user(user_id: int, full_name: str, username: str | None = None, phone: str | None = None):
    users[user_id] = {
        "full_name": full_name,
        "username": username or "",
        "phone": phone or "",
    }


def delete_user(user_id: int):
    if user_id in users:
        del users[user_id]
    if user_id in user_selected_tournaments:
        del user_selected_tournaments[user_id]


def is_user_registered(user_id: int):
    return user_id in users


def generate_manual_user_id():
    manual_ids = [uid for uid in users.keys() if isinstance(uid, int) and uid < 0]
    if not manual_ids:
        return -1
    return min(manual_ids) - 1


def add_user_to_tournament(tournament_id: int, user_id: int):
    tournament = get_tournament_by_id(tournament_id)
    if not tournament:
        return False, "Turnir topilmadi."

    if user_id in tournament["players"]:
        return False, "Bu ishtirokchi allaqachon turnirga qo‘shilgan."

    if len(tournament["players"]) >= tournament["max_players"]:
        return False, "Turnir to‘lgan."

    tournament["players"].append(user_id)
    return True, "Ishtirokchi turnirga muvaffaqiyatli qo‘shildi."


def add_user_to_current_tournament(user_id: int):
    tournament = get_current_tournament()
    if not tournament:
        return False, "Hozircha tanlangan turnir yo‘q."
    return add_user_to_tournament(tournament["id"], user_id)


def add_user_to_selected_tournament(user_id: int):
    tournament = get_user_selected_tournament(user_id)
    if not tournament:
        return False, "Avval turnirni tanlang."
    return add_user_to_tournament(tournament["id"], user_id)


def remove_user_from_tournament(tournament_id: int, user_id: int):
    tournament = get_tournament_by_id(tournament_id)
    if not tournament:
        return False, "Turnir topilmadi."

    if user_id not in tournament["players"]:
        return False, "Bu ishtirokchi turnirda yo‘q."

    tournament["players"].remove(user_id)
    return True, "Ishtirokchi turnirdan o‘chirildi."


def get_tournament_players(tournament_id: int):
    tournament = get_tournament_by_id(tournament_id)
    if not tournament:
        return []

    result = []
    for user_id in tournament["players"]:
        user_data = users.get(user_id, {})
        result.append({
            "user_id": user_id,
            "full_name": user_data.get("full_name", f"User {user_id}"),
            "username": user_data.get("username", ""),
            "phone": user_data.get("phone", ""),
        })
    return result


def set_tournament_stage(tournament_id: int, stage_size: int):
    tournament = get_tournament_by_id(tournament_id)
    if not tournament:
        return False

    tournament["selected_stage"] = stage_size
    return True


def save_tournament_bracket(tournament_id: int, bracket_pairs):
    tournament = get_tournament_by_id(tournament_id)
    if not tournament:
        return False

    tournament["bracket_pairs"] = bracket_pairs
    return True


def get_tournament_bracket(tournament_id: int):
    tournament = get_tournament_by_id(tournament_id)
    if not tournament:
        return []

    return tournament.get("bracket_pairs", [])


def is_user_in_any_tournament(user_id: int) -> bool:
    for tournament in tournaments:
        if user_id in tournament["players"]:
            return True
    return False


def cleanup_user_if_unused(user_id: int):
    if not is_user_in_any_tournament(user_id):
        delete_user(user_id)


def delete_tournament(tournament_id: int):
    global tournaments, current_tournament_id

    tournament = get_tournament_by_id(tournament_id)
    if not tournament:
        return False

    player_ids = tournament["players"][:]

    tournaments = [t for t in tournaments if t["id"] != tournament_id]

    if current_tournament_id == tournament_id:
        current_tournament_id = None

    to_delete = []
    for user_id, selected_id in user_selected_tournaments.items():
        if selected_id == tournament_id:
            to_delete.append(user_id)

    for user_id in to_delete:
        del user_selected_tournaments[user_id]

    for user_id in player_ids:
        cleanup_user_if_unused(user_id)

    return True