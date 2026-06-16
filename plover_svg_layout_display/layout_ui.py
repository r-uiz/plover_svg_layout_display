import os

from typing import Callable, List, Tuple, Union

from plover import system
from plover.engine import StenoEngine
from plover.oslayer.config import PLUGINS_PLATFORM
from plover.gui_qt.tool import Tool
from plover.steno import Stroke
from plover import log

from PySide6.QtWidgets import QHBoxLayout, QGraphicsView
from PySide6.QtGui import QAction
from PySide6.QtGui import QKeySequence, QMouseEvent
from PySide6.QtCore import (
    Qt, QRect, QSettings, QTimer, QVariantAnimation, QAbstractAnimation, QEasingCurve
)

from plover_svg_layout_display.resources_rc import *
from plover_svg_layout_display.config_ui import ConfigUI
from plover_svg_layout_display.layout_config import CONFIG_ITEMS, CONFIG_TYPES, SYSTEM_PREFIX, LayoutConfig
from plover_svg_layout_display.svg_widget import LayoutWidget
from plover_svg_layout_display.qt_utils import load_qt_text


STYLESHEET = "border:0px; background:transparent;"
DEFAULT_SVG = ":/svgld/resources/en_layout.svg"
DEFAULT_SCALE = 100
DEFAULT_PY = ":/svgld/resources/en_convert.py"

# Bundled Stenokeyboards Uni v4 presets, shipped on disk inside the package.
# A style ("house"/"mono"/"inverted") plus the Labels / Finger guides checkboxes
# resolve to uni_<style>[_labels][_guides].svg; uni_convert.py is shared.
UNI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "uni")
UNI_CONVERT = "uni_convert.py"
GUIDES_GROUP = "guides"

FADE_MS = 220  # snappy cross-fade for the auto-clear


