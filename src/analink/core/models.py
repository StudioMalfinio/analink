# analink.core.models

from enum import Enum
from typing import ClassVar, Optional

from pydantic import BaseModel, PrivateAttr, computed_field

from analink.core.condition import Condition
from analink.parser.utils import extract_parts


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
    choice_order: Optional[int] = None
    glue_before: bool = False
    glue_after: bool = False
    instruction: Optional[str] = None
    is_fallback: bool = False
    knot_name: str = "HEADER"
    stitch_name: str = "HEADER"
    is_sticky: bool = False
    condition: Optional[Condition] = None

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
            if self.content.strip().startswith("->"):
                self.is_fallback = True
                self.content = self.content.replace("->", "")
                return None
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
        while "<>" in self.content:
            if self.content.startswith("<>"):
                self.glue_before = True
                self.content = self.content[2:]
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

    def post_process(self) -> Optional["Node"]:
        """Apply all post-processing steps to this node and return any divert node created"""
        # Parse and get any divert node first
        new_node = self.parse_divert()

        # Parse choice text if this is a choice node
        if self.node_type is NodeType.CHOICE:
            self.parse_choice()

        # Parse glue and instructions on this node
        self.parse_glue()
        self.parse_instruction()

        # Parse glue and instructions on the divert node if it exists
        if new_node is not None:
            new_node.parse_glue()
            new_node.parse_instruction()

        return new_node


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
