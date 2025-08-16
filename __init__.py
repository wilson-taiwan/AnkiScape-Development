# __init__.py

from .constants import (
    ORE_DATA,
    TREE_DATA,
    BAR_DATA,
    GEM_DATA,
    CRAFTING_DATA,
    ORE_IMAGES,
    TREE_IMAGES,
    BAR_IMAGES,
    GEM_IMAGES,
    CRAFTED_ITEM_IMAGES,
)
from aqt import mw, gui_hooks
from anki.hooks import addHook, wrap
from aqt.reviewer import Reviewer
import time
import random
import os
import datetime
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
from .logic import level_up_check, check_achievements, calculate_woodcutting_probability, calculate_mining_probability
from .ui import (
    ExpPopup,
    show_error_message,
    show_tree_selection_dialog,
    show_ore_selection_dialog,
    refresh_skill_availability,
    is_main_menu_open,
    focus_main_menu_if_open,
)
from . import ui
from .deck_injection_pure import DeckBrowserContent as _DBC, inject_into_deck_browser_content
from .storage import load_player_data as storage_load_player_data, save_player_data as storage_save_player_data

global card_turned, exp_awarded, answer_shown

answer_shown = False
card_turned = False
exp_awarded = False

current_skill = "None"

# --- Debug logging ---
DEBUG_LOG_FILE = os.path.join(os.path.dirname(__file__), "ankiscape_debug.log")

def debug_log(msg: str) -> None:
    try:
        with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().isoformat()} | {msg}\n")
    except Exception:
        pass

# Guard to avoid duplicate registrations
_ANKISCAPE_HOOKS_REGISTERED = False
_LAST_MENU_OPEN_TS = 0.0

def show_review_popup():
    ui.show_review_popup()


# Classes moved to ui.py


def save_player_data():
    storage_save_player_data(player_data, current_skill)


def load_player_data():
    global player_data, current_skill
    player_data, current_skill = storage_load_player_data()
    ui.update_menu_visibility(current_skill)

## Removed legacy get_exp_to_next_level stub; use logic_pure.get_exp_to_next_level in tests/pure logic.

# UI functions

def initialize_skill():
    global current_skill
    current_skill = mw.col.get_config("ankiscape_current_skill", default="None")
    ui.update_menu_visibility(current_skill)


# --- Small helpers to reduce duplication ---
def _show_exp(exp_gained) -> None:
    """Ensure the ExpPopup exists and display exp."""
    try:
        if not hasattr(mw, 'exp_popup'):
            mw.exp_popup = ExpPopup(mw)
        mw.exp_popup.show_exp(exp_gained)
    except Exception:
        pass


def _refresh_skill_availability() -> None:
    """Recompute and refresh Smithing/Crafting availability in the menu."""
    try:
        can_craft_any = any(
            can_craft_item_pure(
                player_data.get("crafting_level", 1),
                player_data.get("inventory", {}),
                item_name,
                CRAFTING_DATA,
            )
            for item_name in CRAFTING_DATA.keys()
        )
        refresh_skill_availability(can_smelt_any_bar(), can_craft_any)
    except Exception:
        pass


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
        ui.update_menu_visibility(current_skill)
        # Persist immediately so the selection survives window close
        try:
            mw.col.set_config("ankiscape_current_skill", current_skill)
        except Exception:
            pass
        if dialog:
            dialog.accept()

## menu visibility now handled by ui.update_menu_visibility

## show_achievement_dialog provided by ui.py

## show_level_up_dialog provided by ui.py

