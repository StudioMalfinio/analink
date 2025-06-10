import re
from enum import Enum
from pathlib import Path
from typing import ClassVar, Optional

from pydantic import BaseModel, PrivateAttr, computed_field


def extract_parts(text):
    # Use re.DOTALL flag to make . match newlines too
    pattern = r"(.*)(?<!\\)\[([^\]]*)\](.*)"
    bracket_pattern = r"(?<!\\)\[[^\]]*\]"
    matches = re.findall(bracket_pattern, text, re.DOTALL)
    if len(matches) > 1:
        raise ValueError(f"Multiple bracket patterns found: {len(matches)} occurrences")
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


class NodeType(Enum):
    CHOICE = "choice"
    GATHER = "gather"
    KNOT = "knot"
    BASE = "base_content"
    STITCHES = "stitches"
    DIVERT = "divert"
    END = "end"
    BEGIN = "begin"
    AUTO_END = "auto_end"


class Node(BaseModel):
    # Instance fields
    _id: int = PrivateAttr(default_factory=lambda: Node._get_next_id())
    node_type: NodeType
    raw_content: str
    level: int
    line_number: int
    name: Optional[str] = None
    content: Optional[str] = None
    choice_text: Optional[str] = None
    glue_before: bool = False
    glue_after: bool = False
    instruction: Optional[str] = None

    _next_id: ClassVar[int] = 1

    @classmethod
    def end_node(cls):
        return cls(
            node_type=NodeType.END, raw_content="", level=-1, line_number=-1, name="END"
        )

    @classmethod
    def auto_end_node(cls):
        return cls(
            node_type=NodeType.AUTO_END,
            raw_content="",
            level=-1,
            line_number=-1,
            name="AUTO_END",
        )

    @classmethod
    def begin_node(cls):
        return cls(
            node_type=NodeType.BEGIN,
            raw_content="",
            level=-1,
            line_number=-1,
            name="BEGIN",
        )

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

    def parse_choice(self):
        choice_content, display_content = extract_parts(self.content)
        self.choice_text = choice_content
        self.content = display_content
        return self

    def parse_divert(self) -> Optional["Node"]:
        if self.content is not None:
            if "->" in self.content:
                new_content, divert_target = self.content.split("->")
                self.content = new_content.strip()
                return Node(
                    node_type=NodeType.DIVERT,
                    raw_content=f"-> {divert_target.strip()}",
                    level=self.level,
                    line_number=self.line_number,
                    name=divert_target.strip(),
                )
        return None

    def parse_glue(self):
        if self.content is None:
            return
        if "<>" in self.content:
            if self.content.startswith("<>"):
                self.glue_before = True
            else:
                self.glue_after = True
            self.content = self.content.replace("<>", "")

    def parse_instruction(self):
        if self.content is None:
            return
        if "#" in self.content:
            new_content, instruction = self.content.split("#")
            self.content = new_content
            self.instruction = instruction


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


def extract_knot_name(text):
    """Extract knot name between = markers"""
    # Match leading =, capture the middle part, ignore trailing =
    match = re.match(r"^=+\s*(.+?)\s*=*$", text.strip())
    if match:
        return match.group(1).strip()
    return text.strip()


def parse_node(
    line: str, line_number: int, last_level: int, in_comment: bool = False
) -> tuple[Optional[Node], int]:
    """Parse a single line of Ink code"""
    stripped = line.strip()
    # Skip empty lines and comments
    if not stripped or stripped.startswith("//"):
        return None, last_level
    if stripped.startswith("/*"):
        in_comment = True
        return None, last_level
    if stripped.startswith("*/"):
        in_comment = False
        return None, last_level
    if in_comment:
        return None, last_level
    # Skip special directives like -> END
    if stripped.startswith("->"):
        return (
            Node(
                level=last_level,
                node_type=NodeType.DIVERT,
                raw_content=line,
                line_number=line_number,
                name=stripped.split("->")[-1].strip(),
            ),
            last_level,
        )
    # Check for choices (stars) and gathers (dashes) in the stripped line
    if stripped.startswith("=="):
        knot_name = extract_knot_name(stripped)
        return (
            Node(
                node_type=NodeType.KNOT,
                raw_content=stripped,
                level=0,
                line_number=line_number,
                name=knot_name,
            ),
            0,
        )

        # this is a knot
    if stripped.startswith("="):
        stitches_name = extract_knot_name(stripped)
        return (
            Node(
                node_type=NodeType.STITCHES,
                raw_content=stripped,
                level=0,
                line_number=line_number,
                name=stitches_name,
            ),
            0,
        )
        # this is a stitches since this is not a node
    choice_count, text_choice = count_leading_chars(stripped, "*")
    gather_count, text_gather = count_leading_chars(stripped, "-")
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


