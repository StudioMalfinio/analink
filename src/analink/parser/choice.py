import re
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from analink.parser.utils import count_leading_chars


class ChoiceType(str, Enum):
    """Enum for choice types"""

    STICKY = "+"  # Reusable choices
    REGULAR = "*"  # Consumed after use


class Choice(BaseModel):
    """Represents a choice in the Ink script"""

    display_text: str = Field(..., description="The display text of the choice")
    text_after_choice: Optional[str] = Field(
        None, description="The text displayed when choosen"
    )
    target: Optional[str] = Field(None, description="The target knot name")
    condition: Optional[str] = Field(
        None, description="Condition for this choice to be available"
    )
    line_number: int = Field(0, description="Line number in the source file")
    sticky: bool = Field(
        False, description="Whether this choice is reusable (+ choices)"
    )

    @property
    def choice_type(self) -> ChoiceType:
        """Get the choice type as an enum"""
        return ChoiceType.STICKY if self.sticky else ChoiceType.REGULAR


def extract_parts(text):
    # Use re.DOTALL flag to make . match newlines too
    pattern = r"(.*)(?<!\\)\[([^\]]*)\](.*)"

    match = re.match(pattern, text, re.DOTALL)

    if match:
        before, inside, after = match.groups()

        # Version 1: before + inside
        version1 = before + inside

        # Version 2: before + after
        version2 = before + after

        return version1, version2
    else:
        # No brackets found, return original text twice
        return text, text


def parse_choices(lines: str) -> list[Choice]:
    lines_list = lines.split("\n")
    i = 0
    key_id = 0
    choices: list[Choice] = []
    while i < len(lines_list):
        line = lines_list[i]
        stripped = line.strip()
        if count_leading_chars(stripped, "*") > 0:
            line_number = i
            choice_buffer = [line.lstrip("*").strip()]
            i += 1
            while i < len(lines_list):
                line = lines_list[i]
                stripped = line.strip()
                if count_leading_chars(stripped, "*") == 0:
                    choice_buffer.append(stripped)
                    i += 1
                else:
                    # Don't increment i here - we want to process this line in the outer loop
                    break
            # print(choice_buffer)
            # choices.append(
            #     parse_only_once_choice(choice_buffer, line_number, key_id=key_id)
            # )
            key_id += 1
        else:
            i += 1
    return choices
