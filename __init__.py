# __init__.py

from .constants import *
from aqt import mw, gui_hooks
from aqt.utils import showInfo
from aqt.qt import *
from anki.hooks import addHook, wrap
from aqt.reviewer import Reviewer
import json
import random
import os
import datetime
import random
from .logic_pure import (
    calculate_probability_with_level,
    pick_gem,
    can_smelt_any_bar_pure,
    create_soft_clay_pure,
    has_crafting_materials_pure,
    can_craft_item_pure,
    apply_crafting_pure,
    apply_smelt_pure,
    apply_woodcutting_pure,
    apply_mining_pure,
    can_mine_ore_pure,
    can_cut_tree_pure,
)
from .logic import level_up_check, check_achievements
from .ui import (
    ExpPopup,
    show_error_message,
    show_tree_selection_dialog,
    show_ore_selection_dialog,
)
from . import ui

global card_turned, exp_awarded, answer_shown

answer_shown = False
card_turned = False
exp_awarded = False

current_skill = "None"

def show_review_popup():
    ui.show_review_popup()


# Classes moved to ui.py


# Helper functions
def save_player_data():
    mw.col.set_config("ankiscape_player_data", player_data)
    mw.col.set_config("ankiscape_current_skill", current_skill)

def load_player_data():
    global player_data, current_skill

    # Define default_values at the beginning of the function
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

        # Check if the loaded data is using the old format
        if "total_exp" in loaded_data:
            # Migrate the old format to the new format
            loaded_data["mining_exp"] = loaded_data.pop("total_exp")
            loaded_data["woodcutting_exp"] = 0

        # Ensure all new fields are present with default values
        for key, value in default_values.items():
            if key not in loaded_data:
                loaded_data[key] = value

        player_data = loaded_data
    else:
        # If no data is loaded, initialize with default values
        player_data = default_values

    current_skill = mw.col.get_config("ankiscape_current_skill", default="None")
    update_menu_visibility()

## Removed legacy get_exp_to_next_level stub; use logic_pure.get_exp_to_next_level in tests/pure logic.

# UI functions

def initialize_skill():
    global current_skill
    current_skill = mw.col.get_config("ankiscape_current_skill", default="None")
    update_menu_visibility()


def show_skill_selection():
    global current_skill
    selected = ui.show_skill_selection_dialog(current_skill, can_smelt_any_bar())
    if selected is None:
        return
    save_skill(selected, None)

def save_skill(skill, dialog):
    global current_skill
    if skill == "Smithing" and not can_smelt_any_bar():
        show_error_message("No Ores Available", "You don't have enough ores to smelt any bars. Mine some ores first!")
    else:
        current_skill = skill
        update_menu_visibility()
        if dialog:
            dialog.accept()

def update_menu_visibility():
    global current_skill
    ore_selection_action.setVisible(current_skill == "Mining")
    tree_selection_action.setVisible(current_skill == "Woodcutting")
    bar_selection_action.setVisible(current_skill == "Smithing")
    craft_selection_action.setVisible(current_skill == "Crafting")
    stats_action.setVisible(current_skill in ["Mining", "Woodcutting", "Smithing", "Crafting"])
    achievements_action.setVisible(current_skill in ["Mining", "Woodcutting", "Smithing", "Crafting"])

## show_achievement_dialog provided by ui.py

## show_level_up_dialog provided by ui.py

def show_craft_selection():
    selected = ui.show_craft_selection_dialog(
        current_craft=player_data.get("current_craft", "None"),
        crafting_level=player_data.get("crafting_level", 1),
        inventory=player_data.get("inventory", {}),
        CRAFTING_DATA=CRAFTING_DATA,
        CRAFTED_ITEM_IMAGES=CRAFTED_ITEM_IMAGES,
    )
    if selected:
        player_data["current_craft"] = selected
        save_player_data()

def has_crafting_materials(item):
    return has_crafting_materials_pure(item, player_data["inventory"], CRAFTING_DATA)

