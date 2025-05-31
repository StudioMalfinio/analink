from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Button, Static
from textual.reactive import reactive
from analink.parser.story import Story

class StoryDisplay(Static):
    """Widget to display story text"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.border_title = "Story"

class ChoiceButton(Button):
    """Custom button for story choices"""
    
    def __init__(self, choice_data, choice_index, *args, **kwargs):
        super().__init__(choice_data, *args, **kwargs)
        self.choice_data = choice_data
        self.choice_index = choice_index

class InkStoryApp(App):
    """Main Textual application for the Ink story player"""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    #story-container {
        height: 70%;
        border: solid $primary;
        margin: 1;
    }
    
    #choices-container {
        height: 30%;
        border: solid $secondary;
        margin: 1;
    }
    
    StoryDisplay {
        padding: 1;
        text-align: left;
    }
    
    ChoiceButton {
        margin: 1;
        width: 100%;
    }
    
    .choice-area {
        padding: 1;
    }
    """
    
    current_story_text = reactive("")
    
    def __init__(self, story_text):
        super().__init__()
        self.parsed_text = Story(story_text)
        
    def compose(self) -> ComposeResult:
        """Create the UI layout"""
        with Container(id="story-container"):
            yield Static(id="story-display")
        
        with Container(id="choices-container"):
            yield Vertical(id="choices", classes="choice-area")
    
    def on_mount(self) -> None:
        """Initialize the story when the app starts"""
        self.update_display()
    
    def update_display(self):
        """Update the story display and choices"""
        section_text = self.parsed_text.get_current_text()
        
        # Update story text
        story_display = self.query_one("#story-display", Static)
        
        # Build the complete story text including history
        full_text = ""
        if self.story_history:
            full_text = "\n".join(self.story_history) + "\n\n"
        
        full_text += section_text
        story_display.update(full_text)
        
        # Update choices
        choices_container = self.query_one("#choices", Vertical)
        choices_container.remove_children()
        
        choices_text = self.parsed_text.get_choices_text()
        for i, choice in enumerate(choices_text):
            button = ChoiceButton(choice, i, id=f"choice-{i}")
            choices_container.mount(button)
    
    def on_choice_button_pressed(self, event: Button.Pressed) -> None:
        """Handle choice selection"""
        if isinstance(event.button, ChoiceButton):
            choice_data = event.button.choice_data
            
            # Add choice to history
            section = self.parser.get_current_section()
            current_text = section['text']
            choice_text = f"• {choice_data['full_text']}"
            
            self.story_history.append(current_text)
            self.story_history.append(choice_text)
            
            # Add continuation if it exists
            if choice_data['continuation']:
                self.story_history.append(choice_data['continuation'])
            
            # For this simple example, we'll just show the choice was made
            # In a full implementation, you'd navigate to the next section
            self.story_history.append("\n[Story continues...]")
            
            # Update display
            story_display = self.query_one("#story-display", Static)
            full_text = "\n".join(self.story_history)
            story_display.update(full_text)
            
            # Clear choices since story segment is complete
            choices_container = self.query_one("#choices", Vertical)
            choices_container.remove_children()

def main():
    # Your example story
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