class RawKnot(BaseModel):
    header: dict[int, Node]
    stitches: dict[int, dict[int, Node]]
    stitches_info: dict[int, Node]

    @property
    def block_name_to_id(self):
        ret = {}
        for item_id, node in self.stitches_info.items():
            ret[node.name] = list(self.stitches[item_id].values())[0].item_id
        return ret

    def get_blocks(self) -> list[dict[int, Node]]:
        ret = []
        if len(self.header) > 0:
            ret.append(self.header)
        ret.extend(list(self.stitches.values()))
        return ret

    @property
    def first_id(self):
        if len(self.header) > 0:
            return list(self.header.values())[0].item_id
        else:
            return list(list(self.stitches.values())[0].values())[0].item_id

    def get_node(self, item_id) -> Optional[Node]:
        if item_id in self.header:
            return self.header[item_id]
        if item_id in self.stitches_info:
            return self.stitches_info[item_id]
        for stitches in self.stitches.values():
            if item_id in stitches:
                return stitches[item_id]
        return None


class RawStory(BaseModel):
    header: dict[int, Node]
    knots: dict[int, RawKnot]
    knots_info: dict[int, Node]

    @property
    def block_name_to_id(self):
        ret = {}
        for item_id, node in self.knots_info.items():
            # knot_name => first of header if len(header)>0 else first_
            ret[node.name] = self.knots[item_id].first_id
            pre_knot_block = self.knots[item_id].block_name_to_id
            for stitiches_name, stitches_link_id in pre_knot_block.items():
                ret[f"{node.name}.{stitiches_name}"] = stitches_link_id
        return ret

    def get_node(self, item_id) -> Optional[Node]:
        if item_id in self.header:
            return self.header[item_id]
        if item_id in self.knots_info:
            return self.knots_info[item_id]
        for knot in self.knots.values():
            possible_node = knot.get_node(item_id)
            if possible_node is not None:
                return possible_node
        return None


def clean_lines(
    ink_code: str, clean_text_sep=" ", cwd: Optional[Path] = None
) -> RawStory:
    lines: dict[int, Node] = {}
    raw_lines = ink_code.strip().split("\n")
    previous_item_id = None
    i = 0
    last_level = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        if line.strip().startswith("INCLUDE"):
            file_name = line.split("INCLUDE")[-1].strip()

            with open((cwd if cwd else Path.cwd()) / file_name, "r") as f:
                new_data = f.read()
            raw_lines.extend(new_data.strip().split("\n"))
            i += 1
            continue
        parsed_line, last_level = parse_node(line, i + 1, last_level)
        if parsed_line is None:
            i += 1
            continue
        if parsed_line.node_type is NodeType.BASE:
            if previous_item_id is None:
                lines[parsed_line.item_id] = parsed_line
                previous_item_id = parsed_line.item_id
            else:
                if (
                    lines[previous_item_id].node_type is NodeType.GATHER
                    or lines[previous_item_id].node_type is NodeType.CHOICE
                    or lines[previous_item_id].node_type is NodeType.BASE
                ):
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
        else:
            lines[parsed_line.item_id] = parsed_line
            previous_item_id = parsed_line.item_id
        i += 1
    header = {}
    knots: dict[int, RawKnot] = {}
    last_knot = None
    knot_info = {}
    last_stitches = None
    knot_header = None
    stitches: dict[int, dict[int, Node]] = {}
    stitches_info: dict[int, Node] = {}
    # more logical to put elements as header, knots
    # and in knot as header, stitches
    for k, node in lines.items():
        if node.node_type is NodeType.KNOT:
            knot_info[node.item_id] = node
            if (knot_header is not None) or (len(stitches) > 0):
                # finish the previous knot
                previous_knot = RawKnot(
                    header=knot_header if knot_header else {},
                    stitches=stitches,
                    stitches_info=stitches_info,
                )
                if last_knot is None:
                    raise NotImplementedError("PARSING ERROR")
                knots[last_knot] = previous_knot
                knot_header = None  # type: ignore
                stitches = {}
                stitches_info = {}
                last_stitches = None
            last_knot = node.item_id
            continue

        if node.node_type is NodeType.STITCHES:
            stitches_info[node.item_id] = node
            stitches[node.item_id] = {}
            last_stitches = node.item_id
            continue
        new_node = node.parse_divert()
        if node.node_type is NodeType.CHOICE:
            node.parse_choice()
        if last_knot is None:
            # add to header
            node.parse_glue()
            node.parse_instruction()
            header[k] = node
            if new_node is not None:
                new_node.parse_glue()
                new_node.parse_instruction()
                header[new_node.item_id] = new_node
        else:
            # add to stitches
            if last_stitches is not None:
                node.parse_glue()
                node.parse_instruction()
                stitches[last_stitches][node.item_id] = node
                if new_node is not None:
                    new_node.parse_glue()
                    new_node.parse_instruction()
                    stitches[last_stitches][new_node.item_id] = new_node
            else:
                if knot_header is None:
                    knot_header = {}
                node.parse_glue()
                node.parse_instruction()
                knot_header[node.item_id] = node
                if new_node is not None:
                    new_node.parse_glue()
                    new_node.parse_instruction()
                    knot_header[new_node.item_id] = new_node
    if (knot_header is not None) or (len(stitches) > 0):
        # finish the previous knot
        previous_knot = RawKnot(
            header=knot_header if knot_header else {},
            stitches=stitches,
            stitches_info=stitches_info,
        )
        if last_knot is None:
            raise NotImplementedError("PARSING ERROR")
        knots[last_knot] = previous_knot
    return RawStory(header=header, knots=knots, knots_info=knot_info)  # type: ignore