def on_crafting_answer():
    item = player_data["current_craft"]

    # Check level and material requirements first
    if not has_crafting_materials(item):
        show_error_message("Insufficient materials", f"You don't have enough materials to craft {item}.")
        return

    # Apply crafting via pure function (handles Soft clay and crafted items)
    new_inv, exp_gained, ok = apply_crafting_pure(item, player_data["inventory"], CRAFTING_DATA)
    if not ok:
        show_error_message("Insufficient materials", f"You don't have enough materials to craft {item}.")
        return

    # Update player data and UI
    player_data["inventory"] = new_inv
    player_data["crafting_exp"] += exp_gained
    level_up_check("Crafting", player_data)
    check_achievements(player_data)
    save_player_data()

    if hasattr(mw, 'exp_popup'):
        mw.exp_popup.show_exp(exp_gained)
    else:
        mw.exp_popup = ExpPopup(mw)
        mw.exp_popup.show_exp(exp_gained)

def show_bar_selection():
    selected = ui.show_bar_selection_dialog(
        current_bar=player_data.get("current_bar", "Bronze bar"),
        smithing_level=player_data.get("smithing_level", 1),
        BAR_DATA=BAR_DATA,
        BAR_IMAGES=BAR_IMAGES,
    )
    if selected:
        player_data["current_bar"] = selected
        save_player_data()


def show_tree_selection():
    selected = show_tree_selection_dialog(
        current_tree=player_data.get("current_tree", ""),
        woodcutting_level=player_data.get("woodcutting_level", 1),
        TREE_DATA=TREE_DATA,
        TREE_IMAGES=TREE_IMAGES,
    )
    if selected:
        player_data["current_tree"] = selected
        save_player_data()

def show_ore_selection():
    selected = show_ore_selection_dialog(
        current_ore=player_data.get("current_ore", "Rune essence"),
        mining_level=player_data.get("mining_level", 1),
        ORE_DATA=ORE_DATA,
        ORE_IMAGES=ORE_IMAGES,
    )
    if selected:
        player_data["current_ore"] = selected
        save_player_data()



# UI
def create_menu():
    global menu, ore_selection_action, tree_selection_action, bar_selection_action, craft_selection_action, stats_action, achievements_action
    menu = QMenu("AnkiScape", mw)
    mw.form.menubar.addMenu(menu)

    skill_selection_action = menu.addAction("Skill Selection")
    skill_selection_action.triggered.connect(show_skill_selection)

    # Add Ore Selection, Tree Selection, Stats, and Achievements (initially hidden)
    ore_selection_action = menu.addAction("Ore Selection")
    ore_selection_action.triggered.connect(show_ore_selection)
    ore_selection_action.setVisible(False)

    tree_selection_action = menu.addAction("Tree Selection")
    tree_selection_action.triggered.connect(show_tree_selection)
    tree_selection_action.setVisible(False)

    bar_selection_action = menu.addAction("Bar Selection")
    bar_selection_action.triggered.connect(show_bar_selection)
    bar_selection_action.setVisible(False)

    craft_selection_action = menu.addAction("Craft Selection")
    craft_selection_action.triggered.connect(show_craft_selection)
    craft_selection_action.setVisible(False)

    stats_action = menu.addAction("Stats")
    stats_action.triggered.connect(lambda: ui.show_stats(player_data, current_skill))
    stats_action.setVisible(False)

    achievements_action = menu.addAction("Achievements")
    achievements_action.triggered.connect(lambda: ui.show_achievements(player_data))
    achievements_action.setVisible(False)


# Main functionality

def on_smithing_answer():
    bar = player_data["current_bar"]
    bar_spec = BAR_DATA[bar]
    player_level = player_data["smithing_level"]

    if player_level < bar_spec["level"]:
        show_error_message("Insufficient level", f"You need level {bar_spec['level']} Smithing to smelt {bar}.")
        return

    # Use pure smelt application
    new_inv, exp_gained, ok = apply_smelt_pure(bar, player_data["inventory"], BAR_DATA)
    if not ok:
        # Find first missing ore to provide a helpful message
        for ore, amount in bar_spec["ore_required"].items():
            if player_data["inventory"].get(ore, 0) < amount:
                show_error_message("Insufficient ore", f"You need {amount} {ore} to smelt {bar}.")
                break
        return

    player_data["inventory"] = new_inv
    player_data["smithing_exp"] += exp_gained
    level_up_check("Smithing", player_data)
    check_achievements(player_data)
    save_player_data()

    if hasattr(mw, 'exp_popup'):
        mw.exp_popup.show_exp(exp_gained)
    else:
        mw.exp_popup = ExpPopup(mw)
        mw.exp_popup.show_exp(exp_gained)


