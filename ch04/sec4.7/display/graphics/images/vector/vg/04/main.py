from vgf_renderer import SimpleRenderer
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2

display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)
renderer = SimpleRenderer(display)
renderer.render_file('image.vgf')
