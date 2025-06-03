from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Button, Static
import networkx as nx

from analink.parser.node import clean_lines, Node, NodeType
from analink.parser.graph_story import parse_story


class ChoiceButton(Button):
    def __init__(self, choice_node: Node, *args, **kwargs):
        super().__init__(choice_node.choice_text or choice_node.content, *args, **kwargs)
        self.choice_node = choice_node


class InkStoryApp(App):
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
        height: 75%;
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
        height: 25%;
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
    
    def __init__(self, story_text: str, typing_delay: float = 0.02):
        super().__init__()
        self.title = "📖 Interactive Ink Story"
        self.nodes = clean_lines(story_text)
        self.edges = parse_story(self.nodes)
        self.graph = nx.DiGraph(self.edges)
        self.story_history = []
        self.current_node_id = self._find_start_node()
        self.typing_delay = typing_delay  # Delay between characters in seconds
        self.is_typing = False  # Flag to track if text is currently being typed
        self.displayed_story_text = ""  # Text that's already been displayed
        self.pending_new_content = []  # New content waiting to be typed
        
    def _find_start_node(self) -> int:
        if not self.edges:
            return list(self.nodes.keys())[0] if self.nodes else 1
        
        nodes_with_incoming = {target for source, target in self.edges}
        all_nodes = set(self.nodes.keys())
        start_candidates = all_nodes - nodes_with_incoming
        
        if start_candidates:
            return min(start_candidates)
        else:
            return list(self.nodes.keys())[0]
    
    def compose(self) -> ComposeResult:
        with Container():
            with Container(id="story-container"):
                yield Static(id="story-text")
            with VerticalScroll(id="choices"):
                pass
            yield Button("❌ Quit", id="quit-button", variant="error")
    
    def on_mount(self) -> None:
        # Add initial node content to history
        current_node = self.nodes.get(self.current_node_id)
        if current_node and current_node.content:
            self.story_history.append(current_node.content)
        
        self.update_display()
    
    def _get_next_nodes(self, node_id: int) -> list[int]:
        if node_id in self.graph:
            return list(self.graph.successors(node_id))
        return []
    
    def _get_choice_nodes(self, node_ids: list[int]) -> list[Node]:
        choice_nodes = []
        for node_id in node_ids:
            if node_id in self.nodes and self.nodes[node_id].node_type == NodeType.CHOICE:
                choice_nodes.append(self.nodes[node_id])
        return choice_nodes
    
    def update_display(self):
        # Format the complete story history with rich markup
        formatted_history = []
        for entry in self.story_history:
            if entry.startswith("• "):
                # Format choice text
                formatted_history.append(f"[bold cyan]{entry}[/bold cyan]")
            elif entry == "END OF STORY":
                formatted_history.append(f"[bold red]{entry}[/bold red]")
            else:
                # Regular story text
                formatted_history.append(f"[white]{entry}[/white]")
        
        complete_story = "\n\n".join(formatted_history)
        
        # Check if there's new content to type
        if complete_story != self.displayed_story_text:
            # Extract only the new content
            if self.displayed_story_text:
                # Find where the new content starts
                new_content = complete_story[len(self.displayed_story_text):]
                if new_content.startswith("\n\n"):
                    new_content = new_content[2:]  # Remove leading newlines
                self.pending_new_content = [new_content]
            else:
                # First time displaying content
                self.pending_new_content = [complete_story]
                self.displayed_story_text = ""
            
            # Start typing the new content
            if self.pending_new_content:
                self._start_typing_new_content()
        else:
            # No new content, just update choices
            self._update_choices()
    
    def _start_typing_new_content(self):
        """Start typing only the new content"""
        if not self.pending_new_content:
            self._update_choices()
            return
        
        self.is_typing = True
        self.current_typing_content = self.pending_new_content[0]
        self.current_typing_position = 0
        self._type_next_character()
    
    def _type_next_character(self):
        """Type the next character of the new content"""
        if self.current_typing_position >= len(self.current_typing_content):
            # Finished typing this piece of content
            self.displayed_story_text += "\n\n" + self.current_typing_content if self.displayed_story_text else self.current_typing_content
            self.pending_new_content.pop(0)
            
            if self.pending_new_content:
                # More content to type
                self._start_typing_new_content()
            else:
                # All content typed
                self.is_typing = False
                self._update_choices()
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
            display_text = self.displayed_story_text + "\n\n" + next_text
        else:
            display_text = next_text
        
        # Update the display
        story_text = self.query_one("#story-text", Static)
        story_text.update(display_text)
        
        # Schedule next character
        if self.typing_delay > 0:
            self.set_timer(self.typing_delay, self._type_next_character)
        else:
            # If delay is 0, show all content immediately
            self.displayed_story_text += "\n\n" + self.current_typing_content if self.displayed_story_text else self.current_typing_content
            story_text.update(self.displayed_story_text)
            self.pending_new_content.clear()
            self.is_typing = False
            self._update_choices()
    
    def _is_safe_markup_position(self, text: str) -> bool:
        """Check if the text ends at a safe position that won't break Rich markup"""
        # Count open and closed brackets
        open_brackets = text.count('[')
        close_brackets = text.count(']')
        
        # If we have equal brackets, we're likely safe
        if open_brackets == close_brackets:
            return True
        
        # If we have more open than close, check if we're at the end of a tag
        if open_brackets > close_brackets:
            # Check if the last character is ']' which would close a tag
            return text.endswith(']')
        
        # If we have more close than open, something's wrong, but allow it
        return True
    
    def _update_choices(self):
        """Update the choices display"""
        choices_container = self.query_one("#choices", VerticalScroll)
        choices_container.remove_children()
        
        next_node_ids = self._get_next_nodes(self.current_node_id)
        choice_nodes = self._get_choice_nodes(next_node_ids)
        
        if choice_nodes:
            for i, choice_node in enumerate(choice_nodes, 1):
                # Add number prefix to choice text
                choice_text = f"{i}. {choice_node.choice_text or choice_node.content}"
                button = ChoiceButton(choice_node)
                button.label = choice_text
                choices_container.mount(button)
        else:
            # Show end message when no choices available
            end_message = Static(
                "[italic dim]🏁 End of story. Thank you for playing![/italic dim]",
                classes="end-message"
            )
            choices_container.mount(end_message)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit-button":
            self.exit()
        elif isinstance(event.button, ChoiceButton) and not self.is_typing:
            # Only allow choices when not typing
            choice_node = event.button.choice_node
            self.current_node_id = choice_node.item_id
            
            # Add choice to history
            self.story_history.append(f"• {choice_node.choice_text}")
            
            # Add choice content if different from choice text
            if choice_node.content and choice_node.content != choice_node.choice_text:
                self.story_history.append(choice_node.content)
            
            # Follow the story path until we find new choices or reach the end
            self._follow_story_path()
            
            self.update_display()
    
    def _follow_story_path(self):
        """Follow the story path, processing gather nodes and base content until we find choices or reach the end"""
        visited = set()  # Prevent infinite loops
        
        while self.current_node_id not in visited:
            visited.add(self.current_node_id)
            
            # Get next nodes
            next_node_ids = self._get_next_nodes(self.current_node_id)
            
            if not next_node_ids:
                # End of story
                self.story_history.append("END OF STORY")
                break
            
            # Check if any next nodes are choices
            choice_nodes = self._get_choice_nodes(next_node_ids)
            
            if choice_nodes:
                # Found choices, stop here so user can choose
                break
            
            # No choices found, continue following the path
            # Move to the first next node
            next_node_id = next_node_ids[0]
            next_node = self.nodes.get(next_node_id)
            
            if next_node:
                # Add content from gather nodes and base content to history
                if next_node.node_type == NodeType.GATHER and next_node.content:
                    self.story_history.append(next_node.content)
                elif next_node.node_type == NodeType.BASE and next_node.content:
                    self.story_history.append(next_node.content)
            
            # Move to this node
            self.current_node_id = next_node_id


def main():
    story_text = '''
"What's that?" my master asked.
*	"I am somewhat tired[."]," I repeated.
	"Really," he responded. "How deleterious."
*	"Nothing, Monsieur!"[] I replied.
	"Very good, then."
*  "I said, this journey is appalling[."] and I want no more of it."
	"Ah," he replied, not unkindly. "I see you are feeling frustrated. Tomorrow, things will improve."
'''
    
    app = InkStoryApp(story_text)
    app.run()


if __name__ == "__main__":
    main()