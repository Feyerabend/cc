# src/font_loader.py
from typing import List, Dict
import json
import os

class HersheyJSONFont:
    _instance = None

    def __new__(cls, json_path: str):
        if cls._instance is None:
            cls._instance = super(HersheyJSONFont, cls).__new__(cls)
            cls._instance._initialize(json_path)
        return cls._instance

    def _initialize(self, json_path: str):
        self.characters = {}
        self.metadata = {}
        self.char_metrics = {}
        self.load_font(json_path)

    def load_font(self, json_path: str):
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            self.metadata = data.get("metadata", {})
            char_data = data.get("characters", {})
            for char, info in char_data.items():
                strokes = info.get("strokes", [])
                # Use width, left_bound, and right_bound from JSON if available
                width = info.get("width", None)
                left_bound = info.get("left_bound", None)
                right_bound = info.get("right_bound", None)
                self.characters[char] = strokes
                self.char_metrics[char] = self._calculate_char_metrics(strokes, width, left_bound, right_bound)
            print(f"✓ Loaded {len(self.characters)} characters from {os.path.basename(json_path)}")
            if self.metadata.get("source_file"):
                print(f"  Source: {self.metadata['source_file']}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Font file not found: {json_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading font: {e}")

    def _calculate_char_metrics(self, strokes: List[List[List[int]]], width: float = None, 
                              left_bound: float = None, right_bound: float = None) -> Dict:
        if not strokes:
            return {"width": 0, "height": 0, "bounds": [0, 0, 0, 0], "advance_width": 8, 
                    "left_bound": 0, "right_bound": 8}
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        for stroke in strokes:
            for point in stroke:
                x, y = point[0], point[1]
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
        if min_x == float('inf'):
            return {"width": 0, "height": 0, "bounds": [0, 0, 0, 0], "advance_width": 8, 
                    "left_bound": 0, "right_bound": 8}
        bounding_width = max_x - min_x
        bounding_height = max_y - min_y
        # Use JSON-provided bounds and width if available, otherwise calculate
        final_left_bound = left_bound if left_bound is not None else min_x
        final_right_bound = right_bound if right_bound is not None else max_x
        final_width = width if width is not None else (final_right_bound - final_left_bound)
        advance_width = final_width if final_width > 0 else max(max_x + 2, bounding_width + 1, 4)
        return {
            "width": final_width,
            "height": bounding_height,
            "bounds": [min_x, min_y, max_x, max_y],
            "advance_width": advance_width,
            "left_bound": final_left_bound,
            "right_bound": final_right_bound
        }

    def get_text_metrics(self, text: str, char_spacing: float = 1.6, scale: float = 1.0) -> Dict:
        if not text:
            return {"width": 0, "height": 0}
        lines = text.split('\n')
        max_width = 0
        total_height = 0
        for line_idx, line in enumerate(lines):
            line_width = 0
            line_height = 0
            for char in line:
                if char == ' ':
                    char_width = self._get_average_char_width()
                else:
                    char_metrics = self.char_metrics.get(char)
                    if char_metrics:
                        char_width = char_metrics["advance_width"]
                        line_height = max(line_height, char_metrics["height"])
                    else:
                        char_width = self._get_average_char_width()
                        line_height = max(line_height, 20)
                line_width += char_width * char_spacing
            max_width = max(max_width, line_width)
            total_height += line_height
            if line_idx < len(lines) - 1:
                total_height += line_height * 0.8
        return {
            "width": max_width * scale,
            "height": total_height * scale
        }

    def _get_average_char_width(self) -> float:
        if not self.char_metrics:
            return 12.0
        widths = [metrics["advance_width"] for metrics in self.char_metrics.values() 
                  if metrics["advance_width"] > 0]
        return sum(widths) / len(widths) if widths else 12.0

    def list_characters(self) -> List[str]:
        return sorted(self.characters.keys())


# src/rendering/screen_renderer.py
from PIL import Image, ImageDraw
from typing import Union, List, Tuple, Optional, Dict, Any
import logging
from src.config_loader import HersheyConfig
from src.font_loader import HersheyJSONFont
from src.font_hints_loader import FontHintsLoader
from src.rendering.kerning_manager import KerningManager

