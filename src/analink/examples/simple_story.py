# Simple usage
from analink.ui.from_textual import run_story_from_text

run_story_from_text(
    """
"What's that?" my master asked.
*	"I am somewhat tired[."]," I repeated.
	"Really," he responded. "How deleterious."
*	"Nothing, Monsieur!"[] I replied.
	"Very good, then."
*  "I said, this journey is appalling[."] and I want no more of it."
	"Ah," he replied, not unkindly. "I see you are feeling frustrated. Tomorrow, things will improve."
""",
    typing_speed=0.01,
)

# # Advanced usage
# from analink.core.story_engine import StoryEngine
# from analink.ui.textual.app import InkStoryApp

# engine = StoryEngine.from_file("story.ink", typing_speed=0.05)
# app = InkStoryApp(engine)
# app.run()

# # Custom event handling
# def on_choice_made(choices):
#     print(f"Available choices: {len(choices)}")

# engine.on_choices_updated = on_choice_made
