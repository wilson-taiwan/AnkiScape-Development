import unittest
from deck_injection_pure import DeckBrowserContent, inject_into_deck_browser_content

class DummyContent:
    def __init__(self, stats=None, tree=None):
        self.stats = stats
        self.tree = tree

class TestDeckBrowserHookContract(unittest.TestCase):
    def test_pure_injection_contract(self):
        # Simulate Anki's content object with stats present
        content = DummyContent(stats="stats")
        dbc = DeckBrowserContent(stats=content.stats, tree=content.tree)
        out = inject_into_deck_browser_content(dbc)
        # Apply back to simulated content (mirrors __init__ logic)
        if out.stats != content.stats:
            content.stats = out.stats
        elif out.tree != content.tree:
            content.tree = out.tree
        # Button appears in stats
        self.assertIn("ankiscape-btn", content.stats)

if __name__ == "__main__":
    unittest.main()
