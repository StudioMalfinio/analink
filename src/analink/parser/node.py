from enum import Enum
from typing import ClassVar, Optional

from pydantic import BaseModel, PrivateAttr, computed_field


class NodeType(Enum):
    CHOICE = "choice"
    GATHER = "gather"
    BASE = "base_content"


class Node(BaseModel):
    # Instance fields
    _id: int = PrivateAttr(default_factory=lambda: Node._get_next_id())
    node_type: NodeType
    raw_content: str
    level: int
    line_number: int
    content: Optional[str] = None
    choice_text: Optional[str] = None

    _next_id: ClassVar[int] = 1

    @computed_field  # type: ignore[prop-decorator]
    @property
    def item_id(self) -> int:
        return self._id

    @classmethod
    def _get_next_id(cls) -> int:
        """Get the next available ID and increment the counter"""
        current_id = cls._next_id
        cls._next_id += 1
        return current_id

    @classmethod
    def reset_id_counter(cls) -> None:
        """Reset the ID counter (useful for testing)"""
        cls._next_id = 1


def count_leading_chars(line: str, char: str) -> tuple[int, str]:
    """Count leading characters (for nesting level) and return the text without the leading char"""
    count = 0
    idx = 0
    for c in line:
        if c == char:
            count += 1
            idx += 1
        elif c == " " or c == "\t":
            idx += 1
            continue
        else:
            break
    return count, line[idx:]


def parse_node(line: str, line_number: int) -> Optional[Node]:
    """Parse a single line of Ink code"""
    stripped = line.strip()
    # Skip empty lines and comments
    if not stripped or stripped.startswith("//"):
        return None

    # Skip special directives like -> END
    if stripped.startswith("->"):
        return None

    # Check for choices (stars) and gathers (dashes) in the stripped line
    choice_count, text_choice = count_leading_chars(stripped, "*")
    gather_count, text_gather = count_leading_chars(stripped, "-")
    if choice_count > 0:
        return Node(
            level=choice_count,
            node_type=NodeType.CHOICE,
            content=text_choice,
            raw_content=line,
            line_number=line_number,
        )
    if gather_count > 0:
        return Node(
            level=gather_count,
            node_type=NodeType.GATHER,
            content=text_gather,
            raw_content=line,
            line_number=line_number,
        )

    return Node(
        level=0,
        node_type=NodeType.BASE,
        content=stripped,
        raw_content=line,
        line_number=line_number,
    )


def clean_lines(ink_code: str, clean_text_sep=" ") -> dict[int, Node]:
    lines: dict[int, Node] = {}
    raw_lines = ink_code.strip().split("\n")
    previous_item_id = None
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        parsed_line = parse_node(line, i + 1)
        if parsed_line is None:
            i += 1
            continue
        if parsed_line.node_type is NodeType.BASE:
            if previous_item_id is None:
                lines[parsed_line.item_id] = parsed_line
                previous_item_id = parsed_line.item_id
            else:
                merged_node = Node(
                    level=lines[previous_item_id].level,
                    node_type=lines[previous_item_id].node_type,
                    content=lines[previous_item_id].content
                    + clean_text_sep
                    + parsed_line.content,
                    raw_content=lines[previous_item_id].raw_content
                    + "\n"
                    + parsed_line.raw_content,
                    line_number=lines[previous_item_id].line_number,
                )
                lines[merged_node.item_id] = merged_node
                del lines[previous_item_id]
                previous_item_id = merged_node.item_id
        else:
            lines[parsed_line.item_id] = parsed_line
            previous_item_id = parsed_line.item_id
        i += 1
    return lines
