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