def show_craft_selection():
    selected = ui.show_craft_selection_dialog(
        current_craft=player_data.get("current_craft", ""),
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

    # Refresh availability for Crafting/Smithing in the open menu (enables, never auto-selects)
    try:
        can_craft_any = any(
            can_craft_item_pure(player_data.get("crafting_level", 1), player_data.get("inventory", {}), item_name, CRAFTING_DATA)
            for item_name in CRAFTING_DATA.keys()
        )
        refresh_skill_availability(can_smelt_any_bar(), can_craft_any)
    except Exception:
        pass

        _refresh_skill_availability()
        _show_exp(exp_gained)

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



def _on_main_menu():
    def _set_floating_enabled(val: bool):
        try:
            mw.col.set_config("ankiscape_floating_enabled", bool(val))
        except Exception:
            pass
        # Re-inject on current screens for immediate effect
        try:
            _inject_reviewer_floating_button()
        except Exception:
            pass
        try:
            _inject_overview_floating_button()
        except Exception:
            pass

    def _set_floating_position(pos: str):
        try:
            if pos not in ("left", "right"):
                pos = "right"
            mw.col.set_config("ankiscape_floating_position", pos)
        except Exception:
            pass
        try:
            _inject_reviewer_floating_button()
        except Exception:
            pass
        try:
            _inject_overview_floating_button()
        except Exception:
            pass

    ui.show_main_menu(
        player_data,
        current_skill,
        can_smelt_any_bar(),
        on_save_skill=lambda skill: save_skill(skill, None),
        on_set_ore=lambda ore: _set_value("current_ore", ore),
        on_set_tree=lambda tree: _set_value("current_tree", tree),
        on_set_bar=lambda bar: _set_value("current_bar", bar),
        on_set_craft=lambda item: _set_value("current_craft", item),
        on_set_floating_enabled=_set_floating_enabled,
        on_set_floating_position=_set_floating_position,
    )


def _set_value(key: str, value):
    player_data[key] = value
    save_player_data()


def initialize_menu():
    ui.create_menu(on_main_menu=_on_main_menu)
    # Refresh Deck Browser so injected content becomes visible after login
    try:
        debug_log("initialize_menu: forcing deck browser refresh")
        _force_deck_browser_refresh()
    except Exception:
        debug_log("initialize_menu: deck browser refresh failed")
        pass


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

    # Refresh availability for Crafting/Smithing in the open menu after smelting
    try:
        can_craft_any = any(
            can_craft_item_pure(player_data.get("crafting_level", 1), player_data.get("inventory", {}), item_name, CRAFTING_DATA)
            for item_name in CRAFTING_DATA.keys()
        )
        refresh_skill_availability(can_smelt_any_bar(), can_craft_any)
    except Exception:
        pass

        _refresh_skill_availability()
        _show_exp(exp_gained)
from .logic import calculate_woodcutting_probability, calculate_mining_probability


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

    _show_exp(exp_gained)


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

            # If the main menu is open, auto-enable Smithing/Crafting when they become possible.
            _refresh_skill_availability()
            _show_exp(exp_gained)

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
addHook("profileLoaded", initialize_menu)
addHook("profileLoaded", lambda: _register_deck_browser_button())

gui_hooks.reviewer_did_show_question.append(on_card_did_show)
gui_hooks.reviewer_did_show_answer.append(on_card_did_show)
gui_hooks.reviewer_did_show_answer.append(on_show_answer)

# Flexible wrappers to handle version differences in hook signatures
def _on_rev_show_question(*_args, **_kwargs):
    _inject_reviewer_floating_button()

def _on_rev_show_answer(*_args, **_kwargs):
    _inject_reviewer_floating_button()

gui_hooks.reviewer_did_show_question.append(_on_rev_show_question)
gui_hooks.reviewer_did_show_answer.append(_on_rev_show_answer)

Reviewer._answerCard = wrap(Reviewer._answerCard, on_answer_card, "around")

# Menu is created on profile load via initialize_menu

# --- Deck Browser bottom button integration ---

def _inject_reviewer_floating_button(_=None):
    """Ensure a floating AnkiScape pill is present in the Reviewer webview."""
    try:
        # Respect settings
        enabled = True
        pos = "right"
        try:
            enabled = bool(mw.col.get_config("ankiscape_floating_enabled", True))
            pos = mw.col.get_config("ankiscape_floating_position", "right")
            if pos not in ("left", "right"):
                pos = "right"
        except Exception:
            pass
        if not enabled:
            js_remove = r"""
            (function(){ var el = document.getElementById('ankiscape-float'); if (el && el.parentElement){ el.parentElement.removeChild(el);} })();
            """
            mw.reviewer.web.eval(js_remove)
            debug_log("inject_reviewer_floating_button: disabled; removed")
            return
        js = r"""
        (function(){
            try{
                var wrap = document.getElementById('ankiscape-float');
                if (!wrap) {
                    wrap = document.createElement('div');
                    wrap.id = 'ankiscape-float';
                    wrap.style.position = 'fixed';
                    // position set below
                    wrap.style.bottom = '16px';
                    wrap.style.zIndex = '9999';
                    document.body.appendChild(wrap);
                }
                // Reset position and apply current side
                wrap.style.left = '';
                wrap.style.right = '';
                if ('__POS__' === 'left') { wrap.style.left = '16px'; } else { wrap.style.right = '16px'; }

                var btn = document.getElementById('ankiscape-btn');
                if (!btn) {
                    btn = document.createElement('a');
                    btn.id = 'ankiscape-btn';
                }
                // Normalize styles/content (icon-only)
                btn.href = '#';
                btn.style.padding = '10px';
                btn.style.border = 'none';
                btn.style.borderRadius = '20px';
                btn.style.background = 'transparent';
                btn.style.boxShadow = 'none';
                btn.style.textDecoration = 'none';
                btn.style.outline = 'none';
                btn.style.webkitTapHighlightColor = 'transparent';
                btn.title = 'AnkiScape';
                var img = btn.querySelector('img');
                if (!img) { btn.textContent = ''; img = document.createElement('img'); btn.appendChild(img); }
                img.alt = 'AnkiScape';
                img.style.width = '24px';
                img.style.height = '24px';
                img.style.display = 'block';
                img.style.filter = 'drop-shadow(0 1px 1px rgba(0,0,0,0.25))';
                img.src = '__ICON_DATA_URI__';
                // Bind click handler only once to avoid duplicate pycmd messages
                if (!btn.dataset.ankiscapeBound) {
                    btn.addEventListener('click', function(ev){
                        ev.preventDefault();
                        try { pycmd('ankiscape_open_menu'); } catch(e){}
                        return false;
                    });
                    btn.dataset.ankiscapeBound = '1';
                }
                // Ensure it sits in our wrap
                if (btn.parentElement !== wrap) { wrap.appendChild(btn); }
                try { pycmd('ankiscape_log:review_floating_inserted'); } catch(e){}
            } catch(e) { try { pycmd('ankiscape_log:review_js_error'); } catch(_){} }
        })();
        """
        # Embed icon data URI for the floating pill
        try:
            from .deck_injection_pure import _get_icon_data_uri
            icon_uri = _get_icon_data_uri() or ''
        except Exception:
            icon_uri = ''
        js = js.replace("__POS__", pos).replace("__ICON_DATA_URI__", icon_uri)
        debug_log("inject_reviewer_floating_button: eval")
        mw.reviewer.web.eval(js)
    except Exception:
        debug_log("inject_reviewer_floating_button: failed")

def _inject_overview_floating_button(overview=None, content=None):  # matches deck_browser_will_render-like signature
    """Ensure a floating pill exists on the Overview (pre-review) screen."""
    try:
        web = None
        try:
            web = overview.web
        except Exception:
            # fallback: try mw.overview.web on some versions
            web = getattr(getattr(mw, 'overview', None), 'web', None)
        if not web:
            debug_log("inject_overview_floating_button: no web")
            return
        # Respect settings
        enabled = True
        pos = "right"
        try:
            enabled = bool(mw.col.get_config("ankiscape_floating_enabled", True))
            pos = mw.col.get_config("ankiscape_floating_position", "right")
            if pos not in ("left", "right"):
                pos = "right"
        except Exception:
            pass
        if not enabled:
            js_remove = r"""
            (function(){ var el = document.getElementById('ankiscape-float'); if (el && el.parentElement){ el.parentElement.removeChild(el);} })();
            """
            web.eval(js_remove)
            debug_log("inject_overview_floating_button: disabled; removed")
            return
        js = r"""
        (function(){
            try{
                var wrap = document.getElementById('ankiscape-float');
                if (!wrap) {
                    wrap = document.createElement('div');
                    wrap.id = 'ankiscape-float';
                    wrap.style.position = 'fixed';
                    // position set below
                    wrap.style.bottom = '16px';
                    wrap.style.zIndex = '9999';
                    document.body.appendChild(wrap);
                }
                // Reset position and apply current side
                wrap.style.left = '';
                wrap.style.right = '';
                if ('__POS__' === 'left') { wrap.style.left = '16px'; } else { wrap.style.right = '16px'; }

                var btn = document.getElementById('ankiscape-btn');
                if (!btn) { btn = document.createElement('a'); btn.id = 'ankiscape-btn'; }
                // Normalize to icon-only style
                btn.href = '#';
                btn.style.padding = '10px';
                btn.style.border = 'none';
                btn.style.borderRadius = '20px';
                btn.style.background = 'transparent';
                btn.style.boxShadow = 'none';
                btn.style.textDecoration = 'none';
                btn.style.outline = 'none';
                btn.style.webkitTapHighlightColor = 'transparent';
                btn.title = 'AnkiScape';
                var img = btn.querySelector('img');
                if (!img) { btn.textContent=''; img = document.createElement('img'); btn.appendChild(img); }
                img.alt = 'AnkiScape';
                img.style.width = '24px';
                img.style.height = '24px';
                img.style.display = 'block';
                img.style.filter = 'drop-shadow(0 1px 1px rgba(0,0,0,0.25))';
                img.src = '__ICON_DATA_URI__';
                // Bind click handler only once to avoid duplicate pycmd messages
                if (!btn.dataset.ankiscapeBound) {
                    btn.addEventListener('click', function(ev){
                        ev.preventDefault();
                        try { pycmd('ankiscape_open_menu'); } catch(e){}
                        return false;
                    });
                    btn.dataset.ankiscapeBound = '1';
                }
                if (btn.parentElement !== wrap) { wrap.appendChild(btn); }
                try { pycmd('ankiscape_log:overview_floating_inserted'); } catch(e){}
            } catch(e) { try { pycmd('ankiscape_log:overview_js_error'); } catch(_){} }
        })();
        """
        try:
            from .deck_injection_pure import _get_icon_data_uri
            icon_uri = _get_icon_data_uri() or ''
        except Exception:
            icon_uri = ''
        js = js.replace("__POS__", pos).replace("__ICON_DATA_URI__", icon_uri)
        debug_log("inject_overview_floating_button: eval")
        web.eval(js)
    except Exception:
        debug_log("inject_overview_floating_button: failed")


def _register_deck_browser_button():
    """Inject an 'AnkiScape' button near the bottom links and wire it to open the menu."""
    try:
        from aqt import gui_hooks as _hooks  # type: ignore
    except Exception:
        return
    global _ANKISCAPE_HOOKS_REGISTERED
    if _ANKISCAPE_HOOKS_REGISTERED:
        debug_log("_register_deck_browser_button: hooks already registered; skipping")
        return
    try:
        debug_log("_register_deck_browser_button: registering hooks; available: " + ", ".join([n for n in dir(_hooks) if not n.startswith("__")][:40]))
    except Exception:
        debug_log("_register_deck_browser_button: registering hooks (could not list attrs)")

    def _add_button(deck_browser, content):  # type: ignore[no-redef]
        debug_log("_add_button: called")
        # Use pure injection logic for determinism and testability
        try:
            # Diagnostics: log which fields exist and sample lengths
            try:
                has_links = hasattr(content, "links") and isinstance(getattr(content, "links"), str)
                has_stats = hasattr(content, "stats") and isinstance(getattr(content, "stats"), str)
                has_tree = hasattr(content, "tree") and isinstance(getattr(content, "tree"), str)
                debug_log(f"_add_button: fields links={has_links} stats={has_stats} tree={has_tree}")
            except Exception:
                debug_log("_add_button: field introspection failed")
            db_content = _DBC(
                links=getattr(content, "links", None),
                stats=getattr(content, "stats", None),
                tree=getattr(content, "tree", None),
            )
            before_links, before_stats, before_tree = db_content.links, db_content.stats, db_content.tree
            db_content = inject_into_deck_browser_content(db_content)
            if db_content.links != before_links:
                if hasattr(content, "links"):
                    content.links = db_content.links
                else:
                    # Links not exposed; do nothing here to avoid overlapping Heatmap
                    debug_log("_add_button: links attr missing; skipping to avoid overlap")
                debug_log("_add_button: injected into links")
            elif db_content.stats != before_stats or db_content.tree != before_tree:
                # We no longer inject into stats/tree by design
                debug_log("_add_button: no injection (stats/tree avoided)")
            else:
                debug_log("_add_button: already present; no injection")
        except Exception as e:
            debug_log(f"_add_button: error {e}")

    def _on_js_message(handled, message, context):  # type: ignore[no-redef]
        debug_log(f"_on_js_message: {message}")
        if isinstance(message, str) and message.startswith("ankiscape_log:"):
            debug_log(f"js: {message[len('ankiscape_log:'):]}")
            return handled
        if message == "ankiscape_open_menu":
            # If already open, just focus it; otherwise open (with debounce)
            try:
                if focus_main_menu_if_open():
                    return (True, None)
            except Exception:
                pass
            try:
                global _LAST_MENU_OPEN_TS
                now = time.monotonic()
                # Ignore rapid duplicate requests (e.g., multiple JS listeners)
                if now - _LAST_MENU_OPEN_TS < 0.5:
                    return (True, None)
                _LAST_MENU_OPEN_TS = now
            except Exception:
                pass
            _on_main_menu()
            return (True, None)
        return handled

    def _did_render(deck_browser):  # type: ignore[no-redef]
        try:
            # Read config to decide whether to allow floating fallback and which side
            enable_floating = True
            float_pos = 'right'
            try:
                enable_floating = bool(mw.col.get_config('ankiscape_floating_enabled', True))
                p = mw.col.get_config('ankiscape_floating_position', 'right')
                float_pos = p if p in ('left','right') else 'right'
            except Exception:
                pass
            # Resolve icon data URI
            try:
                from .deck_injection_pure import _get_icon_data_uri
                _icon_uri = _get_icon_data_uri() or ''
            except Exception:
                _icon_uri = ''
            js = r"""
            (function(){
                try {
                    // Don't early-return; we might need to reposition the wrap based on settings
                    function makeBtn(){
                        var a = document.createElement('a');
                        a.id = 'ankiscape-btn';
                        a.href = '#';
                        a.style.marginLeft = '8px';
                        a.style.padding = '6px';
                        a.style.border = 'none';
                        a.style.borderRadius = '8px';
                        a.style.textDecoration = 'none';
                        a.style.background = 'transparent';
                        a.title = 'AnkiScape';
                        var img = document.createElement('img');
                        img.alt = 'AnkiScape';
                        img.style.width = '24px';
                        img.style.height = '24px';
                        img.style.display = 'block';
                        img.style.filter = 'drop-shadow(0 1px 1px rgba(0,0,0,0.25))';
                        img.src = '__ICON_DATA_URI__';
                        a.appendChild(img);
                        if (!a.dataset.ankiscapeBound) {
                            a.addEventListener('click', function(ev){
                                ev.preventDefault();
                                try { pycmd('ankiscape_open_menu'); } catch(e){}
                                return false;
                            });
                            a.dataset.ankiscapeBound = '1';
                        }
                        return a;
                    }

                    // 1) Try bottom actions row: insert after last known action
                    var elems = Array.from(document.querySelectorAll('a,button'));
                    var actions = elems.filter(function(e){
                        var t = (e.textContent || '').trim();
                        return /(Get Shared|Create Deck|Import)/i.test(t);
                    });
                    if (actions.length) {
                        var last = actions[actions.length - 1];
                        var btn = document.getElementById('ankiscape-btn') || makeBtn();
                        // If existing button lacks an img, replace its contents
                        if (!btn.querySelector('img')) {
                            btn.textContent = '';
                            var img1 = document.createElement('img');
                            img1.alt = 'AnkiScape'; img1.style.width='24px'; img1.style.height='24px'; img1.style.display='block'; img1.style.filter='drop-shadow(0 1px 1px rgba(0,0,0,0.25))';
                            img1.src='__ICON_DATA_URI__'; btn.appendChild(img1);
                        }
                        if (last.parentElement) {
                            if (last.nextSibling) {
                                last.parentElement.insertBefore(btn, last.nextSibling);
                            } else {
                                last.parentElement.appendChild(btn);
                            }
                            try { pycmd('ankiscape_log:after_last_action(' + actions.length + ')'); } catch(e){}
                            return;
                        }
                    }

                    // 2) Try top nav: find Decks/Add/Browse/Stats/Sync anchors and append next to Sync
                    var topAnchors = elems.filter(function(e){
                        var t = (e.textContent || '').trim();
                        return /(Decks|Add|Browse|Stats|Sync)/i.test(t);
                    });
                    if (topAnchors.length) {
                        // Find the rightmost among these
                        var rightmost = topAnchors[topAnchors.length - 1];
                        var btn2 = document.getElementById('ankiscape-btn') || makeBtn();
                        if (!btn2.querySelector('img')) {
                            btn2.textContent = '';
                            var img2 = document.createElement('img');
                            img2.alt='AnkiScape'; img2.style.width='24px'; img2.style.height='24px'; img2.style.display='block'; img2.style.filter='drop-shadow(0 1px 1px rgba(0,0,0,0.25))';
                            img2.src='__ICON_DATA_URI__'; btn2.appendChild(img2);
                        }
                        if (rightmost.parentElement) {
                            if (rightmost.nextSibling) {
                                rightmost.parentElement.insertBefore(btn2, rightmost.nextSibling);
                            } else {
                                rightmost.parentElement.appendChild(btn2);
                            }
                            try { pycmd('ankiscape_log:inserted_topnav(' + topAnchors.length + ')'); } catch(e){}
                            return;
                        }
                    }

                    // 3) Fallback: try known footer selectors
                    var footer = document.querySelector('.links') || document.querySelector('#links') || null;
                    if (footer) {
                        var btn3 = document.getElementById('ankiscape-btn') || makeBtn();
                        if (!btn3.querySelector('img')) {
                            btn3.textContent = '';
                            var img3 = document.createElement('img');
                            img3.alt='AnkiScape'; img3.style.width='24px'; img3.style.height='24px'; img3.style.display='block'; img3.style.filter='drop-shadow(0 1px 1px rgba(0,0,0,0.25))';
                            img3.src='__ICON_DATA_URI__'; btn3.appendChild(img3);
                        }
                        footer.appendChild(btn3);
                        try { pycmd('ankiscape_log:inserted_selector'); } catch(e){}
                        return;
                    }

                    // 4) Last resort: floating edge-aligned pill
                    if (__ENABLE_FLOATING__) {
                        var wrap = document.getElementById('ankiscape-float');
                        if (!wrap) {
                            wrap = document.createElement('div');
                            wrap.id = 'ankiscape-float';
                            wrap.style.position = 'fixed';
                            // position set below
                            wrap.style.bottom = '16px';
                            wrap.style.zIndex = '9999';
                            document.body.appendChild(wrap);
                        }
                        // Reset position and set based on config
                        wrap.style.left = '';
                        wrap.style.right = '';
                        if ('__POS__' === 'left') { wrap.style.left = '16px'; } else { wrap.style.right = '16px'; }
                        var btn = document.getElementById('ankiscape-btn');
                        if (!btn) { btn = makeBtn(); }
                        if (!btn.querySelector('img')) {
                            btn.textContent = '';
                            var img4 = document.createElement('img');
                            img4.alt='AnkiScape'; img4.style.width='24px'; img4.style.height='24px'; img4.style.display='block'; img4.style.filter='drop-shadow(0 1px 1px rgba(0,0,0,0.25))';
                            img4.src='__ICON_DATA_URI__'; btn.appendChild(img4);
                        }
                        if (btn.parentElement !== wrap) { wrap.appendChild(btn); } else if (!document.getElementById('ankiscape-btn')) { wrap.appendChild(btn); }
                        try { pycmd('ankiscape_log:inserted_floating'); } catch(e){}
                    }
                } catch (e) {
                    try { pycmd('ankiscape_log:js_error'); } catch(_){}
                }
            })();
            """
            js = js.replace("__ENABLE_FLOATING__", "true" if enable_floating else "false").replace("__POS__", float_pos).replace("__ICON_DATA_URI__", _icon_uri)
            deck_browser.web.eval(js)
            debug_log("_did_render: eval injected fallback button if absent")
        except Exception:
            debug_log("_did_render: eval failed")

    # Register hooks: remove then append (avoid membership tests that may fail)
    try:
        try:
            _hooks.deck_browser_will_render_content.remove(_add_button)
        except Exception:
            pass
        _hooks.deck_browser_will_render_content.append(_add_button)
        debug_log("registered: deck_browser_will_render_content")
    except Exception as e:
        debug_log(f"register failed: deck_browser_will_render_content: {e}")
    try:
        try:
            _hooks.deck_browser_did_render.remove(_did_render)
        except Exception:
            pass
        _hooks.deck_browser_did_render.append(_did_render)
        debug_log("registered: deck_browser_did_render")
    except Exception as e:
        debug_log(f"register failed: deck_browser_did_render: {e}")
    try:
        try:
            _hooks.webview_did_receive_js_message.remove(_on_js_message)
        except Exception:
            pass
        _hooks.webview_did_receive_js_message.append(_on_js_message)
        debug_log("registered: webview_did_receive_js_message")
    except Exception as e:
        debug_log(f"register failed: webview_did_receive_js_message: {e}")

    # Add to the deck options (gear) menu as an additional entry point
    def _will_show_options_menu(menu, deck_id):  # type: ignore[no-redef]
        try:
            act = menu.addAction("AnkiScape")
            act.triggered.connect(lambda: _on_main_menu())
            debug_log("will_show_options_menu: added action")
        except Exception:
            debug_log("will_show_options_menu: failed to add action")
    try:
        try:
            _hooks.deck_browser_will_show_options_menu.remove(_will_show_options_menu)
        except Exception:
            pass
        _hooks.deck_browser_will_show_options_menu.append(_will_show_options_menu)
        debug_log("registered: deck_browser_will_show_options_menu")
    except Exception as e:
        debug_log(f"register failed: deck_browser_will_show_options_menu: {e}")

    # Legacy addHook fallback for older environments (name: deckBrowserWillRenderContent)
    try:
        def _legacy_add_button(content):
            debug_log("_legacy_add_button: called")
            try:
                db_content = _DBC(stats=getattr(content, "stats", None), tree=getattr(content, "tree", None))
                before_stats, before_tree = db_content.stats, db_content.tree
                db_content = inject_into_deck_browser_content(db_content)
                if db_content.stats != before_stats:
                    content.stats = db_content.stats
                    debug_log("_legacy_add_button: injected into stats")
                elif db_content.tree != before_tree:
                    content.tree = db_content.tree
                    debug_log("_legacy_add_button: injected into tree")
                else:
                    debug_log("_legacy_add_button: already present; no injection")
            except Exception as e:
                debug_log(f"_legacy_add_button: error {e}")
        addHook("deckBrowserWillRenderContent", _legacy_add_button)
        debug_log("legacy registered: deckBrowserWillRenderContent")
    except Exception as e:
        debug_log(f"legacy register failed: deckBrowserWillRenderContent: {e}")

    _ANKISCAPE_HOOKS_REGISTERED = True

    # Also hook Overview rendering to inject floating pill on the pre-review screen
    try:
        from aqt import gui_hooks as _hooks2  # type: ignore
        # overview_did_refresh exists on modern Anki; if not, we'll use legacy below
        if hasattr(_hooks2, 'overview_did_refresh'):
            _hooks2.overview_did_refresh.append(lambda overview: _inject_overview_floating_button(overview))
            debug_log("registered: overview_did_refresh")
        elif hasattr(_hooks2, 'overview_will_render_content'):
            _hooks2.overview_will_render_content.append(lambda overview, content: _inject_overview_floating_button(overview, content))
            debug_log("registered: overview_will_render_content")
    except Exception:
        debug_log("register failed: overview gui_hooks")
    try:
        addHook("overviewWillRender", lambda *a, **k: _inject_overview_floating_button())
        debug_log("legacy registered: overviewWillRender")
    except Exception as e:
        debug_log(f"legacy register failed: overviewWillRender: {e}")


def _force_deck_browser_refresh():
    """Trigger a Deck Browser rerender so injected content becomes visible immediately."""
    try:
        db = getattr(mw, "deckBrowser", None)
        if db is None:
            debug_log("force_refresh: no deckBrowser present")
            return
        # Prefer refresh when available, otherwise renderPage
        if hasattr(db, "refresh"):
            debug_log("force_refresh: calling deckBrowser.refresh()")
            db.refresh()
        elif hasattr(db, "renderPage"):
            debug_log("force_refresh: calling deckBrowser.renderPage()")
            db.renderPage()
    except Exception:
        debug_log("force_refresh: failed to refresh")
        pass
