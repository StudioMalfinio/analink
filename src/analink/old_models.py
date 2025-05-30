
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum

class ChoiceType(str, Enum):
    """Enum for choice types"""
    STICKY = "+"  # Reusable choices
    REGULAR = "*"  # Consumed after use

class Choice(BaseModel):
    """Represents a choice in the Ink script"""
    text: str = Field(..., description="The display text of the choice")
    target: str = Field(..., description="The target knot name")
    condition: Optional[str] = Field(None, description="Condition for this choice to be available")
    line_number: int = Field(0, description="Line number in the source file")
    sticky: bool = Field(False, description="Whether this choice is reusable (+ choices)")
    
    @property
    def choice_type(self) -> ChoiceType:
        """Get the choice type as an enum"""
        return ChoiceType.STICKY if self.sticky else ChoiceType.REGULAR
    
    def __str__(self) -> str:
        sticky_marker = "+" if self.sticky else "*"
        condition_str = f" {{{self.condition}}}" if self.condition else ""
        return f"{sticky_marker}{condition_str} [{self.text}] -> {self.target}"
    
class VariableChange(BaseModel):
    """Represents a variable change operation"""
    change_type: str = Field(..., description="Type of change (e.g., 'assignment')")
    expression: str = Field(..., description="The variable change expression")
    
    def __str__(self) -> str:
        return f"~ {self.expression}"
    
class Gather(BaseModel):
    """Represents a gather point in weave structure"""
    content: str = Field("", description="Content at this gather point")
    line_number: int = Field(0, description="Line number in the source file")
    nesting_level: int = Field(0, description="How deeply nested this gather is")
    
    def __str__(self) -> str:
        indent = "  " * self.nesting_level
        return f"{indent}- {self.content[:50]}..."

class WeaveElement(BaseModel):
    """Represents an element in the weave structure"""
    type: str = Field(..., description="Type: 'choice', 'gather', 'content'")
    content: str = Field("", description="Text content")
    choices: List[Choice] = Field(default_factory=list, description="Choices if this is a choice point")
    nesting_level: int = Field(0, description="Nesting depth")
    line_number: int = Field(0, description="Line number in source")

class Stitch(BaseModel):
    """Represents a stitch (sub-section) within a knot"""
    name: str = Field(..., description="Name of the stitch")
    content: str = Field("", description="Text content of the stitch")
    choices: List[Choice] = Field(default_factory=list, description="Available choices in this stitch")
    weave_elements: List[WeaveElement] = Field(default_factory=list, description="Weave structure elements")
    fallback_target: Optional[str] = Field(None, description="Default target if no choices are available")
    line_number: int = Field(0, description="Line number where this stitch is defined")
    variable_changes: List[VariableChange] = Field(default_factory=list, description="Variable changes in this stitch")
    
    @field_validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Stitch name cannot be empty")
        return v.strip()
    
    def get_choice_summary(self) -> Dict[str, int]:
        """Get a summary of choice types in this stitch"""
        sticky_count = sum(1 for choice in self.choices if choice.sticky)
        regular_count = len(self.choices) - sticky_count
        
        # Also count choices in weave elements
        for element in self.weave_elements:
            if element.type == 'choice':
                for choice in element.choices:
                    if choice.sticky:
                        sticky_count += 1
                    else:
                        regular_count += 1
        
        return {"sticky": sticky_count, "regular": regular_count}
    
    def __str__(self) -> str:
        summary = self.get_choice_summary()
        fallback = f" → {self.fallback_target}" if self.fallback_target else ""
        var_changes = f" ({len(self.variable_changes)} var changes)" if self.variable_changes else ""
        weave_info = f" (weave: {len(self.weave_elements)} elements)" if self.weave_elements else ""
        return f"  = {self.name}: {summary['regular']} regular + {summary['sticky']} sticky choices{fallback}{var_changes}{weave_info}"

class Knot(BaseModel):
    """Represents a knot (scene/section) in the Ink script"""
    name: str = Field(..., description="Name of the knot")
    content: str = Field("", description="Text content of the knot")
    choices: List[Choice] = Field(default_factory=list, description="Available choices in this knot")
    stitches: Dict[str, Stitch] = Field(default_factory=dict, description="Stitches within this knot")
    weave_elements: List[WeaveElement] = Field(default_factory=list, description="Weave structure elements")
    fallback_target: Optional[str] = Field(None, description="Default target if no choices are available")
    line_number: int = Field(0, description="Line number where this knot is defined")
    variable_changes: List[VariableChange] = Field(default_factory=list, description="Variable changes in this knot")
    
    @field_validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Knot name cannot be empty")
        return v.strip()
    
    def get_choice_summary(self) -> Dict[str, int]:
        """Get a summary of choice types in this knot"""
        sticky_count = sum(1 for choice in self.choices if choice.sticky)
        regular_count = len(self.choices) - sticky_count
        
        # Count choices in weave elements
        for element in self.weave_elements:
            if element.type == 'choice':
                for choice in element.choices:
                    if choice.sticky:
                        sticky_count += 1
                    else:
                        regular_count += 1
        
        # Also count choices in stitches
        for stitch in self.stitches.values():
            stitch_summary = stitch.get_choice_summary()
            sticky_count += stitch_summary['sticky']
            regular_count += stitch_summary['regular']
        
        return {"sticky": sticky_count, "regular": regular_count}
    
    def __str__(self) -> str:
        summary = self.get_choice_summary()
        fallback = f" → {self.fallback_target}" if self.fallback_target else ""
        var_changes = f" ({len(self.variable_changes)} var changes)" if self.variable_changes else ""
        stitches_info = f" ({len(self.stitches)} stitches)" if self.stitches else ""
        weave_info = f" (weave: {len(self.weave_elements)} elements)" if self.weave_elements else ""
        return f"{self.name}: {summary['regular']} regular + {summary['sticky']} sticky choices{fallback}{var_changes}{stitches_info}{weave_info}"

class InkScript(BaseModel):
    """Represents a complete Ink script with all its knots and variables"""
    knots: Dict[str, Knot] = Field(default_factory=dict, description="All knots in the script")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Initial variable values")
    includes: List[str] = Field(default_factory=list, description="Included files")
    
    def get_starting_knot(self, preferred_start: Optional[str] = None) -> Optional[str]:
        """Find the starting knot for path analysis"""
        if preferred_start and preferred_start in self.knots:
            return preferred_start
            
        possible_starts = [
            'start', 'scene_01_01', 'scene_1_1', 'beginning', 'intro'
        ]
        
        for start_name in possible_starts:
            if start_name in self.knots:
                return start_name
        
        # Return first knot if no standard starting point found
        return list(self.knots.keys())[0] if self.knots else None