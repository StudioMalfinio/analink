"""
Styles for the interactive fiction story app.
"""

APP_CSS = """
Screen {
    background: $surface;
}

Container {
    height: 100%;
    width: 100%;
    padding: 1;
}

#story-container {
    height: 60%;
    border: thick $primary;
    border-title-color: $primary;
    border-title-background: $surface;
    border-title-style: bold;
    padding: 1;
    margin-bottom: 1;
    background: $surface-darken-1;
}

#story-text {
    height: 100%;
    color: $text;
    scrollbar-size: 1 1;
}

#choices {
    height: 30%;
    border: thick $secondary;
    border-title-color: $secondary;
    border-title-background: $surface;
    border-title-style: bold;
    padding: 1;
    background: $surface-darken-2;
}

ChoiceButton {
    width: 100%;
    height: 3;
    margin: 1 0;
    border: solid $accent;
    background: $accent-darken-2;
    color: $text;
}

ChoiceButton:hover {
    background: $accent;
    border: solid $accent-lighten-1;
    color: $text-muted;
    text-style: bold;
}

ChoiceButton:focus {
    background: $accent-lighten-1;
    border: solid $warning;
    color: $surface;
    text-style: bold;
}

.end-message {
    text-align: center;
    padding: 1;
    color: $warning;
}

#quit-button {
    height: 3;
    width: 20;
    margin: 1;
    dock: bottom;
}
"""

"""
Vintage terminal-themed styles for the interactive fiction story app.
Classic green-on-black terminal aesthetics with retro charm.
"""

VINTAGE_TERMINAL_CSS = """
Screen {
    background: #000000;
}

Container {
    height: 100%;
    width: 100%;
    padding: 1;
    background: #000000;
}

#story-container {
    height: 60%;
    border: ascii #00ff00;
    border-title-color: #00ff00;
    border-title-background: #000000;
    border-title-style: bold;
    padding: 1;
    margin-bottom: 1;
    background: #001100;
}

#story-text {
    height: 100%;
    color: #00ff00;
    scrollbar-color: #00aa00;
    scrollbar-size: 1 1;
    text-style: none;
}

#choices {
    height: 30%;
    border: ascii #00aa00;
    border-title-color: #00aa00;
    border-title-background: #000000;
    border-title-style: bold;
    padding: 1;
    background: #000800;
}

ChoiceButton {
    width: 100%;
    height: 3;
    margin: 1 0;
    border: none;
    background: #000000;
    color: #00ff00;
    text-style: none;
}

ChoiceButton:hover {
    background: #003300;
    border: none;
    color: #00ff00;
    text-style: reverse;
}

ChoiceButton:focus {
    background: #004400;
    border: none;
    color: #00ff00;
    text-style: reverse bold;
}

.end-message {
    text-align: center;
    padding: 1;
    color: #00ff00;
    text-style: bold;
    background: #000000;
}

#quit-button {
    height: 3;
    width: 20;
    margin: 1;
    dock: bottom;
    background: #000000;
    color: #00ff00;
    border: ascii #00ff00;
    text-style: bold;
}

#quit-button:hover {
    background: #002200;
    color: #00ff00;
    border: ascii #00ff00;
    text-style: reverse bold;
}

#quit-button:focus {
    background: #003300;
    color: #00ff00;
    border: ascii #00ff00;
    text-style: reverse bold;
}
"""

"""
Fantasy scroll-themed styles for the interactive fiction story app.
Warm, parchment-like colors with medieval aesthetics.
"""

FANTASY_SCROLL_CSS = """
Screen {
    background: #2d1810;
}

Container {
    height: 100%;
    width: 100%;
    padding: 1;
    background: #2d1810;
}

#story-container {
    height: 60%;
    border: thick #8b4513;
    border-title-color: #daa520;
    border-title-background: #2d1810;
    border-title-style: bold;
    padding: 1;
    margin-bottom: 1;
    background: #f4e4bc;
}

#story-text {
    height: 100%;
    color: #3e2723;
    scrollbar-color: #8b4513;
    scrollbar-size: 1 1;
    text-style: none;
}

#choices {
    height: 30%;
    border: thick #654321;
    border-title-color: #daa520;
    border-title-background: #2d1810;
    border-title-style: bold;
    padding: 1;
    background: #e6d7c3;
}

ChoiceButton {
    width: 100%;
    height: 3;
    margin: 1 0;
    border: solid #8b4513;
    background: #d2b48c;
    color: #3e2723;
    text-style: bold;
}

ChoiceButton:hover {
    background: #daa520;
    border: solid #654321;
    color: #2d1810;
    text-style: bold;
}

ChoiceButton:focus {
    background: #cd853f;
    border: thick #3e2723;
    color: #000000;
    text-style: bold;
}

.end-message {
    text-align: center;
    padding: 1;
    color: #8b0000;
    text-style: bold italic;
    background: #f4e4bc;
}

#quit-button {
    height: 3;
    width: 20;
    margin: 1;
    dock: bottom;
    background: #8b0000;
    color: #f4e4bc;
    border: solid #654321;
    text-style: bold;
}

#quit-button:hover {
    background: #a0522d;
    color: #ffffff;
    border: thick #8b4513;
}

#quit-button:focus {
    background: #b8860b;
    color: #000000;
    border: thick #3e2723;
}
"""

"""
Cyberpunk-themed styles for the interactive fiction story app.
Neon colors, glowing effects, and futuristic aesthetics.
"""

CYBERPUNK_CSS = """
Screen {
    background: $surface;
}

Container {
    height: 100%;
    width: 100%;
    padding: 1;
}

#story-container {
    height: 60%;
    border: thick $primary;
    border-title-color: $primary;
    border-title-background: $surface;
    border-title-style: bold;
    padding: 1;
    margin-bottom: 1;
    background: $surface-darken-3;
}

#story-text {
    height: 100%;
    color: $text;
    scrollbar-size: 1 1;
}

#choices {
    height: 30%;
    border: thick $secondary;
    border-title-color: $secondary;
    border-title-background: $surface;
    border-title-style: bold;
    padding: 1;
    background: $surface-darken-2;
}

ChoiceButton {
    width: 100%;
    height: 3;
    margin: 1 0;
    border: solid $accent;
    background: $accent-darken-3;
    color: $accent-lighten-2;
    text-style: bold;
}

ChoiceButton:hover {
    background: $accent-darken-1;
    border: thick $accent;
    color: $text;
    text-style: bold;
}

ChoiceButton:focus {
    background: $accent;
    border: thick $warning;
    color: $surface;
    text-style: bold;
}

.end-message {
    text-align: center;
    padding: 1;
    color: $warning;
    text-style: bold;
}

#quit-button {
    height: 3;
    width: 20;
    margin: 1;
    dock: bottom;
    background: $error-darken-2;
    color: $error-lighten-2;
    border: solid $error;
    text-style: bold;
}

#quit-button:hover {
    background: $error-darken-1;
    color: $text;
    border: thick $error;
}

#quit-button:focus {
    background: $error;
    color: $surface;
    border: thick $warning;
}
"""
