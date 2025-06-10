from typing import Optional

from analink.core.models import Node, NodeType
from analink.parser.utils import count_leading_chars, extract_knot_name


class InkLineParser:
    """Handles parsing individual lines of Ink code"""

    def __init__(self):
        self.in_comment = False

    def is_comment_or_empty(self, line: str) -> bool:
        """Check if line is empty or a comment"""
        stripped = line.strip()

        if not stripped or stripped.startswith("//"):
            return True

        if stripped.startswith("/*") and not stripped.endswith("*/"):
            self.in_comment = True
            return True
        elif stripped.startswith("/*") and stripped.endswith("*/"):
            self.in_comment = False
            return True
        elif stripped.endswith("*/"):
            self.in_comment = False
            return True
        elif self.in_comment:
            return True

        return False

    def parse_divert(
        self, line: str, last_level: int, line_number: int
    ) -> Optional[Node]:
        """Parse divert lines (starting with ->)"""
        stripped = line.strip()
        if stripped.startswith("->"):
            return Node(
                level=last_level,
                node_type=NodeType.DIVERT,
                raw_content=line,
                line_number=line_number,
                name=stripped.split("->")[-1].strip(),
            )
        return None

    def parse_knot_or_stitches(self, line: str, line_number: int) -> Optional[Node]:
        """Parse knot (==) or stitches (=) lines"""
        stripped = line.strip()
        if stripped.startswith("=="):
            knot_name = extract_knot_name(stripped)
            return Node(
                node_type=NodeType.KNOT,
                raw_content=stripped,
                level=0,
                line_number=line_number,
                name=knot_name,
            )
        elif stripped.startswith("="):
            stitches_name = extract_knot_name(stripped)
            return Node(
                node_type=NodeType.STITCHES,
                raw_content=stripped,
                level=0,
                line_number=line_number,
                name=stitches_name,
            )
        return None

    def parse_choice_or_gather(
        self, line: str, line_number: int
    ) -> Optional[tuple[Node, int]]:
        """Parse choice (*) or gather (-) lines"""
        stripped = line.strip()

        choice_count, text_choice = count_leading_chars(stripped, "*")
        if choice_count > 0:
            return (
                Node(
                    level=choice_count,
                    node_type=NodeType.CHOICE,
                    content=text_choice,
                    raw_content=line,
                    line_number=line_number,
                ),
                choice_count,
            )

        gather_count, text_gather = count_leading_chars(stripped, "-")
        if gather_count > 0:
            return (
                Node(
                    level=gather_count,
                    node_type=NodeType.GATHER,
                    content=text_gather,
                    raw_content=line,
                    line_number=line_number,
                ),
                gather_count,
            )

        return None

    def parse_line(
        self, line: str, line_number: int, last_level: int
    ) -> tuple[Optional[Node], int]:
        """Parse a single line of Ink code"""
        # Skip empty lines and comments
        if self.is_comment_or_empty(line):
            return None, last_level

        # Try parsing as divert
        divert_node = self.parse_divert(line, last_level, line_number)
        if divert_node is not None:
            return divert_node, last_level

        # Try parsing as knot or stitches
        knot_or_stitches_node = self.parse_knot_or_stitches(line, line_number)
        if knot_or_stitches_node is not None:
            return knot_or_stitches_node, 0

        # Try parsing as choice or gather
        choice_or_gather_result = self.parse_choice_or_gather(line, line_number)
        if choice_or_gather_result is not None:
            return choice_or_gather_result

        # Default to base content
        stripped = line.strip()
        return (
            Node(
                level=last_level,
                node_type=NodeType.BASE,
                content=stripped,
                raw_content=line,
                line_number=line_number,
            ),
            last_level,
        )


class LineMerger:
    """Handles merging of consecutive BASE, CHOICE, and GATHER nodes"""

    def __init__(self, clean_text_sep: str = " "):
        self.clean_text_sep = clean_text_sep
        self.lines: dict[int, Node] = {}
        self.previous_item_id: Optional[int] = None

    def can_merge_with_previous(self, node: Node) -> bool:
        """Check if the current node can be merged with the previous one"""
        if node.node_type != NodeType.BASE or self.previous_item_id is None:
            return False

        previous_node = self.lines[self.previous_item_id]
        return previous_node.node_type in (
            NodeType.GATHER,
            NodeType.CHOICE,
            NodeType.BASE,
        )

    def merge_with_previous(self, node: Node) -> Node:
        """Merge the current node with the previous one"""
        if self.previous_item_id is None:
            raise AttributeError("previous item id cannot be None when merging")
        previous_node = self.lines[self.previous_item_id]
        if previous_node.content is None or node.content is None:
            raise AttributeError("nodes content cannot be None when merging")
        merged_node = Node(
            level=previous_node.level,
            node_type=previous_node.node_type,
            content=previous_node.content + self.clean_text_sep + node.content,
            raw_content=previous_node.raw_content + "\n" + node.raw_content,
            line_number=previous_node.line_number,
        )

        # Remove the previous node and update tracking
        del self.lines[self.previous_item_id]
        self.lines[merged_node.item_id] = merged_node
        self.previous_item_id = merged_node.item_id

        return merged_node

    def add_node(self, node: Node) -> None:
        """Add a node, merging with previous if applicable"""
        if node.node_type == NodeType.BASE and self.can_merge_with_previous(node):
            self.merge_with_previous(node)
        else:
            self.lines[node.item_id] = node
            self.previous_item_id = node.item_id

    def get_lines(self) -> dict[int, Node]:
        """Get the final merged lines"""
        return self.lines