class ScreenRenderer:
    def __init__(self, font, config=None, hints=None, font_style: str = "default"):
        self.font = font
        self.config = config or {}
        self.hints = hints or MockHints()
        self.font_style = font_style
        self.logger = logging.getLogger(__name__)
        self._init_rendering_params()
        self.avg_char_width = self._calculate_average_char_width()
        self.avg_char_height = self._calculate_average_char_height()
        self.kerning = KerningManager(self.config, self.hints, self.font_style)
        self.logger.info(f"ScreenRenderer initialized: avg_width={self.avg_char_width:.1f}, avg_height={self.avg_char_height:.1f}")

    def _init_rendering_params(self):
        base_scale = self._get_config("rendering", "scale", 2.5)
        scale_adjustment = self.hints.get_hint(self.font_style, "scale_adjustment", 1.0)
        self.default_scale = base_scale * scale_adjustment
        self.default_char_spacing = self._get_config("rendering", "char_spacing", 1.6)
        self.default_line_spacing = self._get_config("rendering", "line_spacing", 1.8)
        self.word_spacing_multiplier = self._get_config("rendering", "word_spacing_multiplier", 1.8)
        self.min_char_spacing = self._get_config("spacing_bounds", "min_char_spacing", 0.5)
        self.max_char_spacing = self._get_config("spacing_bounds", "max_char_spacing", 4.0)
        self.default_line_width = self._get_config("rendering", "line_width", 2)
        self.default_antialias = self._get_config("rendering", "antialias", True)
        self.default_margin = self._get_config("layout", "margin", 20)
        self.default_align = self._get_config("layout", "align", "center")
        self.default_valign = self._get_config("layout", "valign", "middle")
        self.default_bg_color = self._get_config("colors", "background", "white")
        self.default_fg_color = self._get_config("colors", "foreground", "black")

    def _get_config(self, section: str, key: str, default: Any) -> Any:
        try:
            if hasattr(self.config, 'get'):
                return self.config.get(section, key, default)
            elif isinstance(self.config, dict):
                return self.config.get(section, {}).get(key, default)
            else:
                return default
        except Exception:
            return default

    def _calculate_average_char_width(self) -> float:
        try:
            if hasattr(self.font, 'char_metrics') and self.font.char_metrics:
                widths = []
                for char, metrics in self.font.char_metrics.items():
                    if isinstance(metrics, dict) and "advance_width" in metrics:
                        width = metrics["advance_width"]
                        if width > 0:
                            widths.append(width)
                if widths:
                    return sum(widths) / len(widths)
            return 12.0
        except Exception as e:
            self.logger.warning(f"Error calculating average char width: {e}")
            return 12.0

    def _calculate_average_char_height(self) -> float:
        try:
            if hasattr(self.font, 'char_metrics') and self.font.char_metrics:
                heights = []
                for char, metrics in self.font.char_metrics.items():
                    if isinstance(metrics, dict) and "height" in metrics:
                        height = metrics["height"]
                        if height > 0:
                            heights.append(height)
                if heights:
                    return sum(heights) / len(heights)
            return 20.0
        except Exception as e:
            self.logger.warning(f"Error calculating average char height: {e}")
            return 20.0

    def _calculate_glyph_width(self, strokes: List[List[List[float]]]) -> float:
        try:
            if not strokes:
                return 0
            min_x = float('inf')
            max_x = float('-inf')
            for stroke in strokes:
                for point in stroke:
                    if len(point) >= 2:
                        x = point[0]
                        min_x = min(min_x, x)
                        max_x = max(max_x, x)
            if min_x != float('inf') and max_x != float('-inf'):
                return max_x - min_x
            return 0
        except Exception:
            return 0

    def _calculate_glyph_height(self, strokes: List[List[List[float]]]) -> float:
        try:
            if not strokes:
                return 0
            min_y = float('inf')
            max_y = float('-inf')
            for stroke in strokes:
                for point in stroke:
                    if len(point) >= 2:
                        y = point[1]
                        min_y = min(min_y, y)
                        max_y = max(max_y, y)
            if min_y != float('inf') and max_y != float('-inf'):
                return max_y - min_y
            return 0
        except Exception:
            return 0

    def draw_character(self, draw: ImageDraw.Draw, char: str, x: float, y: float,
                      color: Union[str, Tuple[int, int, int]], scale: float, line_width: int) -> float:
        try:
            if not hasattr(self.font, 'characters') or char not in self.font.characters:
                self.logger.debug(f"Character '{char}' not found in font")
                return self.avg_char_width * scale
            strokes = self.font.characters[char]
            x_offset = self.hints.get_hint(self.font_style, "x_offset", 0)
            y_offset = self.hints.get_hint(self.font_style, "y_offset", 0)
            line_width_modifier = self.hints.get_hint(self.font_style, "line_width_modifier", 1.0)
            adjusted_line_width = max(1, int(line_width * line_width_modifier))
            advance_width = self._get_char_advance_width(char)
            # Get bounds for positioning
            char_metrics = self.font.char_metrics.get(char, {})
            left_bound = char_metrics.get("left_bound", 0)
            # Adjust x position based on left bound
            adjusted_x = x + (left_bound * scale)
            for stroke in strokes:
                if not stroke or len(stroke) < 1:
                    continue
                points = []
                for px, py in stroke:
                    try:
                        screen_x = float(adjusted_x + px * scale + x_offset)
                        screen_y = float(y + py * scale + y_offset)
                        points.append((screen_x, screen_y))
                    except (TypeError, ValueError) as e:
                        self.logger.debug(f"Invalid point data in stroke: {px}, {py}")
                        continue
                if len(points) == 1:
                    px, py = points[0]
                    radius = max(1, adjusted_line_width // 2)
                    draw.ellipse([px-radius, py-radius, px+radius, py+radius], fill=color)
                elif len(points) >= 2:
                    for i in range(len(points) - 1):
                        try:
                            draw.line([points[i], points[i + 1]], fill=color, width=adjusted_line_width)
                        except Exception as e:
                            self.logger.debug(f"Error drawing line segment: {e}")
                            continue
            return advance_width * scale
        except Exception as e:
            self.logger.error(f"Error drawing character '{char}': {e}")
            return self.avg_char_width * scale

    def _get_char_advance_width(self, char: str) -> float:
        try:
            if hasattr(self.font, 'char_metrics') and self.font.char_metrics:
                if char in self.font.char_metrics:
                    metrics = self.font.char_metrics[char]
                    if isinstance(metrics, dict) and "advance_width" in metrics:
                        return metrics["advance_width"]
            return self.avg_char_width
        except Exception:
            return self.avg_char_width

    def render_text(self, text: str, width: int = 800, height: int = 200, **kwargs) -> Image.Image:
        scale = kwargs.get('scale', self.default_scale)
        char_spacing = kwargs.get('char_spacing', self.default_char_spacing)
        line_spacing = kwargs.get('line_spacing', self.default_line_spacing)
        word_spacing = kwargs.get('word_spacing', char_spacing * self.word_spacing_multiplier)
        min_char_spacing = kwargs.get('min_char_spacing', self.min_char_spacing)
        max_char_spacing = kwargs.get('max_char_spacing', self.max_char_spacing)
        use_kerning = kwargs.get('use_kerning', True)
        align = kwargs.get('align', self.default_align)
        valign = kwargs.get('valign', self.default_valign)
        margin = kwargs.get('margin', self.default_margin)
        bg_color = kwargs.get('bg_color', self.default_bg_color)
        fg_color = kwargs.get('fg_color', self.default_fg_color)
        line_width = kwargs.get('line_width', self.default_line_width)
        antialias = kwargs.get('antialias', self.default_antialias)
        scale = max(0.1, scale)
        char_spacing = max(min_char_spacing, min(char_spacing, max_char_spacing))
        line_spacing = max(0.5, line_spacing)
        word_spacing = max(0.5, word_spacing)
        line_width = max(1, line_width)
        margin = max(0, margin)
        try:
            return self._render_text_internal(
                text, width, height, scale, char_spacing, line_spacing, word_spacing,
                use_kerning, align, valign, margin, bg_color, fg_color, line_width, antialias
            )
        except Exception as e:
            self.logger.error(f"Error rendering text: {e}")
            img = Image.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(img)
            draw.text((10, 10), f"Render Error: {str(e)[:50]}", fill='red')
            return img

    def _render_text_internal(self, text: str, width: int, height: int, scale: float,
                             char_spacing: float, line_spacing: float, word_spacing: float,
                             use_kerning: bool, align: str, valign: str, margin: int,
                             bg_color, fg_color, line_width: int, antialias: bool) -> Image.Image:
        if antialias:
            aa_scale = 2
            aa_width, aa_height = width * aa_scale, height * aa_scale
            draw_scale = scale * aa_scale
            draw_line_width = line_width * aa_scale
            draw_margin = margin * aa_scale
        else:
            aa_width, aa_height = width, height
            draw_scale = scale
            draw_line_width = line_width
            draw_margin = margin
        mode = 'RGBA' if antialias else 'RGB'
        img = Image.new(mode, (aa_width, aa_height), bg_color)
        draw = ImageDraw.Draw(img)
        lines = text.split('\n')
        if not lines:
            return img.resize((width, height), Image.LANCZOS) if antialias else img
        line_heights = []
        line_widths = []
        scaled_line_height = self.avg_char_height * draw_scale
        for line in lines:
            line_width_px = self._calculate_line_width(line, draw_scale, char_spacing, word_spacing, use_kerning)
            line_heights.append(scaled_line_height)
            line_widths.append(line_width_px)
        total_text_height = len(lines) * scaled_line_height + (len(lines) - 1) * scaled_line_height * (line_spacing - 1)
        max_line_width = max(line_widths) if line_widths else 0
        if valign == 'top':
            start_y = draw_margin
        elif valign == 'bottom':
            start_y = aa_height - total_text_height - draw_margin
        else:
            start_y = (aa_height - total_text_height) // 2
        current_y = start_y
        for i, line in enumerate(lines):
            if not line:
                current_y += line_heights[i] if i < len(line_heights) else scaled_line_height
                continue
            line_width_px = line_widths[i] if i < len(line_widths) else 0
            if align == 'left':
                start_x = draw_margin
            elif align == 'right':
                start_x = aa_width - line_width_px - draw_margin
            else:
                start_x = (aa_width - line_width_px) // 2
            self._render_line(draw, line, start_x, current_y, fg_color, draw_scale, 
                            draw_line_width, char_spacing, word_spacing, use_kerning)
            if i < len(lines) - 1:
                current_y += scaled_line_height * line_spacing
            else:
                current_y += scaled_line_height
        if antialias:
            img = img.resize((width, height), Image.LANCZOS)
        return img

    def _calculate_line_width(self, line: str, scale: float, char_spacing: float, 
                            word_spacing: float, use_kerning: bool) -> float:
        if not line:
            return 0
        total_width = 0
        prev_char = None
        for char in line:
            if char == ' ':
                total_width += self._get_char_advance_width(' ') * scale * word_spacing
            else:
                if use_kerning and prev_char and prev_char != ' ':
                    kerning_adj = self.kerning.get_kerning_adjustment(prev_char, char)
                    total_width += kerning_adj * self.avg_char_width * scale
                advance_width = self._get_char_advance_width(char)
                total_width += advance_width * scale * char_spacing
            prev_char = char
        return total_width

    def _render_line(self, draw: ImageDraw.Draw, line: str, start_x: float, y: float,
                    color, scale: float, line_width: int, char_spacing: float, 
                    word_spacing: float, use_kerning: bool):
        current_x = start_x
        prev_char = None
        for char in line:
            if char == ' ':
                current_x += self._get_char_advance_width(' ') * scale * word_spacing
            else:
                if use_kerning and prev_char and prev_char != ' ':
                    kerning_adj = self.kerning.get_kerning_adjustment(prev_char, char)
                    current_x += kerning_adj * self.avg_char_width * scale
                char_advance = self.draw_character(draw, char, current_x, y, color, scale, line_width)
                current_x += char_advance * char_spacing
            prev_char = char

    def get_kerning_adjustment(self, char1: str, char2: str) -> float:
        return self.kerning.get_kerning_adjustment(char1, char2)


class MockHints:
    def get_hint(self, font_style: str, hint_name: str, default):
        return default