# src/rendering/kerning_manager.py
# Integrating font hints into kerning adjustments
from src.config_loader import HersheyConfig
from src.font_hints_loader import FontHintsLoader

class KerningManager:
    def __init__(self, config: HersheyConfig, hints: FontHintsLoader, font_style: str = "default"):
        self.config = config
        self.hints = hints
        self.font_style = font_style
        self.kerning_strength = self.config.get("kerning", "strength", 0.7) * self.hints.get_hint(font_style, "kerning_strength", 1.0)
        base_kerning_pairs = {
            ('A', 'V'): -0.3, ('A', 'W'): -0.3, ('A', 'Y'): -0.4,
            ('V', 'A'): -0.3, ('W', 'A'): -0.3, ('Y', 'A'): -0.4,
            ('T', 'o'): -0.2, ('T', 'a'): -0.2, ('T', 'e'): -0.2,
            ('P', 'A'): -0.3, ('F', 'A'): -0.3, ('L', 'T'): -0.2,
            ('L', 'V'): -0.3, ('L', 'W'): -0.3, ('L', 'Y'): -0.4,
            ('.', ' '): 0.1, (',', ' '): 0.1,
            ('r', 'n'): -0.1, ('r', 'm'): -0.1, ('f', 'i'): -0.2,
            ('m', 'a'): 0.1, ('m', 'e'): 0.1, ('m', 'i'): 0.1,
            ('a', 'm'): 0.1, ('e', 'm'): 0.1, ('S', 'm'): 0.2,
        }
        self.kerning_pairs = {
            pair: adjustment * self.kerning_strength 
            for pair, adjustment in base_kerning_pairs.items()
        }

    def add_kerning_pair(self, char1: str, char2: str, adjustment: float):
        self.kerning_pairs[(char1, char2)] = adjustment * self.kerning_strength

    def get_kerning_adjustment(self, char1: str, char2: str) -> float:
        return self.kerning_pairs.get((char1, char2), 0.0)