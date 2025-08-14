# storage_pure.py - Pure helpers for migrating and defaulting player data (no Anki deps)
from typing import Dict, Any

CURRENT_CONFIG_VERSION = 2


def default_player_data(ORE_DATA: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "config_version": CURRENT_CONFIG_VERSION,
        "mining_level": 1,
        "woodcutting_level": 1,
        "smithing_level": 1,
        "crafting_level": 1,
        "mining_exp": 0,
        "woodcutting_exp": 0,
        "smithing_exp": 0,
        "crafting_exp": 0,
    "current_craft": "",
        "current_ore": "Rune essence",
        "current_tree": "Tree",
        "current_bar": "Bronze bar",
        "inventory": {ore: 0 for ore in ORE_DATA},
        "progress_to_next": 0,
        "completed_achievements": [],
    }


def migrate_loaded_data(loaded: Dict[str, Any], ORE_DATA: Dict[str, Any]) -> Dict[str, Any]:
    # Start from copy
    data = dict(loaded) if loaded else {}

    # Add config_version if missing
    if "config_version" not in data:
        data["config_version"] = 1

    # Migration: old schema used total_exp (treated as mining_exp), and no per-skill exp
    if "total_exp" in data and "mining_exp" not in data:
        data["mining_exp"] = data.pop("total_exp")
        data.setdefault("woodcutting_exp", 0)
        data.setdefault("smithing_exp", 0)
        data.setdefault("crafting_exp", 0)

    # Ensure smithing fields exist
    data.setdefault("smithing_level", 1)
    data.setdefault("smithing_exp", 0)
    data.setdefault("current_bar", "Bronze bar")

    # Ensure crafting fields exist
    data.setdefault("crafting_level", 1)
    data.setdefault("crafting_exp", 0)
    data.setdefault("current_craft", "")

    # Ensure ore/tree selection fields exist
    data.setdefault("current_ore", "Rune essence")
    data.setdefault("current_tree", "Tree")

    # Ensure inventory exists and at least has ore keys (preserve existing entries like logs/bars/gems)
    inv = data.get("inventory") or {}
    if not isinstance(inv, dict):
        inv = {}
    for ore in ORE_DATA:
        inv.setdefault(ore, 0)
    data["inventory"] = inv

    # Ensure achievements structure exists
    data.setdefault("completed_achievements", [])

    # Level defaults
    data.setdefault("mining_level", 1)
    data.setdefault("woodcutting_level", 1)

    # Progress key retained (not critical)
    data.setdefault("progress_to_next", 0)

    # Bump version to current
    data["config_version"] = CURRENT_CONFIG_VERSION
    return data
