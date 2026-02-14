# src/rendering/screen_renderer.py
# Fixed and improved screen renderer with better error handling and font integration
# replaced with rendering to PIL images instead of SVG for better compatibility and performance
from PIL import Image, ImageDraw
from typing import Union, List, Tuple, Optional, Dict, Any
import logging

# Assuming these are your existing modules
from src.config_loader import HersheyConfig
from src.font_loader import HersheyJSONFont
from src.font_hints_loader import FontHintsLoader
from src.rendering.kerning_manager import KerningManager

class ScreenRenderer:
    def __init__(self, font, config=None, hints=None, font_style: str = "default"):
        """
        Initialize the screen renderer with better defaults and error handling
        
        Args:
            font: HersheyJSONFont or compatible font object
            config: HersheyConfig or dict-like configuration object
            hints: FontHintsLoader or compatible hints object
            font_style: Font style identifier
        """
        self.font = font
        self.config = config or {}
        self.hints = hints or MockHints()
        self.font_style = font_style
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize rendering parameters with safe defaults
        self._init_rendering_params()
        
        # Initialize kerning manager
        self.kerning = KerningManager(self.config, self.hints, self.font_style)
        
        # Calculate font metrics
        self.avg_char_width = self._calculate_average_char_width()
        self.avg_char_height = self._calculate_average_char_height()
        
        self.logger.info(f"ScreenRenderer initialized: avg_width={self.avg_char_width:.1f}, avg_height={self.avg_char_height:.1f}")

    def _init_rendering_params(self):
        """Initialize rendering parameters with safe defaults"""
        # Get configuration values safely
        base_scale = self._get_config("rendering", "scale", 2.5)
        scale_adjustment = self.hints.get_hint(self.font_style, "scale_adjustment", 1.0)
        
        self.default_scale = base_scale * scale_adjustment
        self.default_char_spacing = self._get_config("rendering", "char_spacing", 1.6)
        self.default_line_spacing = self._get_config("rendering", "line_spacing", 1.8)
        self.word_spacing_multiplier = self._get_config("rendering", "word_spacing_multiplier", 1.8)
        
        # Bounds checking
        self.min_char_spacing = self._get_config("spacing_bounds", "min_char_spacing", 0.5)
        self.max_char_spacing = self._get_config("spacing_bounds", "max_char_spacing", 4.0)
        
        # Rendering options
        self.default_line_width = self._get_config("rendering", "line_width", 2)
        self.default_antialias = self._get_config("rendering", "antialias", True)
        
        # Layout
        self.default_margin = self._get_config("layout", "margin", 20)
        self.default_align = self._get_config("layout", "align", "center")
        self.default_valign = self._get_config("layout", "valign", "middle")
        
        # Colors
        self.default_bg_color = self._get_config("colors", "background", "white")
        self.default_fg_color = self._get_config("colors", "foreground", "black")

    def _get_config(self, section: str, key: str, default: Any) -> Any:
        """Safely get configuration values"""
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
        """Calculate average character width with fallback"""
        try:
            # Try to get from font metrics
            if hasattr(self.font, 'char_metrics') and self.font.char_metrics:
                widths = []
                for char, metrics in self.font.char_metrics.items():
                    if isinstance(metrics, dict) and "advance_width" in metrics:
                        width = metrics["advance_width"]
                        if width > 0:
                            widths.append(width)
                
                if widths:
                    return sum(widths) / len(widths)
            
            # Fallback: calculate from actual glyph data
            if hasattr(self.font, 'characters') and self.font.characters:
                widths = []
                for char, strokes in self.font.characters.items():
                    if char.isalnum():  # Focus on alphanumeric characters
                        width = self._calculate_glyph_width(strokes)
                        if width > 0:
                            widths.append(width)
                
                if widths:
                    return sum(widths) / len(widths)
            
            # Ultimate fallback
            return 12.0
            
        except Exception as e:
            self.logger.warning(f"Error calculating average char width: {e}")
            return 12.0

    def _calculate_average_char_height(self) -> float:
        """Calculate average character height with fallback"""
        try:
            # Try to get from font metrics
            if hasattr(self.font, 'char_metrics') and self.font.char_metrics:
                heights = []
                for char, metrics in self.font.char_metrics.items():
                    if isinstance(metrics, dict) and "height" in metrics:
                        height = metrics["height"]
                        if height > 0:
                            heights.append(height)
                
                if heights:
                    return sum(heights) / len(heights)
            
            # Fallback: calculate from actual glyph data
            if hasattr(self.font, 'characters') and self.font.characters:
                heights = []
                for char, strokes in self.font.characters.items():
                    if char.isalnum():  # Focus on alphanumeric characters
                        height = self._calculate_glyph_height(strokes)
                        if height > 0:
                            heights.append(height)
                
                if heights:
                    return sum(heights) / len(heights)
            
            # Ultimate fallback
            return 20.0
            
        except Exception as e:
            self.logger.warning(f"Error calculating average char height: {e}")
            return 20.0

    def _calculate_glyph_width(self, strokes: List[List[List[float]]]) -> float:
        """Calculate the width of a glyph from its stroke data"""
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
        """Calculate the height of a glyph from its stroke data"""
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
        """Draw a single character with improved error handling"""
        try:
            # Get character strokes
            if not hasattr(self.font, 'characters') or char not in self.font.characters:
                self.logger.debug(f"Character '{char}' not found in font")
                return self.avg_char_width * scale
            
            strokes = self.font.characters[char]
            
            # Get font hints
            x_offset = self.hints.get_hint(self.font_style, "x_offset", 0)
            y_offset = self.hints.get_hint(self.font_style, "y_offset", 0)
            line_width_modifier = self.hints.get_hint(self.font_style, "line_width_modifier", 1.0)
            
            adjusted_line_width = max(1, int(line_width * line_width_modifier))
            
            # Get advance width
            advance_width = self._get_char_advance_width(char)
            
            # Draw strokes
            for stroke in strokes:
                if not stroke or len(stroke) < 1:
                    continue
                
                points = []
                for px, py in stroke:
                    try:
                        screen_x = float(x + px * scale + x_offset)
                        screen_y = float(y + py * scale + y_offset)
                        points.append((screen_x, screen_y))
                    except (TypeError, ValueError) as e:
                        self.logger.debug(f"Invalid point data in stroke: {px}, {py}")
                        continue
                
                # Draw the stroke
                if len(points) == 1:
                    # Single point - draw as circle
                    px, py = points[0]
                    radius = max(1, adjusted_line_width // 2)
                    draw.ellipse([px-radius, py-radius, px+radius, py+radius], fill=color)
                elif len(points) >= 2:
                    # Multiple points - draw as connected lines
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
        """Get the advance width for a character"""
        try:
            if hasattr(self.font, 'char_metrics') and self.font.char_metrics:
                if char in self.font.char_metrics:
                    metrics = self.font.char_metrics[char]
                    if isinstance(metrics, dict) and "advance_width" in metrics:
                        return metrics["advance_width"]
            
            # Fallback: calculate from glyph data
            if hasattr(self.font, 'characters') and char in self.font.characters:
                width = self._calculate_glyph_width(self.font.characters[char])
                if width > 0:
                    return width
            
            return self.avg_char_width
            
        except Exception:
            return self.avg_char_width

    def render_text(self, text: str, width: int = 800, height: int = 200, **kwargs) -> Image.Image:
        """
        Render text with comprehensive parameter handling
        
        Args:
            text: Text to render
            width: Image width
            height: Image height
            **kwargs: Additional rendering parameters
        """
        # Extract parameters with defaults
        scale = kwargs.get('scale', self.default_scale)
        char_spacing = kwargs.get('char_spacing', self.default_char_spacing)
        line_spacing = kwargs.get('line_spacing', self.default_line_spacing)
        word_spacing = kwargs.get('word_spacing', char_spacing * self.word_spacing_multiplier)
        
        # Bounds and features
        min_char_spacing = kwargs.get('min_char_spacing', self.min_char_spacing)
        max_char_spacing = kwargs.get('max_char_spacing', self.max_char_spacing)
        use_kerning = kwargs.get('use_kerning', True)
        
        # Layout
        align = kwargs.get('align', self.default_align)
        valign = kwargs.get('valign', self.default_valign)
        margin = kwargs.get('margin', self.default_margin)
        
        # Appearance
        bg_color = kwargs.get('bg_color', self.default_bg_color)
        fg_color = kwargs.get('fg_color', self.default_fg_color)
        line_width = kwargs.get('line_width', self.default_line_width)
        antialias = kwargs.get('antialias', self.default_antialias)
        
        # Validate and constrain parameters
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
            # Return a simple error image
            img = Image.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(img)
            draw.text((10, 10), f"Render Error: {str(e)[:50]}", fill='red')
            return img

    def _render_text_internal(self, text: str, width: int, height: int, scale: float,
                             char_spacing: float, line_spacing: float, word_spacing: float,
                             use_kerning: bool, align: str, valign: str, margin: int,
                             bg_color, fg_color, line_width: int, antialias: bool) -> Image.Image:
        """Internal text rendering implementation"""
        
        # Set up antialiasing
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
        
        # Create image
        mode = 'RGBA' if antialias else 'RGB'
        img = Image.new(mode, (aa_width, aa_height), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Process text into lines
        lines = text.split('\n')
        if not lines:
            return img.resize((width, height), Image.LANCZOS) if antialias else img
        
        # Calculate layout
        line_heights = []
        line_widths = []
        
        # Use actual character height
        scaled_line_height = self.avg_char_height * draw_scale
        
        for line in lines:
            line_width_px = self._calculate_line_width(line, draw_scale, char_spacing, word_spacing, use_kerning)
            line_heights.append(scaled_line_height)
            line_widths.append(line_width_px)
        
        # Calculate total dimensions
        total_text_height = len(lines) * scaled_line_height + (len(lines) - 1) * scaled_line_height * (line_spacing - 1)
        max_line_width = max(line_widths) if line_widths else 0
        
        # Vertical positioning
        if valign == 'top':
            start_y = draw_margin
        elif valign == 'bottom':
            start_y = aa_height - total_text_height - draw_margin
        else:  # middle
            start_y = (aa_height - total_text_height) // 2
        
        # Render each line
        current_y = start_y
        for i, line in enumerate(lines):
            if not line:
                current_y += line_heights[i] if i < len(line_heights) else scaled_line_height
                continue
            
            line_width_px = line_widths[i] if i < len(line_widths) else 0
            
            # Horizontal positioning
            if align == 'left':
                start_x = draw_margin
            elif align == 'right':
                start_x = aa_width - line_width_px - draw_margin
            else:  # center
                start_x = (aa_width - line_width_px) // 2
            
            self._render_line(draw, line, start_x, current_y, fg_color, draw_scale, 
                            draw_line_width, char_spacing, word_spacing, use_kerning)
            
            # Move to next line
            if i < len(lines) - 1:
                current_y += scaled_line_height * line_spacing
            else:
                current_y += scaled_line_height
        
        # Apply antialiasing
        if antialias:
            img = img.resize((width, height), Image.LANCZOS)
        
        return img

    def _calculate_line_width(self, line: str, scale: float, char_spacing: float, 
                            word_spacing: float, use_kerning: bool) -> float:
        """Calculate the total width of a line of text"""
        if not line:
            return 0
        
        total_width = 0
        prev_char = None
        
        for char in line:
            if char == ' ':
                total_width += self._get_char_advance_width(' ') * scale * word_spacing
            else:
                # Apply kerning if enabled
                if use_kerning and prev_char and prev_char != ' ':
                    kerning_adj = self.get_kerning_adjustment(prev_char, char)
                    total_width += kerning_adj * self.avg_char_width * scale
                
                # Add character width
                advance_width = self._get_char_advance_width(char)
                total_width += advance_width * scale * char_spacing
            
            prev_char = char
        
        return total_width

    def _render_line(self, draw: ImageDraw.Draw, line: str, start_x: float, y: float,
                    color, scale: float, line_width: int, char_spacing: float, 
                    word_spacing: float, use_kerning: bool):
        """Render a single line of text"""
        current_x = start_x
        prev_char = None
        
        for char in line:
            if char == ' ':
                current_x += self._get_char_advance_width(' ') * scale * word_spacing
            else:
                # Apply kerning if enabled
                if use_kerning and prev_char and prev_char != ' ':
                    kerning_adj = self.get_kerning_adjustment(prev_char, char)
                    current_x += kerning_adj * self.avg_char_width * scale
                
                # Draw the character
                char_advance = self.draw_character(draw, char, current_x, y, color, scale, line_width)
                current_x += char_advance * char_spacing
            
            prev_char = char

    def get_kerning_adjustment(self, char1: str, char2: str) -> float:
        """Get kerning adjustment between two characters"""
        return self.kerning.get_kerning_adjustment(char1, char2)


class MockHints:
    """Mock hints class for when hints are not available"""
    
    def get_hint(self, font_style: str, hint_name: str, default):
        """Return default value for any hint request"""
        return default