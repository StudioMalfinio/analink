# Simple usage
from analink.ui.from_textual import run_story_from_text

another_example = """
-> paragraph_1
=== paragraph_1 ===
You stand by the wall of Analand, sword in hand.
* [Open the gate] -> paragraph_2
* [Smash down the gate] -> paragraph_3
* [Turn back and go home] -> paragraph_4

=== paragraph_2 ===
You open the gate, and step out onto the path.

=== paragraph_3 ===
The third

=== paragraph_4 ===
"What's that?" my master asked.
*	"I am somewhat tired[."]," I repeated.
	"Really," he responded. "How deleterious."
*	"Nothing, Monsieur!"[] I replied.
	"Very good, then."
*  "I said, this journey is appalling[."] and I want no more of it."
	"Ah," he replied, not unkindly. "I see you are feeling frustrated. Tomorrow, things will improve."
"""
base_example = """
"What's that?" my master asked.
*	"I am somewhat tired[."]," I repeated.
	"Really," he responded. "How deleterious."
*	"Nothing, Monsieur!"[] I replied.
	"Very good, then."
*  "I said, this journey is appalling[."] and I want no more of it."
	"Ah," he replied, not unkindly. "I see you are feeling frustrated. Tomorrow, things will improve."
"""
run_story_from_text(
    another_example,
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
