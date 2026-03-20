import random


def validate_bracket_request(max_players: int, stage_size: int) -> bool:
    valid_map = {
        32: [8, 16],
        64: [16, 32],
        128: [32, 64],
        256: [64, 128],
    }
    return stage_size in valid_map.get(max_players, [])


def build_bracket(players: list[int], stage_size: int):
    shuffled = players[:]
    random.shuffle(shuffled)

    while len(shuffled) < stage_size:
        shuffled.append(None)

    pairs = []
    for i in range(0, stage_size, 2):
        pairs.append((shuffled[i], shuffled[i + 1]))
    return pairs


def format_bracket_text(bracket_pairs, users: dict, title: str = "Setka"):
    lines = [f"🏆 {title}", ""]

    for idx, (p1, p2) in enumerate(bracket_pairs, start=1):
        name1 = "BYE" if p1 is None else users.get(p1, {}).get("full_name", f"ID {p1}")
        name2 = "BYE" if p2 is None else users.get(p2, {}).get("full_name", f"ID {p2}")
        lines.append(f"{idx}) {name1}  🆚  {name2}")

    return "\n".join(lines)