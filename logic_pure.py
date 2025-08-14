# logic_pure.py - Pure logic functions for AnkiScape (no Anki dependencies)

def get_exp_to_next_level(player_data, EXP_TABLE):
    current_level = player_data["mining_level"]
    if current_level >= 99:
        return 0
    return EXP_TABLE[current_level] - player_data["total_exp"]

def calculate_new_level(skill_exp, current_level, EXP_TABLE):
    """
    Calculate the new level for a skill given experience, current level, and EXP_TABLE.
    Returns the new level (int).
    """
    new_level = current_level
    while new_level < 99 and EXP_TABLE.get(new_level + 1) is not None and skill_exp >= EXP_TABLE[new_level + 1]:
        new_level += 1
    return new_level

def get_newly_completed_achievements(player_data, ACHIEVEMENTS):
    """
    Returns a list of achievement names that are newly completed (not yet in player_data["completed_achievements"])
    """
    completed = set(player_data.get("completed_achievements", []))
    newly_completed = []
    for name, data in ACHIEVEMENTS.items():
        if name not in completed and data["condition"](player_data):
            newly_completed.append(name)
    return newly_completed

def calculate_probability_with_level(player_level, base_probability, level_bonus_factor, source_probability, cap=0.95):
    """
    Compute success probability given a player's level and base probabilities.
    Probability = min(base_probability + player_level * level_bonus_factor, cap) * source_probability
    """
    level_bonus = player_level * level_bonus_factor
    return min(base_probability + level_bonus, cap) * source_probability

def pick_gem(gem_data, r):
    """
    Deterministically pick a gem given gem_data and a random draw r in [0, 1).
    gem_data: { name: { "probability": float }, ... }
    Returns the gem name, or None if r exceeds the total probability mass.
    """
    cumulative = 0.0
    for gem, data in gem_data.items():
        cumulative += data.get("probability", 0.0)
        if r < cumulative:
            return gem
    return None

def can_smelt_any_bar_pure(inventory, smithing_level, bar_data):
    """
    Return True if at least one bar can be smelted given the player's smithing_level and inventory.
    bar_data format: { bar_name: {"level": int, "ore_required": {ore: amount}} }
    """
    for _, data in bar_data.items():
        if smithing_level >= data.get("level", 0):
            if all(inventory.get(ore, 0) >= amount for ore, amount in data.get("ore_required", {}).items()):
                return True
    return False

def create_soft_clay_pure(inventory):
    """
    Deduct 1 "Clay" and add 1 "Soft clay" if possible.
    Returns (new_inventory, success: bool). Does not mutate input.
    """
    current_clay = inventory.get("Clay", 0)
    if current_clay > 0:
        new_inv = dict(inventory)
        new_inv["Clay"] = current_clay - 1
        new_inv["Soft clay"] = new_inv.get("Soft clay", 0) + 1
        return new_inv, True
    return inventory, False

def has_crafting_materials_pure(item, inventory, crafting_data):
    """
    Return True if inventory satisfies crafting requirements for the given item.
    """
    requirements = crafting_data[item].get("requirements", {})
    for material, amount in requirements.items():
        if inventory.get(material, 0) < amount:
            return False
    return True

def apply_crafting_pure(item, inventory, crafting_data):
    """
    If inventory meets requirements, deduct inputs and return (new_inventory, exp, success).
    Does not mutate input inventory.
    """
    if not has_crafting_materials_pure(item, inventory, crafting_data):
        return inventory, 0, False
    new_inv = dict(inventory)
    for material, amount in crafting_data[item].get("requirements", {}).items():
        new_inv[material] = new_inv.get(material, 0) - amount
    # Add the crafted item to inventory if it's a tangible product (exclude placeholders like "None")
    if item not in ("None",):
        new_inv[item] = new_inv.get(item, 0) + 1
    exp = crafting_data[item].get("exp", 0)
    return new_inv, exp, True

def apply_smelt_pure(bar_name, inventory, bar_data):
    """
    Attempt to smelt a specific bar. Returns (new_inventory, exp, success).
    Does not mutate input inventory. Only checks materials; level checks should be handled by caller.
    bar_data format: { bar_name: {"exp": float, "ore_required": {ore: amount}} }
    """
    spec = bar_data.get(bar_name)
    if not spec:
        return inventory, 0, False
    requirements = spec.get("ore_required", {})
    # Check materials
    if not all(inventory.get(ore, 0) >= amount for ore, amount in requirements.items()):
        return inventory, 0, False
    # Deduct and add bar
    new_inv = dict(inventory)
    for ore, amount in requirements.items():
        new_inv[ore] = new_inv.get(ore, 0) - amount
    new_inv[bar_name] = new_inv.get(bar_name, 0) + 1
    return new_inv, spec.get("exp", 0), True
