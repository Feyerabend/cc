# src/config_loader.py
# Integrating custom YAML parser for configuration loading
from typing import Optional, Dict
import os
from src.utils.yaml_parser import SimpleYAMLParser

class HersheyConfig:
    def __init__(self, config_path: Optional[str] = None):
        self.config = {
            "rendering": {
                "scale": 2.5,
                "char_spacing": 1.6,
                "line_spacing": 1.8,
                "word_spacing_multiplier": 1.8,
                "line_width": 2,
                "antialias": True
            },
            "spacing_bounds": {
                "min_char_spacing": 0.8,
                "max_char_spacing": 4.0
            },
            "layout": {
                "align": "center",
                "valign": "middle",
                "margin": 20
            },
            "colors": {
                "background": "white",
                "foreground": "black"
            },
            "kerning": {
                "enabled": True,
                "strength": 0.7
            }
        }
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)

    def load_config(self, config_path: str):
        try:
            with open(config_path, 'r') as f:
                yaml_text = f.read()
            user_config = SimpleYAMLParser.parse(yaml_text)
            self._deep_merge(self.config, user_config.get('hershey_config', {}))
            print(f"✓ Loaded configuration from {config_path}")
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
            print("Using default configuration")

    def _deep_merge(self, base_dict: dict, update_dict: dict):
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value

    def get(self, section: str, key: str, default=None):
        return self.config.get(section, {}).get(key, default)

    def save_default_config(self, path: str = "hershey_config.yaml"):
        with open(path, 'w') as f:
            f.write(SimpleYAMLParser.dump({'hershey_config': self.config}))
        print(f"✓ Default configuration saved to {path}")