class SVGLayoutDisplayTool(Tool):
    TITLE = "SVG Layout Display"
    ICON = ":/svgld/resources/icon.svg"
    ROLE = "svgld"

    def __init__(self, engine: StenoEngine) -> None:
        super().__init__(engine)
        self.setObjectName("svgld")
        engine.signal_connect("stroked", self.on_stroke)
        engine.signal_connect("config_changed", self.on_config_changed)

        self.system_name = system.NAME
        self.repaint_offset = False
        self.convert_stroke = None
        self.last_group_ids: List[str] = []

        self.config = LayoutConfig()
        self.restore_state()

        # Plover emits `stroked` per committed chord (not key up/down), so a
        # highlight otherwise persists until the next stroke. This single-shot
        # timer clears it after `clear_ms` (0 = hold, never clear).
        self.clear_timer = QTimer(self)
        self.clear_timer.setSingleShot(True)
        self.clear_timer.timeout.connect(self.on_clear)

        # Optional cross-fade for that clear.
        self.fade_anim = QVariantAnimation(self)
        self.fade_anim.setDuration(FADE_MS)
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_anim.valueChanged.connect(self.on_fade_value)
        self.fade_anim.finished.connect(self.on_fade_done)
        self.fade_base: List[str] = []
        self.fade_top: List[str] = []
        self.fade_press: List[str] = []

        self.setup_actions()
        self.setup_trans()
        self.setup_layout()
        self.reload_config()

        self.finished.connect(self.save_state)

    def _restore_state(self, settings: QSettings) -> None:
        # Cross system settings
        for field_name in CONFIG_ITEMS.keys():
            if settings.contains(field_name) and not field_name.startswith(SYSTEM_PREFIX):
                setattr(
                    self.config,
                    field_name,
                    settings.value(field_name, type=CONFIG_TYPES[field_name])
                )

            elif (
                field_name == "force_repaint"
                and PLUGINS_PLATFORM is not None and PLUGINS_PLATFORM == "mac"
            ):
                self.config.force_repaint = True

        # System specific settings
        for field_name in settings.allKeys():
            sys_name, sys_field = (None, None)
            if "/" in field_name:
                sys_name, sys_field = field_name.split("/", 1)
            elif "\\" in field_name:
                sys_name, sys_field = field_name.split("\\", 1)

            if sys_name and sys_field and sys_field in CONFIG_ITEMS.keys():
                if sys_name not in self.config.system_map:
                    self.config.system_map[sys_name] = dict()

                self.config.system_map[sys_name][sys_field] = settings.value(
                    field_name,
                    type=CONFIG_TYPES[sys_field]
                )

    def _save_state(self, settings: QSettings) -> None:
        for key, value in self.config.get_values():
            settings.setValue(key, value)

        for sys_name, sys_map in self.config.system_map.items():
            for key, value in sys_map.items():
                settings.setValue(sys_name + "/" + key, value)

    def view_mouse_move(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPos() - self.drag_position)

    def view_mouse_press(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()

    def view_mouse_double_click(self, event: QMouseEvent) -> None:
        # Frameless + always-on-top means there's no close button; double-click
        # (or Ctrl+X) dismisses the display.
        self.accept()

    def setup_actions(self) -> None:
        self.close_action = QAction(self)
        self.close_action.setText("Close Display")
        self.close_action.triggered.connect(self.accept)
        self.close_action.setShortcut(QKeySequence("Ctrl+X"))
        self.addAction(self.close_action)

        self.settings_action = QAction(self)
        self.settings_action.setText("Configure Display")
        self.settings_action.triggered.connect(self.on_settings)
        self.settings_action.setShortcut(QKeySequence("Ctrl+S"))
        self.addAction(self.settings_action)

    def split_groups(self, group_ids: List[str]) -> Tuple[List[str], List[str], List[str]]:
        # base = neutral cap for every key, press = the pressed caps, top =
        # always-on overlays (finger guides). Used to cross-fade press -> neutral.
        base, press, top = [], [], []
        for gid in group_ids:
            if gid == GUIDES_GROUP:
                top.append(gid)
            elif gid.endswith("_n"):
                base.append(gid)
            else:
                base.append(gid + "_n")
                press.append(gid)
        return base, press, top

    def on_stroke(self, stroke: Union[Stroke, Tuple[str, ...]]) -> None:
        if isinstance(stroke, Stroke):
            stroke_tup = tuple(stroke.steno_keys)
        else:
            stroke_tup = stroke

        if stroke_tup:
            self.stop_fade()

        if self.convert_stroke is not None:
            prev_translations = self._engine.translator_state.prev()
            if not prev_translations:
                output = ""
            else:
                output = prev_translations[-1].english

            group_ids = self.convert_stroke(stroke_tup, output)
            self.last_group_ids = list(group_ids)
            self.svg_widget.update_groups(group_ids)

        if stroke_tup and self.config.clear_ms > 0:
            self.clear_timer.start(self.config.clear_ms)

        self.repaint()

    def on_clear(self) -> None:
        base, press, top = self.split_groups(self.last_group_ids)
        if self.config.fade and press:
            self.fade_base, self.fade_press, self.fade_top = base, press, top
            self.fade_anim.stop()
            self.fade_anim.start()
        else:
            self.on_stroke(tuple())

    def on_fade_value(self, value: float) -> None:
        self.svg_widget.update_blend(
            self.fade_base, self.fade_press, self.fade_top, float(value)
        )
        self.repaint()

    def on_fade_done(self) -> None:
        self.on_stroke(tuple())

    def stop_fade(self) -> None:
        if self.fade_anim.state() == QAbstractAnimation.State.Running:
            self.fade_anim.stop()

    def setup_trans(self) -> None:
        # For some strange reason, even though this piece of code doesn't
        # actually draw anything, the widget refuses to be transparent on
        # some systems unless this is included.
        self.trans_view = QGraphicsView(self)
        self.trans_view.setStyleSheet(STYLESHEET)

    def setup_layout(self) -> None:
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("QWidget#svgld {background:transparent;}")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setToolTip("Double-click or press Ctrl+X to close - Ctrl+S to configure")

        self.svg_widget = LayoutWidget()

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.svg_widget)
        self.setLayout(self.layout)

        self.mouseMoveEvent = self.view_mouse_move
        self.mousePressEvent = self.view_mouse_press
        self.mouseDoubleClickEvent = self.view_mouse_double_click

        self.show()

    def on_config_changed(self, config: dict) -> None:
        new_sys_name = config.get("system_name")
        if not new_sys_name or new_sys_name == self.system_name:
            return

        self.system_name = new_sys_name
        self.reload_config()

    def on_settings(self) -> None:
        config_dialog = ConfigUI(self.config.copy(), self.system_name, self)
        if config_dialog.exec():
            self.config = config_dialog.temp_config
            self.reload_config()

    def load_py_script(self, py_path: str) -> None:
        py_text = load_qt_text(py_path)

        if not py_text.strip():
            self.convert_stroke = None
            return

        try:
            globs = {}
            exec(py_text, globs)

            convert_stroke = globs.get("convert_stroke")
            if not isinstance(convert_stroke, Callable):
                self.convert_stroke = None

            self.convert_stroke = convert_stroke

        except Exception as e:
            log.error("loading Python script from %s failed: %s", py_path, e, exc_info=True)
            self.convert_stroke = None

    def preset_paths(self, sys_config: dict) -> Tuple[Union[str, None], Union[str, None]]:
        style = sys_config.get("system_style", "")
        if not style:
            return (None, None)

        labels = sys_config.get("system_labels", True)
        guides = sys_config.get("system_guides", False)
        name = "uni_%s%s%s.svg" % (
            style,
            "_labels" if labels else "",
            "_guides" if guides else "",
        )
        svg_path = os.path.join(UNI_DIR, name)

        if not os.path.isfile(svg_path):
            log.error("Layout preset not found: %s", svg_path)
            return (None, None)

        return (svg_path, os.path.join(UNI_DIR, UNI_CONVERT))

    def reload_config(self) -> None:
        self.stop_fade()
        self.clear_timer.stop()

        if self.system_name in self.config.system_map:
            sys_config = self.config.system_map[self.system_name]

            preset_svg, preset_py = self.preset_paths(sys_config)
            svg_path = preset_svg if preset_svg else sys_config.get("system_svg")
            py_path = preset_py if preset_py else sys_config.get("system_py")

            if svg_path is not None:
                self.svg_widget.load_svg(
                    svg_path,
                    sys_config.get("system_scale", 100)
                )

            if py_path is not None:
                self.load_py_script(py_path)

        elif self.system_name == "English Stenotype":
            self.svg_widget.load_svg(DEFAULT_SVG, DEFAULT_SCALE)
            self.load_py_script(DEFAULT_PY)
        else:
            log.error("No configuration found for system name: %s", self.system_name)

        self.last_group_ids = []
        self.on_stroke(tuple())

    def repaint_rect(self) -> QRect:
        window_rect = self.rect()
        if self.repaint_offset:
            window_rect.setWidth(window_rect.width() - 1)

        return window_rect

    def repaint(self) -> None:
        self.repaint_offset = not self.repaint_offset
        svg_size = self.svg_widget.svg_size

        if svg_size is not None:
            right_margin_px = 1 * self.config.force_repaint * self.repaint_offset
            self.layout.setContentsMargins(0, 0, right_margin_px, 0)
            self.setFixedWidth(svg_size.width() + right_margin_px)
            self.setFixedHeight(svg_size.height())