def on_woodcutting_answer():
    tree = player_data["current_tree"]
    spec = TREE_DATA[tree]
    player_level = player_data["woodcutting_level"]

    woodcutting_probability = calculate_woodcutting_probability(player_level, spec["probability"])
    r_action = random.random()
    new_inv, exp_gained, ok = apply_woodcutting_pure(tree, player_data["inventory"], TREE_DATA, r_action, woodcutting_probability)
    if ok:
        if "logs_cut_today" not in player_data:
            player_data["logs_cut_today"] = 0
        player_data["logs_cut_today"] += 1
        player_data["inventory"] = new_inv
        player_data["woodcutting_exp"] += exp_gained
        level_up_check("Woodcutting", player_data)
        check_achievements(player_data)
        save_player_data()

        if hasattr(mw, 'exp_popup'):
            mw.exp_popup.show_exp(exp_gained)
        else:
            mw.exp_popup = ExpPopup(mw)
            mw.exp_popup.show_exp(exp_gained)


from .logic import calculate_woodcutting_probability, calculate_mining_probability


def on_good_answer():
    global current_skill, exp_awarded
    if exp_awarded:
        return
    if current_skill == "Mining":
        ore = player_data["current_ore"]
        ore_spec = ORE_DATA[ore]
        player_level = player_data["mining_level"]

        mining_probability = calculate_mining_probability(player_level, ore_spec["probability"])
        r_action = random.random()
        r_gem_chance = random.random()
        r_gem_pick = random.random()

        new_inv, exp_gained, ok, gem = apply_mining_pure(
            ore,
            player_data["inventory"],
            ORE_DATA,
            GEM_DATA,
            r_action,
            mining_probability,
            r_gem_chance,
            r_gem_pick,
            gem_drop_chance=1/256,
        )
        if ok:
            if "ores_mined_today" not in player_data:
                player_data["ores_mined_today"] = 0
            player_data["ores_mined_today"] += 1
            player_data["inventory"] = new_inv
            player_data["mining_exp"] += exp_gained
            level_up_check("Mining", player_data)
            check_achievements(player_data)
            save_player_data()

            if hasattr(mw, 'exp_popup'):
                mw.exp_popup.show_exp(exp_gained)
            else:
                mw.exp_popup = ExpPopup(mw)
                mw.exp_popup.show_exp(exp_gained)

    elif current_skill == "Woodcutting":
        on_woodcutting_answer()

    elif current_skill == "Smithing":
        on_smithing_answer()

    elif current_skill == "Crafting":
        on_crafting_answer()

    exp_awarded = True


## Removed roll_gem wrapper; mining uses apply_mining_pure directly.


def on_answer_card(self, ease, _old):
    global card_turned, exp_awarded, answer_shown
    if ease > 1 and current_skill in ["Mining", "Woodcutting",
                                      "Smithing", "Crafting"] and card_turned and not exp_awarded and answer_shown:
        on_good_answer()
        exp_awarded = True
    card_turned = False
    answer_shown = False  # Reset for the next card
    return _old(self, ease)


def on_card_did_show(card):
    global card_turned, exp_awarded, answer_shown
    card_turned = True
    exp_awarded = False
    answer_shown = False


def on_show_answer(reviewer):
    global answer_shown
    answer_shown = True


## show_error_message now provided by ui.show_error_message


def can_smelt_any_bar():
    return can_smelt_any_bar_pure(player_data["inventory"], player_data["smithing_level"], BAR_DATA)

def create_soft_clay():
    new_inv, ok = create_soft_clay_pure(player_data["inventory"]) 
    if ok:
        player_data["inventory"] = new_inv
    return ok

# Removed legacy safe_deduct_from_inventory; use utils.safe_deduct_from_inventory where needed.

# Initialization and hooks
def initialize_exp_popup():
    mw.exp_popup = ExpPopup(mw)


# Set up hooks
addHook("profileLoaded", load_player_data)
addHook("profileLoaded", initialize_exp_popup)
addHook("profileLoaded", initialize_skill)
addHook("profileLoaded", show_review_popup)

gui_hooks.reviewer_did_show_question.append(on_card_did_show)
gui_hooks.reviewer_did_show_answer.append(on_card_did_show)
gui_hooks.reviewer_did_show_answer.append(on_show_answer)

Reviewer._answerCard = wrap(Reviewer._answerCard, on_answer_card, "around")

# Initialize menu
create_menu()
