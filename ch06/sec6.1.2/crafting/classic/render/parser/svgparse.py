import re

class SVGPathParser:
    def __init__(self, svg_content):
        self.svg_content = svg_content
        self.paths = []

    def parse(self):
        self.paths = self._extract_paths(self.svg_content)

    def _extract_paths(self, svg_content):
        paths = []
        for line in svg_content.splitlines():
            if "<path" in line:
                style_match = re.search(r'style="fill:([^"]+)"', line)
                d_match = re.search(r'd="([^"]+)"', line)
                if style_match and d_match:
                    fill_color = self._parse_color(style_match.group(1))
                    d_commands = self._parse_d_commands(d_match.group(1))
                    paths.append({"fill": fill_color, "commands": d_commands})
        return paths

    def _parse_color(self, color):
        if color.startswith("#") and len(color) == 7:
            return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
        return (0, 0, 0) # black

    def _parse_d_commands(self, d):
        # regex split commands and numbers, while keeping them separate
        tokens = re.findall(r'[a-zA-Z]|-?\d*\.?\d+', d)
        commands = []
        current_command = None
        command_args = []

        for token in tokens:
            if re.match(r'[a-zA-Z]', token):  # commands (M, L, C ..)
                if current_command:
                    commands.append((current_command, command_args))
                current_command = token
                command_args = []
            else:  # argument (number)
                try:
                    command_args.append(float(token))
                except ValueError:
                    print(f"Warning: Skipping invalid number '{token}' in path data.")
        if current_command:
            commands.append((current_command, command_args))

        return commands

    def _tokenize_d(self, d): # d attr in SVG
        tokens = []
        current_token = []
        for char in d:
            if char.isalpha() or char in "+-":
                if current_token:
                    tokens.append("".join(current_token))
                    current_token = []
                tokens.append(char)
            elif char.isdigit() or char == ".":
                current_token.append(char)
            elif char.isspace() and current_token:
                tokens.append("".join(current_token))
                current_token = []
        if current_token:
            tokens.append("".join(current_token))
        return tokens

# example
svg_data = """
<svg xmlns="http://www.w3.org/2000/svg">
    <path style="fill:#653300" d="M274 0 C289 1.667 308 1.667 323 0 L357 0 z"/>
    <path style="fill:#503e20" d="M323 0 C308 1.667 289 1.667 274 0 z"/>
</svg>
"""

parser = SVGPathParser(svg_data)
parser.parse()

for path in parser.paths:
    print(f"Fill: {path['fill']}, Commands: {path['commands']}")
