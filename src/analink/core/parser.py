# analink.parser.node

from pathlib import Path
from typing import Optional

from analink.core.line_parser import InkLineParser, LineMerger
from analink.core.models import Node, NodeType, RawKnot, RawStory


class RawStoryBuilder:
    """Handles building the hierarchical story structure from parsed nodes"""

    def __init__(self) -> None:
        self.header: dict[int, Node] = {}
        self.knots: dict[int, RawKnot] = {}
        self.knots_info: dict[int, Node] = {}

        # Current knot state
        self.current_knot_id: Optional[int] = None
        self.current_knot_header: Optional[dict[int, Node]] = None
        self.current_stitches: dict[int, dict[int, Node]] = {}
        self.current_stitches_info: dict[int, Node] = {}
        self.current_stitches_id: Optional[int] = None

        # Context tracking
        self.current_knot_name: str = "HEADER"
        self.current_stitch_name: str = "HEADER"

    def finalize_current_knot(self) -> None:
        """Finalize the current knot and add it to the knots collection"""
        if self.current_knot_id is not None and (
            self.current_knot_header or self.current_stitches
        ):
            knot = RawKnot(
                header=self.current_knot_header or {},
                stitches=self.current_stitches,
                stitches_info=self.current_stitches_info,
            )
            self.knots[self.current_knot_id] = knot

            # Reset current knot state
            self.current_knot_header = None
            self.current_stitches = {}
            self.current_stitches_info = {}
            self.current_stitches_id = None

    def start_new_knot(self, node: Node) -> None:
        """Start a new knot"""
        self.finalize_current_knot()
        self.knots_info[node.item_id] = node
        self.current_knot_id = node.item_id
        self.current_knot_name = node.name or "HEADER"  # Add this line
        self.current_stitch_name = "HEADER"  # Reset stitch context

    def start_new_stitches(self, node: Node) -> None:
        """Start a new stitches section"""
        self.current_stitches_info[node.item_id] = node
        self.current_stitches[node.item_id] = {}
        self.current_stitches_id = node.item_id
        self.current_stitch_name = node.name or "HEADER"  # Add this line

    def add_content_node(self, node: Node, divert_node: Optional[Node] = None) -> None:
        """Add a content node to the appropriate section"""
        node.knot_name = self.current_knot_name
        node.stitch_name = self.current_stitch_name
        if self.current_knot_id is None:
            # Add to story header
            self.header[node.item_id] = node
            if divert_node is not None:
                self.header[divert_node.item_id] = divert_node
        else:
            # Add to current knot
            if self.current_stitches_id is not None:
                # Add to current stitches
                self.current_stitches[self.current_stitches_id][node.item_id] = node
                if divert_node is not None:
                    self.current_stitches[self.current_stitches_id][
                        divert_node.item_id
                    ] = divert_node
            else:
                # Add to knot header
                if self.current_knot_header is None:
                    self.current_knot_header = {}
                self.current_knot_header[node.item_id] = node
                if divert_node is not None:
                    self.current_knot_header[divert_node.item_id] = divert_node

    def process_node(self, node: Node) -> None:
        """Process a single node and add it to the appropriate section"""
        if node.node_type == NodeType.KNOT:
            self.start_new_knot(node)
            node.knot_name = node.name or "HEADER"  # Set its own knot name
            node.stitch_name = "HEADER"
        elif node.node_type == NodeType.STITCHES:
            node.knot_name = self.current_knot_name  # Inherit current knot
            node.stitch_name = node.name or "HEADER"  # Set its own stitch name
            self.start_new_stitches(node)
        else:
            # Process content nodes (BASE, CHOICE, GATHER, DIVERT)
            divert_node = node.post_process()
            self.add_content_node(node, divert_node)

    def build_story(self, nodes: dict[int, Node]) -> RawStory:
        """Build the final story structure from the given nodes"""
        for node in nodes.values():
            self.process_node(node)

        # Finalize any remaining knot
        self.finalize_current_knot()

        return RawStory(
            header=self.header, knots=self.knots, knots_info=self.knots_info
        )


class InkParser:
    """Main parser class that orchestrates the entire parsing process"""

    def __init__(self, clean_text_sep: str = " "):
        self.clean_text_sep = clean_text_sep

    def handle_include_files(
        self, raw_lines: list[str], cwd: Optional[Path] = None
    ) -> list[str]:
        """Process INCLUDE directives and return expanded lines"""
        for line in raw_lines:
            if line.strip().startswith("INCLUDE"):
                file_name = line.split("INCLUDE")[-1].strip()
                file_path = (cwd if cwd else Path.cwd()) / file_name

                with open(file_path, "r") as f:
                    included_content = f.read()
                raw_lines.remove(line)
                raw_lines.extend(included_content.strip().split("\n"))
        return raw_lines

    def parse(self, ink_code: str, cwd: Optional[Path] = None) -> RawStory:
        """Parse Ink code and return a RawStory structure"""
        parser = InkLineParser()
        line_merger = LineMerger(self.clean_text_sep)

        # Handle includes
        raw_lines = ink_code.strip().split("\n")
        expanded_lines = self.handle_include_files(raw_lines, cwd)

        # Parse each line
        last_level = 0
        for i, line in enumerate(expanded_lines):
            parsed_line, last_level = parser.parse_line(line, i + 1, last_level)
            if parsed_line is not None:
                line_merger.add_node(parsed_line)

        # Build the final story structure
        lines = line_merger.get_lines()
        story_builder = RawStoryBuilder()
        return story_builder.build_story(lines)


def clean_lines(
    ink_code: str, clean_text_sep=" ", cwd: Optional[Path] = None
) -> RawStory:
    parser = InkParser(clean_text_sep)
    return parser.parse(ink_code, cwd)
