import unittest
from logic_pure import get_exp_to_next_level

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

if __name__ == "__main__":
    unittest.main()
