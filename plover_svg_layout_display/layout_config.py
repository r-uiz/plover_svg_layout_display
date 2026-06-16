from typing import List, Tuple, Any


CONFIG_ITEMS = {
    "system_style": "",
    "system_labels": True,
    "system_guides": False,
    "system_svg": "",
    "system_py": "",
    "system_scale": 100,
    "clear_ms": 3000,
    "fade": True,
    "force_repaint": False
}

CONFIG_FILE_PARAMS = {
    "system_svg": ("Select Layout SVG", "Vector Graphics (*.svg)"),
    "system_py": ("Select Python Script", "Python Script (*.py)")
}

# Dropdown choices: (label, stored value). Empty value = "Custom" -> use the
# system_svg / system_py paths. Non-empty values are bundled Uni styles; the
# Labels / Finger guides checkboxes pick the variant file (see layout_ui).
CONFIG_CHOICES = {
    "system_style": [
        ("Custom (use SVG / script paths below)", ""),
        ("Uni - House", "house"),
        ("Uni - Mono", "mono"),
        ("Uni - Inverted", "inverted"),
    ],
}

# Ints rendered as a plain spinbox instead of the percentage one. clear_ms is in
# milliseconds (0 = "Off").
CONFIG_INT_PLAIN = {"clear_ms"}

CONFIG_TYPES = {k: type(v) for k, v in CONFIG_ITEMS.items()}

CONFIG_NAMES = {
    "system_name": "Current System:",
    "system_style": "Layout Preset",
    "system_labels": "Labels",
    "system_guides": "Finger guides",
    "system_svg": "Custom SVG",
    "system_py": "Custom Python Script",
    "system_scale": "Layout Scale",
    "clear_ms": "Auto-clear After",
    "fade": "Fade out on clear",
    "force_repaint": "Force Repaint (macOS)"
}

CONFIG_ORDER = [
    "System Settings",
    "system_name",
    "system_style",
    "system_labels",
    "system_guides",
    "system_svg",
    "system_py",
    "system_scale",

    "Behaviour",
    "clear_ms",
    "fade",

    "Force Repaint (macOS Window Shadow)",
    "force_repaint"
]


SYSTEM_NAME_PLACEHOLDER = "system_name"
SYSTEM_PREFIX = "system_"


class LayoutConfig:
    def __init__(self, system_map: dict = None, values: dict = None) -> None:
        if system_map is None:
            self.system_map = dict()
        else:
            self.system_map = system_map

        if values is None:
            values = dict()

        for key, default in CONFIG_ITEMS.items():
            if key in values:
                setattr(self, key, values[key])
            else:
                setattr(self, key, default)

    def copy(self) -> "LayoutConfig":
        value_dict = {k: getattr(self, k) for k in CONFIG_ITEMS.keys()}
        return LayoutConfig(self.system_map, value_dict)

    def get_values(self) -> List[Tuple[str, Any]]:
        results = []
        for key in CONFIG_ITEMS.keys():
            if not key.startswith(SYSTEM_PREFIX):
                results.append((key, getattr(self, key)))

        return results
