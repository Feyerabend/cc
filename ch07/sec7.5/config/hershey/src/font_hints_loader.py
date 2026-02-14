# src/font_hints_loader.py
# custom YAML parser for font hints loading
from typing import Optional, Dict
import os
from src.utils.yaml_parser import SimpleYAMLParser

class FontHintsLoader:
    def __init__(self, hints_path: Optional[str] = None):
        self.hints = {
            "default": {
                "scale_adjustment": 1.0,
                "x_offset": 0,
                "y_offset": 0,
                "kerning_strength": 0.7,
                "line_width_modifier": 1.0
            },
            "roman": {
                "scale_adjustment": 1.1,
                "x_offset": 1,
                "y_offset": -1,
                "kerning_strength": 0.8,
                "line_width_modifier": 1.2
            },
            "gothic": {
                "scale_adjustment": 0.9,
                "x_offset": 0,
                "y_offset": 0,
                "kerning_strength": 0.6,
                "line_width_modifier": 0.9
            }
        }
        if hints_path and os.path.exists(hints_path):
            self.load_hints(hints_path)

    def load_hints(self, hints_path: str):
        try:
            with open(hints_path, 'r') as f:
                yaml_text = f.read()
            user_hints = SimpleYAMLParser.parse(yaml_text)
            self._deep_merge(self.hints, user_hints.get('font_hints', {}))
            print(f"✓ Loaded font hints from {hints_path}")
        except Exception as e:
            print(f"Warning: Could not load hints from {hints_path}: {e}")
            print("Using default font hints")

    def _deep_merge(self, base_dict: dict, update_dict: dict):
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value

    def get_hint(self, font_style: str, key: str, default=None):
        return self.hints.get(font_style, self.hints.get('default', {})).get(key, default)

    def save_default_hints(self, path: str = "font_hints.yaml"):
        with open(path, 'w') as f:
            f.write(SimpleYAMLParser.dump({'font_hints': self.hints}))
        print(f"✓ Default font hints saved to {path}")
