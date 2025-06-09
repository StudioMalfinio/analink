from pathlib import Path

from analink.ui.from_textual import run_story_from_file

DATA_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "notebooks"
    / "test_data"
    / "documentation_data"
)

file_name = "015.ink"
run_story_from_file(
    str(DATA_DIR / file_name),
    typing_speed=0.01,
)
