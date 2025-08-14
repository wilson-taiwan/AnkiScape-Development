# ui.py - UI components and dialogs for AnkiScape

from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
import os
from typing import Optional
from .constants import (
    EXP_TABLE,
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
    ACHIEVEMENTS,
    current_dir,
)
from .logic_pure import can_cut_tree_pure, can_mine_ore_pure, can_craft_item_pure

# UI Classes
class ExpPopup(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet("""
            background-color: rgba(70, 130, 180, 200);
            color: white;
            border-radius: 10px;
            padding: 5px;
            font-weight: bold;
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide()

    def show_exp(self, exp):
        self.setText(f"+{exp} XP")
        self.adjustSize()
        self.show()
        self.move(self.parent().width() - self.width() - 20, self.parent().height() - 100)
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(2000)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_animation.finished.connect(self.hide)
        self.float_animation = QPropertyAnimation(self, b"pos")
        self.float_animation.setDuration(2000)
        start_pos = self.pos()
        end_pos = start_pos - QPoint(0, 50)
        self.float_animation.setStartValue(start_pos)
        self.float_animation.setEndValue(end_pos)
        self.float_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_animation.start()
        self.float_animation.start()

# UI Functions
# ...existing code...
# Move all dialog, popup, and menu functions here from __init__.py

def show_error_message(title: str, message: str):
    """Centralized error dialog helper."""
    error_dialog = QMessageBox(mw)
    error_dialog.setIcon(QMessageBox.Icon.Warning)
    error_dialog.setWindowTitle(title)
    error_dialog.setText(message)
    error_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
    error_dialog.exec()


def show_level_up_dialog(skill: str):
    """Level-up dialog with a skill icon."""
    dialog = QDialog(mw)
    dialog.setWindowTitle("Level Up!")
    dialog.setFixedSize(380, 200)
    layout = QVBoxLayout()

    # Icon row
    icon_map = {
        "Mining": "mining_icon.png",
        "Woodcutting": "woodcutting_icon.png",
        "Smithing": "smithing_icon.png",
        "Crafting": "crafting_icon.png",
    }
    icon_file = icon_map.get(skill)
    if icon_file:
        icon_path = os.path.join(current_dir, "icon", icon_file)
        if os.path.exists(icon_path):
            icon_label = QLabel()
            pixmap = QPixmap(icon_path)
            icon_label.setPixmap(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

    msg = QLabel(f"Congratulations! You've advanced a {skill} level!")
    msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(msg)

    ok_button = QPushButton("OK")
    ok_button.clicked.connect(dialog.accept)
    layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)

    dialog.setLayout(layout)
    dialog.exec()


def show_achievement_dialog(achievement: str, data: dict):
    """Achievement dialog with an icon."""
    dialog = QDialog(mw)
    dialog.setWindowTitle("Achievement Unlocked!")
    dialog.setFixedSize(420, 240)
    layout = QVBoxLayout()

    # Try a specific icon based on achievement name, otherwise use generic
    icon_path = os.path.join(current_dir, "icon", f"{achievement.lower().replace(' ', '_')}.png")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(current_dir, "icon", "achievement_icon.png")
    if os.path.exists(icon_path):
        icon_label = QLabel()
        pixmap = QPixmap(icon_path)
        icon_label.setPixmap(pixmap.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

    title = QLabel(achievement)
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setStyleSheet("font-size: 16px; font-weight: bold;")
    layout.addWidget(title)

    desc = QLabel(data.get("description", ""))
    desc.setWordWrap(True)
    layout.addWidget(desc, alignment=Qt.AlignmentFlag.AlignCenter)

    ok_button = QPushButton("OK")
    ok_button.clicked.connect(dialog.accept)
    layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)

    dialog.setLayout(layout)
    dialog.exec()


def create_menu(on_main_menu):
    """Create a single AnkiScape > Menu entry that opens the consolidated window."""
    menu = QMenu("AnkiScape", mw)
    mw.form.menubar.addMenu(menu)
    main_action = menu.addAction("Menu")
    main_action.triggered.connect(on_main_menu)


def update_menu_visibility(current_skill: str):
    """No-op: single consolidated menu item is always visible."""
    return


def show_main_menu(
    player_data: dict,
    current_skill: str,
    can_smelt_any_bar: bool,
    on_save_skill,
    on_set_ore,
    on_set_tree,
    on_set_bar,
    on_set_craft,
    on_open_stats,
    on_open_achievements,
):
    """Show a consolidated window with tabs for Skills, Mining, Woodcutting, Smithing, Crafting,
    and quick access buttons for Stats and Achievements.
    Callbacks apply changes and handle persistence in the caller.
    """
    dialog = QDialog(mw)
    dialog.setWindowTitle("AnkiScape Menu")
    dialog.setMinimumWidth(700)
    dialog.setMinimumHeight(600)

    layout = QVBoxLayout()
    tabs = QTabWidget()

    # Skills tab
    skills_tab = QWidget()
    s_layout = QVBoxLayout(skills_tab)
    skill_combo = QComboBox()
    skills = ["None", "Mining", "Woodcutting", "Smithing", "Crafting"]
    skill_combo.addItems(skills)
    skill_combo.setCurrentText(current_skill)
    s_layout.addWidget(QLabel("Current Skill:"))
    s_layout.addWidget(skill_combo)
    warn = QLabel("")
    warn.setStyleSheet("color: red;")
    s_layout.addWidget(warn)

    def _update_warn():
        if skill_combo.currentText() == "Smithing" and not can_smelt_any_bar:
            warn.setText("You don't have enough ores to smelt any bars. Mine some ores first!")
        else:
            warn.setText("")

    _update_warn()
    skill_combo.currentTextChanged.connect(lambda _: _update_warn())
    save_btn = QPushButton("Save Skill")
    save_btn.clicked.connect(lambda: on_save_skill(skill_combo.currentText()))
    s_layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignLeft)
    tabs.addTab(skills_tab, "Skills")

    # Mining tab
    mining_tab = QWidget()
    m_layout = QVBoxLayout(mining_tab)
    m_layout.addWidget(QLabel("Select Ore to Mine"))
    ore_list = QListWidget()
    for ore, data in ORE_DATA.items():
        item = QListWidgetItem(f"{ore} (Lvl {data['level']})")
        item.setData(Qt.ItemDataRole.UserRole, ore)
        if not can_mine_ore_pure(player_data.get("mining_level", 1), ore, ORE_DATA):
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
        ore_list.addItem(item)
        if ore == player_data.get("current_ore"):
            ore_list.setCurrentItem(item)
    m_layout.addWidget(ore_list)
    m_apply = QPushButton("Apply")
    def _apply_ore():
        current = ore_list.currentItem()
        if current:
            on_set_ore(current.data(Qt.ItemDataRole.UserRole))
    m_apply.clicked.connect(_apply_ore)
    m_layout.addWidget(m_apply, alignment=Qt.AlignmentFlag.AlignLeft)
    tabs.addTab(mining_tab, "Mining")

    # Woodcutting tab
    wood_tab = QWidget()
    w_layout = QVBoxLayout(wood_tab)
    w_layout.addWidget(QLabel("Select Tree to Cut"))
    tree_list = QListWidget()
    for tree, data in TREE_DATA.items():
        item = QListWidgetItem(f"{tree} (Lvl {data['level']})")
        item.setData(Qt.ItemDataRole.UserRole, tree)
        if not can_cut_tree_pure(player_data.get("woodcutting_level", 1), tree, TREE_DATA):
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
        tree_list.addItem(item)
        if tree == player_data.get("current_tree"):
            tree_list.setCurrentItem(item)
    w_layout.addWidget(tree_list)
    w_apply = QPushButton("Apply")
    w_apply.clicked.connect(lambda: tree_list.currentItem() and on_set_tree(tree_list.currentItem().data(Qt.ItemDataRole.UserRole)))
    w_layout.addWidget(w_apply, alignment=Qt.AlignmentFlag.AlignLeft)
    tabs.addTab(wood_tab, "Woodcutting")

    # Smithing tab
    smith_tab = QWidget()
    sm_layout = QVBoxLayout(smith_tab)
    sm_layout.addWidget(QLabel("Select Bar to Smelt"))
    bar_list = QListWidget()
    for bar, data in BAR_DATA.items():
        item = QListWidgetItem(f"{bar} (Lvl {data['level']})")
        item.setData(Qt.ItemDataRole.UserRole, bar)
        if data.get("level", 1) > player_data.get("smithing_level", 1):
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
        bar_list.addItem(item)
        if bar == player_data.get("current_bar"):
            bar_list.setCurrentItem(item)
    sm_layout.addWidget(bar_list)
    sm_apply = QPushButton("Apply")
    sm_apply.clicked.connect(lambda: bar_list.currentItem() and on_set_bar(bar_list.currentItem().data(Qt.ItemDataRole.UserRole)))
    sm_layout.addWidget(sm_apply, alignment=Qt.AlignmentFlag.AlignLeft)
    tabs.addTab(smith_tab, "Smithing")

    # Crafting tab
    craft_tab = QWidget()
    c_layout = QVBoxLayout(craft_tab)
    c_layout.addWidget(QLabel("Select Item to Craft"))
    craft_list = QListWidget()
    for item_name, spec in CRAFTING_DATA.items():
        item = QListWidgetItem(f"{item_name} (Lvl {spec['level']})")
        item.setData(Qt.ItemDataRole.UserRole, item_name)
        if not can_craft_item_pure(player_data.get("crafting_level", 1), player_data.get("inventory", {}), item_name, CRAFTING_DATA):
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
        craft_list.addItem(item)
        if item_name == player_data.get("current_craft"):
            craft_list.setCurrentItem(item)
    c_layout.addWidget(craft_list)
    c_apply = QPushButton("Apply")
    c_apply.clicked.connect(lambda: craft_list.currentItem() and on_set_craft(craft_list.currentItem().data(Qt.ItemDataRole.UserRole)))
    c_layout.addWidget(c_apply, alignment=Qt.AlignmentFlag.AlignLeft)
    tabs.addTab(craft_tab, "Crafting")

    # Stats tab
    stats_tab = QWidget()
    st_layout = QVBoxLayout(stats_tab)
    st_layout.addWidget(QLabel("Open detailed stats in a dialog"))
    st_btn = QPushButton("Open Stats")
    st_btn.clicked.connect(on_open_stats)
    st_layout.addWidget(st_btn, alignment=Qt.AlignmentFlag.AlignLeft)
    tabs.addTab(stats_tab, "Stats")

    # Achievements tab
    ach_tab = QWidget()
    a_layout = QVBoxLayout(ach_tab)
    a_layout.addWidget(QLabel("Open achievements in a dialog"))
    a_btn = QPushButton("Open Achievements")
    a_btn.clicked.connect(on_open_achievements)
    a_layout.addWidget(a_btn, alignment=Qt.AlignmentFlag.AlignLeft)
    tabs.addTab(ach_tab, "Achievements")

    layout.addWidget(tabs)
    close = QPushButton("Close")
    close.clicked.connect(dialog.accept)
    layout.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)
    dialog.setLayout(layout)
    dialog.exec()


def show_tree_selection_dialog(current_tree: str, woodcutting_level: int, TREE_DATA: dict, TREE_IMAGES: dict) -> Optional[str]:
    """Render a Tree Selection dialog and return the chosen tree name or None if cancelled."""
    dialog = QDialog(mw)
    dialog.setWindowTitle("Tree Selection")
    dialog.setMinimumWidth(400)
    layout = QVBoxLayout()

    title_label = QLabel("Select Tree to Cut")
    title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50; margin-bottom: 15px;")
    layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

    grid_layout = QGridLayout()
    row, col = 0, 0
    button_group = QButtonGroup(dialog)

    for tree_name, tree_data in TREE_DATA.items():
        tree_widget = QWidget()
        tree_layout = QVBoxLayout(tree_widget)

        tree_image = QLabel()
        pixmap = QPixmap(TREE_IMAGES[tree_name])
        tree_image.setPixmap(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio))
        tree_layout.addWidget(tree_image, alignment=Qt.AlignmentFlag.AlignCenter)

        tree_info = QLabel(f"{tree_name}\nLevel: {tree_data['level']}")
        tree_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tree_layout.addWidget(tree_info)

        radio_button = QRadioButton()
        radio_button.setChecked(tree_name == current_tree)
        if not can_cut_tree_pure(woodcutting_level, tree_name, TREE_DATA):
            radio_button.setEnabled(False)
            tree_widget.setStyleSheet("color: gray;")
        button_group.addButton(radio_button)
        radio_button.tree_name = tree_name
        tree_layout.addWidget(radio_button, alignment=Qt.AlignmentFlag.AlignCenter)

        grid_layout.addWidget(tree_widget, row, col)
        col += 1
        if col > 2:
            col = 0
            row += 1

    layout.addLayout(grid_layout)

    button_layout = QHBoxLayout()
    ok_button = QPushButton("OK")
    cancel_button = QPushButton("Cancel")
    ok_button.clicked.connect(dialog.accept)
    cancel_button.clicked.connect(dialog.reject)
    button_layout.addWidget(cancel_button)
    button_layout.addWidget(ok_button)
    layout.addLayout(button_layout)

    dialog.setLayout(layout)

    if dialog.exec():
        selected_button = button_group.checkedButton()
        if selected_button:
            return selected_button.tree_name
    return None


def show_ore_selection_dialog(current_ore: str, mining_level: int, ORE_DATA: dict, ORE_IMAGES: dict) -> Optional[str]:
    """Render an Ore Selection dialog and return the chosen ore name or None if cancelled."""
    dialog = QDialog(mw)
    dialog.setWindowTitle("Ore Selection")
    dialog.setMinimumWidth(400)
    layout = QVBoxLayout()

    title_label = QLabel("Select Ore to Mine")
    title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50; margin-bottom: 15px;")
    layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

    grid_layout = QGridLayout()
    row, col = 0, 0
    button_group = QButtonGroup(dialog)

    for ore, data in ORE_DATA.items():
        ore_widget = QWidget()
        ore_layout = QVBoxLayout(ore_widget)

        ore_image = QLabel()
        pixmap = QPixmap(ORE_IMAGES[ore])
        ore_image.setPixmap(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio))
        ore_layout.addWidget(ore_image, alignment=Qt.AlignmentFlag.AlignCenter)

        ore_info = QLabel(f"{ore}\nLevel: {data['level']}")
        ore_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ore_layout.addWidget(ore_info)

        radio_button = QRadioButton()
        radio_button.setChecked(ore == current_ore)
        if not can_mine_ore_pure(mining_level, ore, ORE_DATA):
            radio_button.setEnabled(False)
            ore_widget.setStyleSheet("color: gray;")
        button_group.addButton(radio_button)
        radio_button.ore_name = ore
        ore_layout.addWidget(radio_button, alignment=Qt.AlignmentFlag.AlignCenter)

        grid_layout.addWidget(ore_widget, row, col)
        col += 1
        if col > 2:
            col = 0
            row += 1

    layout.addLayout(grid_layout)

    button_layout = QHBoxLayout()
    ok_button = QPushButton("OK")
    cancel_button = QPushButton("Cancel")
    ok_button.clicked.connect(dialog.accept)
    cancel_button.clicked.connect(dialog.reject)
    button_layout.addWidget(cancel_button)
    button_layout.addWidget(ok_button)
    layout.addLayout(button_layout)

    dialog.setLayout(layout)

    if dialog.exec():
        selected_button = button_group.checkedButton()
        if selected_button:
            return selected_button.ore_name
    return None


def show_bar_selection_dialog(current_bar: str, smithing_level: int, BAR_DATA: dict, BAR_IMAGES: dict) -> Optional[str]:
    dialog = QDialog(mw)
    dialog.setWindowTitle("Bar Selection")
    dialog.setMinimumWidth(400)
    layout = QVBoxLayout()

    title_label = QLabel("Select Bar to Smelt")
    title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50; margin-bottom: 15px;")
    layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

    grid_layout = QGridLayout()
    row, col = 0, 0
    button_group = QButtonGroup(dialog)

    for bar_name, bar_data in BAR_DATA.items():
        bar_widget = QWidget()
        bar_layout = QVBoxLayout(bar_widget)

        bar_image = QLabel()
        pixmap = QPixmap(BAR_IMAGES[bar_name])
        bar_image.setPixmap(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio))
        bar_layout.addWidget(bar_image, alignment=Qt.AlignmentFlag.AlignCenter)

        bar_info = QLabel(f"{bar_name}\nLevel: {bar_data['level']}")
        bar_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bar_layout.addWidget(bar_info)

        radio_button = QRadioButton()
        radio_button.setChecked(bar_name == current_bar)
        if bar_data.get("level", 1) > smithing_level:
            radio_button.setEnabled(False)
            bar_widget.setStyleSheet("color: gray;")
        button_group.addButton(radio_button)
        radio_button.bar_name = bar_name
        bar_layout.addWidget(radio_button, alignment=Qt.AlignmentFlag.AlignCenter)

        grid_layout.addWidget(bar_widget, row, col)
        col += 1
        if col > 2:
            col = 0
            row += 1

    layout.addLayout(grid_layout)

    button_layout = QHBoxLayout()
    ok_button = QPushButton("OK")
    cancel_button = QPushButton("Cancel")
    ok_button.clicked.connect(dialog.accept)
    cancel_button.clicked.connect(dialog.reject)
    button_layout.addWidget(cancel_button)
    button_layout.addWidget(ok_button)
    layout.addLayout(button_layout)

    dialog.setLayout(layout)

    if dialog.exec():
        selected_button = button_group.checkedButton()
        if selected_button:
            return selected_button.bar_name
    return None


def show_craft_selection_dialog(current_craft: str, crafting_level: int, inventory: dict, CRAFTING_DATA: dict, CRAFTED_ITEM_IMAGES: dict) -> Optional[str]:
    dialog = QDialog(mw)
    dialog.setWindowTitle("Craft Selection")
    dialog.setMinimumWidth(400)
    dialog.setMinimumHeight(500)

    layout = QVBoxLayout()
    title_label = QLabel("Select Item to Craft")
    title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50; margin-bottom: 15px;")
    layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setStyleSheet("border: none;")

    scroll_content = QWidget()
    grid_layout = QGridLayout(scroll_content)
    grid_layout.setSpacing(10)

    row, col = 0, 0
    button_group = QButtonGroup(dialog)

    for item, data in CRAFTING_DATA.items():
        item_widget = QWidget()
        item_layout = QVBoxLayout(item_widget)

        item_image = QLabel()
        pixmap = QPixmap(CRAFTED_ITEM_IMAGES.get(item, ""))
        item_image.setPixmap(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio))
        item_layout.addWidget(item_image, alignment=Qt.AlignmentFlag.AlignCenter)

        item_info = QLabel(f"{item}\nLevel: {data['level']}")
        item_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        item_layout.addWidget(item_info)

        radio_button = QRadioButton()
        radio_button.setChecked(item == current_craft)
        if not can_craft_item_pure(crafting_level, inventory, item, CRAFTING_DATA):
            radio_button.setEnabled(False)
            item_widget.setStyleSheet("color: gray;")

        button_group.addButton(radio_button)
        radio_button.item_name = item
        item_layout.addWidget(radio_button, alignment=Qt.AlignmentFlag.AlignCenter)

        grid_layout.addWidget(item_widget, row, col)
        col += 1
        if col > 2:
            col = 0
            row += 1

    scroll_area.setWidget(scroll_content)
    layout.addWidget(scroll_area)

    button_layout = QHBoxLayout()
    ok_button = QPushButton("OK")
    cancel_button = QPushButton("Cancel")
    ok_button.clicked.connect(dialog.accept)
    cancel_button.clicked.connect(dialog.reject)
    button_layout.addWidget(cancel_button)
    button_layout.addWidget(ok_button)
    layout.addLayout(button_layout)

    dialog.setLayout(layout)

    if dialog.exec():
        selected_button = button_group.checkedButton()
        if selected_button:
            return selected_button.item_name
    return None


def show_skill_selection_dialog(current_skill: str, can_smelt_any_bar: bool) -> Optional[str]:
    """Skill selection dialog that returns the chosen skill or None if cancelled.
    Disables Smithing when no bars can be smelted (per provided boolean).
    """
    dialog = QDialog(mw)
    dialog.setWindowTitle("Skill Selection")
    layout = QVBoxLayout()

    skill_combo = QComboBox()
    skills = ["None", "Mining", "Woodcutting", "Smithing", "Crafting"]
    skill_combo.addItems(skills)
    skill_combo.setCurrentText(current_skill)
    layout.addWidget(skill_combo)

    warning_label = QLabel("")
    warning_label.setStyleSheet("color: red;")
    layout.addWidget(warning_label)

    def update_warning():
        if skill_combo.currentText() == "Smithing" and not can_smelt_any_bar:
            warning_label.setText("You don't have enough ores to smelt any bars. Mine some ores first!")
            save_button.setEnabled(False)
        else:
            warning_label.setText("")
            save_button.setEnabled(True)

    skill_combo.currentTextChanged.connect(lambda _: update_warning())

    button_layout = QHBoxLayout()
    cancel_button = QPushButton("Cancel")
    save_button = QPushButton("Save")

    cancel_button.clicked.connect(dialog.reject)
    save_button.clicked.connect(dialog.accept)

    button_layout.addWidget(cancel_button)
    button_layout.addWidget(save_button)
    layout.addLayout(button_layout)

    dialog.setLayout(layout)
    update_warning()

    if dialog.exec():
        return skill_combo.currentText()
    return None


def show_review_popup():
    if mw.col.get_config("ankiscape_hide_review_popup", False):
        return

    dialog = QDialog(mw)
    dialog.setWindowTitle("AnkiScape - Enjoying the add-on?")
    layout = QVBoxLayout()

    message = QLabel(
        "If you're enjoying AnkiScape, please consider leaving a review. Your feedback helps others discover the add-on!")
    layout.addWidget(message)

    review_button = QPushButton("Leave a Review")
    review_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://ankiweb.net/shared/review/1808450369")))
    layout.addWidget(review_button)

    hide_checkbox = QCheckBox("Don't show this message again")
    layout.addWidget(hide_checkbox)

    close_button = QPushButton("Close")
    close_button.clicked.connect(dialog.accept)
    layout.addWidget(close_button)

    dialog.setLayout(layout)

    if dialog.exec():
        if hide_checkbox.isChecked():
            mw.col.set_config("ankiscape_hide_review_popup", True)
            mw.col.save()


def show_stats(player_data: dict, current_skill: str):
    """Render the Stats dialog using provided player_data and current_skill."""
    try:
        dialog = QDialog(mw)
        dialog.setWindowTitle("AnkiScape Stats")
        dialog.setMinimumWidth(700)
        dialog.setMinimumHeight(700)

        dialog.setStyleSheet(
            """
            QDialog { background-color: @CANVAS; }
            QLabel { color: @TEXT; }
            QTabWidget::pane { border: 1px solid @BORDER; background-color: @CANVAS; border-radius: 5px; }
            QTabBar::tab { background-color: @BUTTON; color: @TEXT; padding: 8px 16px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background-color: @CANVAS; border-bottom: 2px solid @ACCENT; }
            QTabBar::tab:hover { background-color: @HOVER; }
            """
        )

        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        status_label = QLabel(f"Current Skill: {current_skill}")
        status_label.setStyleSheet(
            """
            font-size: 18px;
            font-weight: bold;
            color: @ACCENT;
            padding: 10px;
            background-color: @CANVAS;
            border-radius: 5px;
            """
        )
        main_layout.addWidget(status_label, alignment=Qt.AlignmentFlag.AlignCenter)

        tabs = QTabWidget()

        def create_label(text, is_header=False):
            label = QLabel(text)
            if is_header:
                label.setStyleSheet(
                    """
                    font-size: 16px;
                    font-weight: bold;
                    color: @ACCENT;
                    margin-top: 15px;
                    margin-bottom: 10px;
                    """
                )
            else:
                label.setStyleSheet("font-size: 14px;")
            return label

        def create_skill_tab(skill_name):
            tab = QWidget()
            tab_layout = QVBoxLayout()
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setStyleSheet("border: none;")
            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)
            scroll_layout.setSpacing(10)
            scroll_layout.setContentsMargins(20, 20, 20, 20)

            scroll_layout.addWidget(create_label(f"{skill_name} Stats", True))
            stats_layout = QGridLayout()
            stats_layout.setColumnStretch(1, 1)
            stats_layout.setHorizontalSpacing(15)
            stats_layout.setVerticalSpacing(10)

            level = player_data.get(f"{skill_name.lower()}_level", 1)
            exp = round(player_data.get(f"{skill_name.lower()}_exp", 0), 1)

            stats_layout.addWidget(create_label(f"{skill_name} Level:"), 0, 0)
            stats_layout.addWidget(create_label(str(level), True), 0, 1)
            stats_layout.addWidget(create_label("Total Experience:"), 1, 0)
            stats_layout.addWidget(create_label(f"{exp:,}", True), 1, 1)

            if level < 99:
                exp_to_next = round(max(0, EXP_TABLE[level] - exp), 1)
                stats_layout.addWidget(create_label("Experience to Next Level:"), 2, 0)
                stats_layout.addWidget(create_label(f"{exp_to_next:,}", True), 2, 1)

            progress_bar = QProgressBar()
            progress_percentage = (exp - EXP_TABLE[level - 1]) / (EXP_TABLE[level] - EXP_TABLE[level - 1]) * 100
            progress_bar.setValue(int(progress_percentage))
            progress_bar.setFormat("")
            progress_bar.setStyleSheet(
                """
                QProgressBar {
                    border: 1px solid @BORDER;
                    border-radius: 5px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: @ACCENT;
                    border-radius: 5px;
                }
                """
            )
            stats_layout.addWidget(create_label("Level Progress:"), 3, 0)
            stats_layout.addWidget(progress_bar, 3, 1)

            scroll_layout.addLayout(stats_layout)

            scroll_layout.addWidget(create_label(f"{skill_name} Inventory", True))
            inventory_layout = QGridLayout()
            inventory_layout.setColumnStretch(1, 1)
            inventory_layout.setHorizontalSpacing(15)
            inventory_layout.setVerticalSpacing(10)

            row = 0
            for item, amount in player_data.get("inventory", {}).items():
                if (
                    (skill_name == "Mining" and (item in ORE_DATA or item in GEM_DATA))
                    or (skill_name == "Woodcutting" and item in TREE_DATA)
                    or (skill_name == "Smithing" and item in BAR_DATA)
                    or (skill_name == "Crafting" and item in CRAFTING_DATA)
                ):
                    item_image = QLabel()
                    pixmap = QPixmap(
                        ORE_IMAGES.get(item)
                        or TREE_IMAGES.get(item)
                        or BAR_IMAGES.get(item)
                        or GEM_IMAGES.get(item)
                        or CRAFTED_ITEM_IMAGES.get(item)
                    )
                    item_image.setPixmap(pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio))
                    inventory_layout.addWidget(item_image, row, 0)

                    inventory_layout.addWidget(create_label(item), row, 1)
                    inventory_layout.addWidget(create_label(str(amount), True), row, 2)
                    row += 1

            scroll_layout.addLayout(inventory_layout)

            scroll_content.setLayout(scroll_layout)
            scroll_area.setWidget(scroll_content)
            tab_layout.addWidget(scroll_area)
            tab.setLayout(tab_layout)
            return tab

        tabs.addTab(create_skill_tab("Mining"), "Mining")
        tabs.addTab(create_skill_tab("Woodcutting"), "Woodcutting")
        tabs.addTab(create_skill_tab("Smithing"), "Smithing")
        tabs.addTab(create_skill_tab("Crafting"), "Crafting")

        main_layout.addWidget(tabs)
        dialog.setLayout(main_layout)
        dialog.exec()

    except Exception as e:
        print(f"Error in show_stats: {str(e)}")
        import traceback
        traceback.print_exc()


def show_achievements(player_data: dict):
    """Render the Achievements dialog based on provided player_data."""
    dialog = QDialog(mw)
    dialog.setWindowTitle("Achievements")
    dialog.setMinimumWidth(700)
    dialog.setMinimumHeight(500)

    dialog.setStyleSheet(
        """
        QDialog {
            background-color: #f5f5f5;
        }
        """
    )

    layout = QVBoxLayout()

    title_label = QLabel("Achievements")
    title_label.setStyleSheet(
        """
        font-size: 28px;
        font-weight: bold;
        color: #333333;
        margin-bottom: 20px;
        """
    )
    layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

    tabs = QTabWidget()
    tabs.setStyleSheet(
        """
        QTabWidget::pane {
            border: none;
            background-color: white;
        }
        QTabBar::tab {
            background-color: #e0e0e0;
            color: #333333;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 2px solid #4CAF50;
        }
        QTabBar::tab:hover {
            background-color: #d0d0d0;
        }
        """
    )

    difficulties = ["Easy", "Moderate", "Difficult", "Very Challenging"]

    for difficulty in difficulties:
        tab = QWidget()
        tab_layout = QVBoxLayout()
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        for achievement, data in ACHIEVEMENTS.items():
            if data["difficulty"] == difficulty:
                achievement_widget = QWidget()
                achievement_layout = QHBoxLayout()

                icon_label = QLabel()
                icon_path = os.path.join(current_dir, "icon", f"{achievement.lower().replace(' ', '_')}.png")
                if os.path.exists(icon_path):
                    pixmap = QPixmap(icon_path)
                else:
                    pixmap = QPixmap(os.path.join(current_dir, "icon", "achievement_icon.png"))
                icon_label.setPixmap(pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio))
                achievement_layout.addWidget(icon_label)

                info_widget = QWidget()
                info_layout = QVBoxLayout()
                name_label = QLabel(achievement)
                name_label.setStyleSheet("font-weight: bold; color: #333333; font-size: 16px;")
                desc_label = QLabel(data["description"])
                desc_label.setWordWrap(True)
                desc_label.setStyleSheet("color: #666666; font-size: 14px;")
                info_layout.addWidget(name_label)
                info_layout.addWidget(desc_label)
                info_widget.setLayout(info_layout)
                achievement_layout.addWidget(info_widget, stretch=1)

                completed = achievement in player_data["completed_achievements"]
                status_label = QLabel("✓" if completed else "")
                status_label.setStyleSheet("color: #4CAF50; font-size: 24px; font-weight: bold;")
                achievement_layout.addWidget(status_label)

                achievement_widget.setLayout(achievement_layout)
                achievement_widget.setStyleSheet(
                    f"""
                    background-color: {'#e8f5e9' if completed else 'white'};
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 8px;
                    """
                )

                scroll_layout.addWidget(achievement_widget)

        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")

        tab_layout.addWidget(scroll_area)
        tab.setLayout(tab_layout)
        tabs.addTab(tab, difficulty)

    layout.addWidget(tabs)

    completed_count = len(player_data["completed_achievements"])
    total_count = len(ACHIEVEMENTS)
    progress_percentage = (completed_count / total_count) * 100
    progress_label = QLabel(f"Completed: {completed_count}/{total_count} ({progress_percentage:.1f}%)")
    progress_label.setStyleSheet(
        """
        font-size: 18px;
        margin-top: 20px;
        color: #333333;
        """
    )
    layout.addWidget(progress_label, alignment=Qt.AlignmentFlag.AlignCenter)

    progress_bar = QProgressBar()
    progress_bar.setValue(int(progress_percentage))
    progress_bar.setTextVisible(False)
    progress_bar.setStyleSheet(
        """
        QProgressBar {
            border: none;
            background-color: #e0e0e0;
            border-radius: 4px;
            height: 8px;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
            border-radius: 4px;
        }
        """
    )
    layout.addWidget(progress_bar)

    dialog.setLayout(layout)
    dialog.exec()
