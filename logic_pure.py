# logic_pure.py - Pure logic functions for AnkiScape (no Anki dependencies)

def get_exp_to_next_level(player_data, EXP_TABLE):
    current_level = player_data["mining_level"]
    if current_level >= 99:
        return 0
    return EXP_TABLE[current_level] - player_data["total_exp"]
