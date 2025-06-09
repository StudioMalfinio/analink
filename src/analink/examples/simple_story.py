# Simple usage
from analink.ui.from_textual import run_story_from_text

example_1 = """=== back_in_london ===

We arrived into London at 9.45pm exactly.

*	"There is not a moment to lose!"[] I declared.
	-> hurry_outside

*	"Monsieur, let us savour this moment!"[] I declared.
	My master clouted me firmly around the head and dragged me out of the door.
	-> dragged_outside

*	[We hurried home] -> hurry_outside


=== hurry_outside ===
We hurried home to Savile Row -> as_fast_as_we_could


=== dragged_outside ===
He insisted that we hurried home to Savile Row
-> as_fast_as_we_could


=== as_fast_as_we_could ===
<> as fast as we could."""
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
    example_1,
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
