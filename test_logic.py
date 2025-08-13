import unittest
from logic_pure import (
    get_exp_to_next_level,
    calculate_new_level,
    get_newly_completed_achievements,
    calculate_probability_with_level,
    pick_gem,
)

class TestLogic(unittest.TestCase):
    def test_get_exp_to_next_level(self):
        player_data = {"mining_level": 10, "total_exp": 1000}
        EXP_TABLE = {10: 1500}
        result = get_exp_to_next_level(player_data, EXP_TABLE)
        self.assertEqual(result, 500)

    def test_max_level(self):
        player_data = {"mining_level": 99, "total_exp": 200000}
        EXP_TABLE = {99: 200000}
        result = get_exp_to_next_level(player_data, EXP_TABLE)
        self.assertEqual(result, 0)

    def test_get_newly_completed_achievements_basic(self):
        # Mock achievements and player data
        achievements = {
            "A": {"condition": lambda p: p["score"] >= 10},
            "B": {"condition": lambda p: p["score"] >= 20},
            "C": {"condition": lambda p: p["score"] >= 30},
        }
        player_data = {"score": 25, "completed_achievements": ["A"]}
        result = get_newly_completed_achievements(player_data, achievements)
        self.assertIn("B", result)
        self.assertNotIn("A", result)
        self.assertNotIn("C", result)

    def test_get_newly_completed_achievements_none(self):
        achievements = {
            "A": {"condition": lambda p: p["score"] >= 10},
            "B": {"condition": lambda p: p["score"] >= 20},
        }
        player_data = {"score": 5, "completed_achievements": []}
        result = get_newly_completed_achievements(player_data, achievements)
        self.assertEqual(result, [])

    def test_get_newly_completed_achievements_all(self):
        achievements = {
            "A": {"condition": lambda p: True},
            "B": {"condition": lambda p: True},
        }
        player_data = {"score": 100, "completed_achievements": []}
        result = get_newly_completed_achievements(player_data, achievements)
        self.assertCountEqual(result, ["A", "B"])

    def test_calculate_new_level_basic(self):
        EXP_TABLE = {1: 0, 2: 100, 3: 300, 4: 600, 5: 1000}
        self.assertEqual(calculate_new_level(50, 1, EXP_TABLE), 1)
        self.assertEqual(calculate_new_level(150, 1, EXP_TABLE), 2)
        self.assertEqual(calculate_new_level(350, 2, EXP_TABLE), 3)

    def test_calculate_new_level_multiple_level_up(self):
        EXP_TABLE = {1: 0, 2: 100, 3: 300, 4: 600, 5: 1000}
        self.assertEqual(calculate_new_level(1200, 1, EXP_TABLE), 5)

    def test_calculate_new_level_max_level(self):
        EXP_TABLE = {98: 10000, 99: 20000}
        self.assertEqual(calculate_new_level(25000, 98, EXP_TABLE), 99)
        self.assertEqual(calculate_new_level(25000, 99, EXP_TABLE), 99)

    def test_calculate_probability_with_level(self):
        # Low level, no cap hit
        prob = calculate_probability_with_level(
            player_level=0,
            base_probability=0.8,
            level_bonus_factor=0.02,
            source_probability=0.5,
            cap=0.95,
        )
        self.assertAlmostEqual(prob, 0.4)

        # Higher level, cap applies: (0.8 + 10*0.02)=1.0 -> capped to 0.95; 0.95*0.5=0.475
        prob = calculate_probability_with_level(
            player_level=10,
            base_probability=0.8,
            level_bonus_factor=0.02,
            source_probability=0.5,
            cap=0.95,
        )
        self.assertAlmostEqual(prob, 0.475)

    def test_pick_gem(self):
        gem_data = {
            "Sapphire": {"probability": 0.5},
            "Emerald": {"probability": 0.3},
            "Ruby": {"probability": 0.2},
        }
        self.assertEqual(pick_gem(gem_data, 0.2), "Sapphire")
        self.assertEqual(pick_gem(gem_data, 0.6), "Emerald")
        self.assertEqual(pick_gem(gem_data, 0.85), "Ruby")
        # When r exceeds total probability mass (1.0 exactly picks last), use 0.99 -> Ruby, 1.1 -> None
        self.assertEqual(pick_gem(gem_data, 0.99), "Ruby")
        partial = {
            "Sapphire": {"probability": 0.4},
            "Emerald": {"probability": 0.4},
        }
        self.assertIsNone(pick_gem(partial, 0.9))

if __name__ == "__main__":
    unittest.main()
