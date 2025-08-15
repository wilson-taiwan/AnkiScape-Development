import unittest
from deck_injection_pure import DeckBrowserContent, inject_into_deck_browser_content, ankiscape_button_html

class TestDeckInjectionPure(unittest.TestCase):
    def test_injects_into_links_when_present(self):
        c = DeckBrowserContent(links="<div>links</div>", stats="<div>stats</div>", tree="<div>tree</div>")
        out = inject_into_deck_browser_content(c)
        self.assertIn("ankiscape-btn", out.links or "")
        self.assertTrue(out.links.endswith(ankiscape_button_html()))

    def test_injects_into_tree_when_links_missing(self):
        c = DeckBrowserContent(links=None, stats=None, tree="<div>tree</div>")
        out = inject_into_deck_browser_content(c)
        self.assertIn("ankiscape-btn", out.tree or "")
        self.assertTrue(out.tree.endswith(ankiscape_button_html()))

    def test_idempotent_injection(self):
        c = DeckBrowserContent(links="<div>links</div>")
        out1 = inject_into_deck_browser_content(c)
        out2 = inject_into_deck_browser_content(out1)
        self.assertEqual(out1.links, out2.links)

if __name__ == "__main__":
    unittest.main()
