"""Pure helpers to prepare Deck Browser injection content and test idempotency.
These do not import Anki modules and can be unit-tested.
"""
from dataclasses import dataclass
from typing import Optional

BUTTON_HTML = (
    '<span id="ankiscape-btn-wrap" style="margin-left:8px">'
    '<a id="ankiscape-btn" href="#" style="padding:2px 6px; border-radius:6px; border:1px solid #ccc; text-decoration:none;" onclick="pycmd(\'ankiscape_open_menu\'); return false;">AnkiScape</a>'
    '</span>'
)

@dataclass
class DeckBrowserContent:
    # Likely present where Anki places the bottom action links (Get Shared, Create Deck, Import)
    links: Optional[str] = None
    # We avoid stats/tree to not overlap Heatmap or deck tree visually
    stats: Optional[str] = None
    tree: Optional[str] = None


def ankiscape_button_html() -> str:
    return BUTTON_HTML


def inject_into_deck_browser_content(content: DeckBrowserContent) -> DeckBrowserContent:
    """Append ankiscape button HTML to the bottom links area only (idempotent).
    We intentionally avoid stats/tree to prevent overlap with Heatmap or deck list.
    """
    if content.links is not None and "ankiscape-btn" not in content.links:
        content.links = (content.links or "") + BUTTON_HTML
        return content
    return content
