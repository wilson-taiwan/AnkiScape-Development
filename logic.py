from .constants import (
    ORE_DATA,
    EXP_TABLE,
    ACHIEVEMENTS,
    BASE_WOODCUTTING_PROBABILITY,
    BASE_MINING_PROBABILITY,
    LEVEL_BONUS_FACTOR,
)
from .ui import show_level_up_dialog, show_achievement_dialog

"""Anki-aware game logic orchestrators (no direct persistence here)."""

def get_exp_to_next_level(player_data, EXP_TABLE):
    current_level = player_data["mining_level"]
    if current_level >= 99:
        return 0
    return EXP_TABLE[current_level] - player_data["total_exp"]

from .logic_pure import calculate_new_level, calculate_probability_with_level

def level_up_check(skill, player_data):
    skill_map = {
        "Mining": ("mining_level", "mining_exp"),
        "Woodcutting": ("woodcutting_level", "woodcutting_exp"),
        "Smithing": ("smithing_level", "smithing_exp"),
        "Crafting": ("crafting_level", "crafting_exp"),
    }
    if skill in skill_map:
        level_key, exp_key = skill_map[skill]
        old_level = player_data[level_key]
        new_level = calculate_new_level(player_data[exp_key], old_level, EXP_TABLE)
        if new_level > old_level:
            for lvl in range(old_level + 1, new_level + 1):
                player_data[level_key] = lvl
                show_level_up_dialog(skill)

from .logic_pure import get_newly_completed_achievements

def check_achievements(player_data):
    newly_completed = get_newly_completed_achievements(player_data, ACHIEVEMENTS)
    for achievement in newly_completed:
        player_data["completed_achievements"].append(achievement)
        show_achievement_dialog(achievement, ACHIEVEMENTS[achievement])


def calculate_woodcutting_probability(player_level: int, tree_probability: float) -> float:
    return calculate_probability_with_level(
        player_level,
        BASE_WOODCUTTING_PROBABILITY,
        LEVEL_BONUS_FACTOR,
        tree_probability,
        cap=0.95,
    )


def calculate_mining_probability(player_level: int, ore_probability: float) -> float:
    return calculate_probability_with_level(
        player_level,
        BASE_MINING_PROBABILITY,
        LEVEL_BONUS_FACTOR,
        ore_probability,
        cap=0.95,
    )
