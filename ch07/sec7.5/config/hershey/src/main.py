# src/main.py
# Integrating font hints and custom YAML parser into the main entry point
#!/usr/bin/env python3
import argparse
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config_loader import HersheyConfig
from src.font_loader import HersheyJSONFont
from src.font_hints_loader import FontHintsLoader
from src.rendering.screen_renderer import ScreenRenderer
from src.font_sample_generator import FontSampleGenerator

def main():
    parser = argparse.ArgumentParser(description='Fast Hershey JSON Font Renderer with Improved Defaults')
    parser.add_argument('font_json', help='Path to Hershey JSON font file')
    parser.add_argument('--config', '-c', help='Path to configuration YAML file')
    parser.add_argument('--hints', help='Path to font hints YAML file')
    parser.add_argument('--font-style', default='default', help='Font style for hints (e.g., default, roman, gothic)')
    parser.add_argument('--text', '-t', default='HELLO WORLD\nHershey Fonts!', help='Text to render (use \\n for line breaks)')
    parser.add_argument('--output', '-o', default='rendered.png', help='Output image file')
    parser.add_argument('--width', '-w', type=int, default=800, help='Image width')
    parser.add_argument('--height', type=int, default=400, help='Image height')
    parser.add_argument('--scale', '-s', type=float, help='Font scale factor (default from config: 2.5)')
    parser.add_argument('--char-spacing', type=float, help='Character spacing multiplier (default from config: 1.6)')
    parser.add_argument('--word-spacing', type=float, help='Word spacing multiplier (default: 1.8x char-spacing)')
    parser.add_argument('--min-char-spacing', type=float, help='Minimum character spacing (default: 0.8)')
    parser.add_argument('--max-char-spacing', type=float, help='Maximum character spacing (default: 4.0)')
    parser.add_argument('--no-kerning', action='store_true', help='Disable kerning adjustments')
    parser.add_argument('--line-spacing', type=float, help='Line spacing multiplier (default from config: 1.8)')
    parser.add_argument('--align', choices=['left', 'center', 'right'], help='Horizontal alignment (default: center)')
    parser.add_argument('--valign', choices=['top', 'middle', 'bottom'], help='Vertical alignment (default: middle)')
    parser.add_argument('--bg-color', help='Background color (default: white)')
    parser.add_argument('--fg-color', help='Foreground color (default: black)')
    parser.add_argument('--line-width', type=int, help='Stroke width (default: 2)')
    parser.add_argument('--no-antialias', action='store_true', help='Disable antialiasing')
    parser.add_argument('--sample', action='store_true', help='Create font sample instead of rendering text')
    parser.add_argument('--list-chars', action='store_true', help='List available characters and exit')
    parser.add_argument('--save-config', help='Save default configuration to specified file')
    parser.add_argument('--save-hints', help='Save default font hints to specified file')
    
    args = parser.parse_args()
    try:
        # Load configuration and hints
        config = HersheyConfig(args.config)
        hints = FontHintsLoader(args.hints)
        if args.save_config:
            config.save_default_config(args.save_config)
            return 0
        if args.save_hints:
            hints.save_default_hints(args.save_hints)
            return 0
        
        # Load font
        font = HersheyJSONFont(args.font_json)
        if args.list_chars:
            chars = font.list_characters()
            print(f"Available characters ({len(chars)}):")
            print(''.join(chars))
            return 0
        
        # Create renderer with hints
        renderer = ScreenRenderer(font, config, hints, args.font_style)
        
        if args.sample:
            sample_width = args.width if args.width != 800 else 1600
            sample_height = args.height if args.height != 400 else 1200
            generator = FontSampleGenerator(font, renderer)
            output_path = generator.create_font_sample(args.output, sample_width, sample_height)
        else:
            render_args = {
                'width': args.width,
                'height': args.height,
                'antialias': not args.no_antialias if args.no_antialias else None,
                'use_kerning': not args.no_kerning if args.no_kerning else None,
            }
            if args.scale is not None:
                render_args['scale'] = args.scale
            if args.char_spacing is not None:
                render_args['char_spacing'] = args.char_spacing
            if args.word_spacing is not None:
                render_args['word_spacing'] = args.word_spacing
            if args.min_char_spacing is not None:
                render_args['min_char_spacing'] = args.min_char_spacing
            if args.max_char_spacing is not None:
                render_args['max_char_spacing'] = args.max_char_spacing
            if args.line_spacing is not None:
                render_args['line_spacing'] = args.line_spacing
            if args.align is not None:
                render_args['align'] = args.align
            if args.valign is not None:
                render_args['valign'] = args.valign
            if args.bg_color is not None:
                render_args['bg_color'] = args.bg_color
            if args.fg_color is not None:
                render_args['fg_color'] = args.fg_color
            if args.line_width is not None:
                render_args['line_width'] = args.line_width
            
            img = renderer.render_text(args.text, **render_args)
            img.save(args.output)
            print(f"✓ Text rendered to: {args.output}")
            print(f"  Image size: {args.width}x{args.height}")
            print(f"  Text: {repr(args.text[:50])}{'...' if len(args.text) > 50 else ''}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())