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

def level_up_check(skill):
    if skill == "Mining":
        while player_data["mining_level"] < 99 and player_data["mining_exp"] >= EXP_TABLE[player_data["mining_level"]]:
            player_data["mining_level"] += 1
            show_level_up_dialog("Mining")
    elif skill == "Woodcutting":
        while player_data["woodcutting_level"] < 99 and player_data["woodcutting_exp"] >= EXP_TABLE[player_data["woodcutting_level"]]:
            player_data["woodcutting_level"] += 1
            show_level_up_dialog("Woodcutting")
    elif skill == "Smithing":
        while player_data["smithing_level"] < 99 and player_data["smithing_exp"] >= EXP_TABLE[player_data["smithing_level"]]:
            player_data["smithing_level"] += 1
            show_level_up_dialog("Smithing")
    elif skill == "Crafting":
        while player_data["crafting_level"] < 99 and player_data["crafting_exp"] >= EXP_TABLE[player_data["crafting_level"]]:
            player_data["crafting_level"] += 1
            show_level_up_dialog("Crafting")

def check_achievements():
    for achievement, data in ACHIEVEMENTS.items():
        if achievement not in player_data["completed_achievements"] and data["condition"](player_data):
            player_data["completed_achievements"].append(achievement)
            show_achievement_dialog(achievement, data)
