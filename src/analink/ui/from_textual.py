"""
Textual-based user interface for interactive fiction stories.
"""

from typing import List

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Button, Static

from analink.core.story_engine import StoryEngine
from analink.parser.node import Node


class ChoiceButton(Button):
    """A button representing a story choice."""

    def __init__(self, choice_node: Node, choice_number: int, *args, **kwargs):
        choice_text = (
            f"{choice_number}. {choice_node.choice_text or choice_node.content}"
        )
        super().__init__(choice_text, *args, **kwargs)
        self.choice_node = choice_node


class InkStoryApp(App):
    """
    A Textual application for playing interactive fiction stories.

    Features:
    - Streaming text with configurable typing speed
    - Scrollable story display
    - Choice buttons with keyboard navigation
    - Rich text formatting
    - Quit functionality
    """

    CSS = """
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

    def __init__(self, story_engine: StoryEngine):
        """
        Initialize the Textual app.

        Args:
            story_engine: The story engine instance to use
        """
        super().__init__()
        self.title = "📖 Interactive Ink Story"
        self.story_engine = story_engine

        # Text streaming state
        self.is_typing = False
        self.displayed_story_text = ""
        self.pending_new_content: List[tuple[str, str]] = []
        self.current_typing_content = ""
        self.current_typing_position = 0
        self._next_content_glued = False
        self.block_separator = "\n\n"

        # Connect story engine callbacks
        self.story_engine.on_content_added = self._on_content_added
        self.story_engine.on_choices_updated = self._on_choices_updated
        self.story_engine.on_story_complete = self._on_story_complete

    @classmethod
    def from_story_text(
        cls, story_text: str, typing_speed: float = 0.05
    ) -> "InkStoryApp":
        """Create an app from story text."""
        engine = StoryEngine(story_text, typing_speed=typing_speed)
        return cls(engine)

    @classmethod
    def from_file(cls, filepath: str, typing_speed: float = 0.05) -> "InkStoryApp":
        """Create an app from an ink file."""
        engine = StoryEngine.from_file(filepath, typing_speed=typing_speed)
        return cls(engine)

    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        with Container():
            with Container(id="story-container"):
                yield Static(id="story-text")
            with VerticalScroll(id="choices"):
                pass
            yield Button("❌ Quit", id="quit-button", variant="error")

    def on_mount(self) -> None:
        """Initialize the app when mounted."""
        self.story_engine.start_story()

    def _on_content_added(self, content: str):
        """Callback when new content is added to the story."""
        block_separator = "\n\n"
        # Get the current node to check for glue properties
        current_node = self.story_engine.nodes.get(self.story_engine.current_node_id)

        # Check for glue_before - affects separator before this content
        if current_node and current_node.glue_before:
            block_separator = ""
        if self._next_content_glued:
            block_separator = ""
            self._next_content_glued = False
        # content+=f" PRINT : {current_node.glue_before, current_node.content}"
        # Queue the content for typing
        formatted_content = self._format_content(content)
        self.pending_new_content.append((block_separator, formatted_content))

        # Check for glue_after - affects separator after this content
        if current_node and current_node.glue_after:
            # Store that next content should be glued
            self._next_content_glued = True

        # Start typing if not already typing
        if not self.is_typing:
            self._start_typing_new_content()

    def _on_choices_updated(self, choices: List[Node]):
        """Callback when available choices are updated."""
        # Only update choices if not currently typing
        if not self.is_typing:
            self._update_choices(choices)

    def _on_story_complete(self):
        """Callback when the story is complete."""
        # Will be handled by the choice update with empty choices
        pass

    def _format_content(self, content: str) -> str:
        """Format content with Rich markup."""
        if content.startswith("• "):
            # Format choice text
            return f"[bold cyan]{content}[/bold cyan]"
        elif content == "END OF STORY":
            return f"[bold red]{content}[/bold red]"
        elif content == "AUTO END OF STORY generated by the software":
            return f"[bold blue]{content}[/bold blue]"
        else:
            # Regular story text
            return f"[white]{content}[/white]"

    def _start_typing_new_content(self):
        """Start typing only the new content."""
        if not self.pending_new_content:
            # Update choices when done typing
            choices = self.story_engine.get_available_choices()
            self._update_choices(choices)
            return

        self.is_typing = True
        self.block_separator, self.current_typing_content = self.pending_new_content[0]
        self.current_typing_position = 0
        self._type_next_character()

    def _type_next_character(self):
        """Type the next character of the new content."""
        if self.current_typing_position >= len(self.current_typing_content):
            # Finished typing this piece of content
            self.displayed_story_text += (
                self.block_separator + self.current_typing_content
                if self.displayed_story_text
                else self.current_typing_content
            )
            self.pending_new_content.pop(0)

            if self.pending_new_content:
                # More content to type
                self._start_typing_new_content()
            else:
                # All content typed
                self.is_typing = False
                choices = self.story_engine.get_available_choices()
                self._update_choices(choices)
            return

        # Find the next safe position to cut the text (avoiding breaking markup)
        next_pos = self.current_typing_position + 1
        next_text = self.current_typing_content[:next_pos]

        # Check if we're in the middle of a markup tag
        while next_pos < len(self.current_typing_content):
            if self._is_safe_markup_position(next_text):
                break
            next_pos += 1
            next_text = self.current_typing_content[:next_pos]

        self.current_typing_position = next_pos

        # Build the complete text to display (old + partial new)
        if self.displayed_story_text:
            display_text = self.displayed_story_text + self.block_separator + next_text
        else:
            display_text = next_text

        # Update the display
        story_text = self.query_one("#story-text", Static)
        story_text.update(display_text)

        # Schedule next character
        if self.story_engine.typing_speed > 0:
            self.set_timer(self.story_engine.typing_speed, self._type_next_character)
        else:
            # If delay is 0, show all content immediately
            self.displayed_story_text += (
                self.block_separator + self.current_typing_content
                if self.displayed_story_text
                else self.current_typing_content
            )
            story_text.update(self.displayed_story_text)
            self.pending_new_content.clear()
            self.is_typing = False
            choices = self.story_engine.get_available_choices()
            self._update_choices(choices)

    def _is_safe_markup_position(self, text: str) -> bool:
        """Check if the text ends at a safe position that won't break Rich markup."""
        # Count open and closed brackets
        open_brackets = text.count("[")
        close_brackets = text.count("]")

        # If we have equal brackets, we're likely safe
        if open_brackets == close_brackets:
            return True

        # If we have more open than close, check if we're at the end of a tag
        if open_brackets > close_brackets:
            # Check if the last character is ']' which would close a tag
            return text.endswith("]")

        # If we have more close than open, something's wrong, but allow it
        return True

    def _update_choices(self, choices: List[Node]):
        """Update the choices display."""
        choices_container = self.query_one("#choices", VerticalScroll)
        choices_container.remove_children()

        if choices:
            for i, choice_node in enumerate(choices, 1):
                button = ChoiceButton(choice_node, i)
                choices_container.mount(button)
        else:
            # Show end message when no choices available
            end_message = Static(
                "[italic dim]🏁 End of story. Thank you for playing![/italic dim]",
                classes="end-message",
            )
            choices_container.mount(end_message)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "quit-button":
            self.exit()
        elif isinstance(event.button, ChoiceButton) and not self.is_typing:
            # Only allow choices when not typing
            choice_node = event.button.choice_node
            self.story_engine.make_choice(choice_node)


# Convenience functions for quick story creation
def create_story_app(story_text: str, typing_speed: float = 0.05) -> InkStoryApp:
    """
    Create a story app from text with default settings.

    Args:
        story_text: The ink story content
        typing_speed: Typing animation speed (0 = instant)

    Returns:
        Configured InkStoryApp ready to run
    """
    return InkStoryApp.from_story_text(story_text, typing_speed)


def run_story_from_file(filepath: str, typing_speed: float = 0.05):
    """
    Run a story directly from a file.

    Args:
        filepath: Path to the ink story file
        typing_speed: Typing animation speed (0 = instant)
    """
    app = InkStoryApp.from_file(filepath, typing_speed)
    app.run()


def run_story_from_text(story_text: str, typing_speed: float = 0.05):
    """
    Run a story directly from text.

    Args:
        story_text: The ink story content
        typing_speed: Typing animation speed (0 = instant)
    """
    app = create_story_app(story_text, typing_speed)
    app.run()
