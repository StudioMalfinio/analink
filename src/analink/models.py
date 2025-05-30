from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class ChoiceType(str, Enum):
    """Enum for choice types"""
    STICKY = "+"  # Reusable choices
    REGULAR = "*"  # Consumed after use

class Choice(BaseModel):
    """Represents a choice in the Ink script"""
    display_text: str = Field(..., description="The display text of the choice")
    text_after_choice: Optional[str] = Field(None, description="The text displayed when choosen")
    target: Optional[str] = Field(None, description="The target knot name")
    condition: Optional[str] = Field(None, description="Condition for this choice to be available")
    line_number: int = Field(0, description="Line number in the source file")
    sticky: bool = Field(False, description="Whether this choice is reusable (+ choices)")
    
    @property
    def choice_type(self) -> ChoiceType:
        """Get the choice type as an enum"""
        return ChoiceType.STICKY if self.sticky else ChoiceType.REGULAR
    

#   https://github.com/inkle/ink/blob/master/Documentation/WritingWithInk.md