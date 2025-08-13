from aqt import mw
from .constants import ORE_DATA, EXP_TABLE, ACHIEVEMENTS
from .ui import show_level_up_dialog, show_achievement_dialog, update_menu_visibility

# Game logic functions

def save_player_data():
    mw.col.set_config("ankiscape_player_data", player_data)
    mw.col.set_config("ankiscape_current_skill", current_skill)

def load_player_data():
    global player_data, current_skill
    default_values = {
        "mining_level": 1,
        "woodcutting_level": 1,
        "smithing_level": 1,
        "crafting_level": 1,
        "mining_exp": 0,
        "woodcutting_exp": 0,
        "smithing_exp": 0,
        "crafting_exp": 0,
        "current_craft": "None",
        "current_ore": "Rune essence",
        "current_tree": "Tree",
        "current_bar": "Bronze bar",
        "inventory": {ore: 0 for ore in ORE_DATA},
        "progress_to_next": 0,
        "completed_achievements": [],
    }
    loaded_data = mw.col.get_config("ankiscape_player_data")
    if loaded_data:
        if "smithing_level" not in loaded_data:
            loaded_data["smithing_level"] = 1
            loaded_data["smithing_exp"] = 0
            loaded_data["current_bar"] = "Bronze bar"
        if "total_exp" in loaded_data:
            loaded_data["mining_exp"] = loaded_data.pop("total_exp")
            loaded_data["woodcutting_exp"] = 0
        for key, value in default_values.items():
            if key not in loaded_data:
                loaded_data[key] = value
        player_data = loaded_data
    else:
        player_data = default_values
    current_skill = mw.col.get_config("ankiscape_current_skill", default="None")
    update_menu_visibility()

def get_exp_to_next_level(player_data, EXP_TABLE):
    current_level = player_data["mining_level"]
    if current_level >= 99:
        return 0
    return EXP_TABLE[current_level] - player_data["total_exp"]

from .logic_pure import calculate_new_level

def level_up_check(skill):
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

def check_achievements():
    newly_completed = get_newly_completed_achievements(player_data, ACHIEVEMENTS)
    for achievement in newly_completed:
        player_data["completed_achievements"].append(achievement)
        show_achievement_dialog(achievement, ACHIEVEMENTS[achievement])
