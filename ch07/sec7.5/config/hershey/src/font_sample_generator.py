# src/font_sample_generator.py
# generate font samples
from PIL import Image
from .font_loader import HersheyJSONFont
from .rendering.screen_renderer import ScreenRenderer

class FontSampleGenerator:
    def __init__(self, font: HersheyJSONFont, renderer: ScreenRenderer):
        self.font = font
        self.renderer = renderer

    def create_font_sample(self, output_path: str = "font_sample.png", width: int = 1600, height: int = 1200) -> str:
        chars = self.font.list_characters()
        lines = []
        alpha_upper = ''.join([c for c in chars if c.isupper() and c.isalpha()])
        alpha_lower = ''.join([c for c in chars if c.islower() and c.isalpha()])
        digits = ''.join([c for c in chars if c.isdigit()])
        basic_punct = ''.join([c for c in chars if c in '.,;:!?'])
        math_symbols = ''.join([c for c in chars if c in '+-=*/()[]{}'])
        other_symbols = ''.join([c for c in chars if not c.isalnum() and c != ' ' and c not in '.,;:!?+-=*/()[]{}'])
        
        if alpha_upper:
            lines.append(f"UPPERCASE: {alpha_upper}")
        if alpha_lower:
            lines.append(f"lowercase: {alpha_lower}")
        if digits:
            lines.append(f"Numbers: {digits}")
        if basic_punct:
            lines.append(f"Punctuation: {basic_punct}")
        if math_symbols:
            lines.append(f"Math & Brackets: {math_symbols}")
        if other_symbols:
            lines.append(f"Other Symbols: {other_symbols}")
        
        sample_sentences = [
            "",  # Empty line for spacing
            "The quick brown fox jumps over the lazy dog",
            "NOW IS THE TIME FOR ALL GOOD MEN ..", # .. to come to the aid of their party.
            "Vector fonts scale beautifully?",
            "Testing 123.. Math: 2+2=4, (3*5)=15"
        ]
        
        for sentence in sample_sentences:
            if not sentence or all(c in chars or c == ' ' for c in sentence):
                lines.append(sentence)
        
        sample_text = '\n'.join(lines)
        text_metrics = self.font.get_text_metrics(sample_text, self.renderer.default_char_spacing, 1.0)
        margin = 40
        available_width = width - (2 * margin)
        available_height = height - (2 * margin)
        
        if text_metrics["width"] > 0 and text_metrics["height"] > 0:
            scale_x = available_width / text_metrics["width"]
            scale_y = available_height / text_metrics["height"]
            optimal_scale = min(scale_x, scale_y) * 0.9
            sample_scale = max(0.5, min(optimal_scale, 4.0))
        else:
            sample_scale = 1.5
        
        print(f"Sample text metrics: {text_metrics['width']:.1f} x {text_metrics['height']:.1f}")
        print(f"Using sample scale: {sample_scale:.2f}")
        
        img = self.renderer.render_text(
            sample_text, width=width, height=height, scale=sample_scale,
            char_spacing=self.renderer.default_char_spacing,
            line_spacing=self.renderer.default_line_spacing,
            align='left', valign='top', antialias=True
        )
        
        img.save(output_path)
        print(f"  Font sample saved to: {output_path}")
#        print(f"  Characters shown: {len([c for c in sample_text if c != ' ' and c != '\n'])}")
        print(f"  Total available: {len(chars)}")
        return output_path
