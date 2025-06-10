# test_models.py


from analink.core.models import Node, NodeType, RawKnot, RawStory


class TestNodeType:
    """Test the NodeType enum"""

    def test_node_type_values(self):
        """Test that NodeType enum has correct values"""
        assert NodeType.CHOICE.value == "choice"
        assert NodeType.GATHER.value == "gather"
        assert NodeType.BASE.value == "base_content"
        assert NodeType.KNOT.value == "knot"
        assert NodeType.STITCHES.value == "stitches"
        assert NodeType.DIVERT.value == "divert"
        assert NodeType.END.value == "end"
        assert NodeType.BEGIN.value == "begin"
        assert NodeType.AUTO_END.value == "auto_end"

    def test_node_type_members(self):
        """Test that all expected members exist"""
        assert hasattr(NodeType, "CHOICE")
        assert hasattr(NodeType, "GATHER")
        assert hasattr(NodeType, "BASE")
        assert hasattr(NodeType, "KNOT")
        assert hasattr(NodeType, "STITCHES")
        assert hasattr(NodeType, "DIVERT")
        assert hasattr(NodeType, "END")
        assert hasattr(NodeType, "BEGIN")
        assert hasattr(NodeType, "AUTO_END")


class TestNode:
    """Test the Node class"""

    def setup_method(self):
        """Reset ID counter before each test"""
        Node.reset_id_counter()

    def test_node_creation_basic(self):
        """Test basic node creation"""
        node = Node(
            node_type=NodeType.BASE, raw_content="test content", level=0, line_number=1
        )
        assert node.node_type == NodeType.BASE
        assert node.raw_content == "test content"
        assert node.level == 0
        assert node.line_number == 1
        assert node.content is None
        assert node.choice_text is None
        assert node.name is None

    def test_node_creation_with_optional_fields(self):
        """Test node creation with optional fields"""
        node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Choice text",
            level=1,
            line_number=5,
            content="Choice text",
            choice_text="Choice text",
            name="choice_1",
        )
        assert node.node_type == NodeType.CHOICE
        assert node.raw_content == "* Choice text"
        assert node.level == 1
        assert node.line_number == 5
        assert node.content == "Choice text"
        assert node.choice_text == "Choice text"
        assert node.name == "choice_1"

    def test_node_creation_with_new_fields(self):
        """Test node creation with new fields like glue and instruction"""
        node = Node(
            node_type=NodeType.BASE,
            raw_content="test content",
            level=0,
            line_number=1,
            content="test content",
            glue_before=True,
            glue_after=False,
            instruction="CLEAR",
            choice_order=5,
        )
        assert node.glue_before is True
        assert node.glue_after is False
        assert node.instruction == "CLEAR"
        assert node.choice_order == 5

    def test_item_id_property(self):
        """Test that item_id returns the private _id"""
        node = Node(node_type=NodeType.BASE, raw_content="test", level=0, line_number=1)
        assert node.item_id == 1

    def test_id_increments(self):
        """Test that IDs increment for each new node"""
        node1 = Node(
            node_type=NodeType.BASE, raw_content="test1", level=0, line_number=1
        )
        node2 = Node(
            node_type=NodeType.BASE, raw_content="test2", level=0, line_number=2
        )
        node3 = Node(
            node_type=NodeType.BASE, raw_content="test3", level=0, line_number=3
        )

        assert node1.item_id == 1
        assert node2.item_id == 2
        assert node3.item_id == 3

    def test_reset_id_counter(self):
        """Test that reset_id_counter resets the counter to 1"""
        Node(node_type=NodeType.BASE, raw_content="test", level=0, line_number=1)
        Node.reset_id_counter()
        node = Node(node_type=NodeType.BASE, raw_content="test", level=0, line_number=1)
        assert node.item_id == 1

    def test_get_next_id_class_method(self):
        """Test the _get_next_id class method"""
        Node.reset_id_counter()
        id1 = Node._get_next_id()
        id2 = Node._get_next_id()
        id3 = Node._get_next_id()

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

    def test_end_node_class_method(self):
        """Test the end_node class method"""
        node = Node.end_node()
        assert node.node_type == NodeType.END
        assert node.raw_content == ""
        assert node.level == -1
        assert node.line_number == -1
        assert node.name == "END"

    def test_auto_end_node_class_method(self):
        """Test the auto_end_node class method"""
        node = Node.auto_end_node()
        assert node.node_type == NodeType.AUTO_END
        assert node.raw_content == ""
        assert node.level == -1
        assert node.line_number == -1
        assert node.name == "AUTO_END"

    def test_begin_node_class_method(self):
        """Test the begin_node class method"""
        node = Node.begin_node()
        assert node.node_type == NodeType.BEGIN
        assert node.raw_content == ""
        assert node.level == -1
        assert node.line_number == -1
        assert node.name == "BEGIN"

    def test_parse_choice_with_brackets(self):
        """Test parse_choice method with bracketed text"""
        node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* [Open door] You open the heavy door",
            level=1,
            line_number=1,
            content="[Open door] You open the heavy door",
        )
        result = node.parse_choice()
        assert result.choice_text == "Open door"
        assert result.content == " You open the heavy door"

    def test_parse_choice_without_brackets(self):
        """Test parse_choice method without brackets"""
        node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Simple choice",
            level=1,
            line_number=1,
            content="Simple choice",
        )
        result = node.parse_choice()
        assert result.choice_text == "Simple choice"
        assert result.content == "Simple choice"

    def test_parse_divert_with_arrow(self):
        """Test parse_divert method with arrow"""
        node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Go to forest -> forest_path",
            level=1,
            line_number=1,
            content="Go to forest -> forest_path",
        )
        divert_node = node.parse_divert()
        assert divert_node is not None
        assert divert_node.node_type == NodeType.DIVERT
        assert divert_node.name == "forest_path"
        assert node.content == "Go to forest"

    def test_parse_divert_without_arrow(self):
        """Test parse_divert method without arrow"""
        node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Simple choice",
            level=1,
            line_number=1,
            content="Simple choice",
        )
        divert_node = node.parse_divert()
        assert divert_node is None
        assert node.content == "Simple choice"

    def test_parse_divert_with_empty_content(self):
        """Test parse_divert with None content"""
        node = Node(
            node_type=NodeType.BASE,
            raw_content="Some text",
            level=0,
            line_number=1,
            content=None,
        )
        divert_node = node.parse_divert()
        assert divert_node is None

    def test_parse_glue_before(self):
        """Test parse_glue method with glue before content"""
        node = Node(
            node_type=NodeType.BASE,
            raw_content="<>Some text",
            level=0,
            line_number=1,
            content="<>Some text",
        )
        node.parse_glue()
        assert node.glue_before is True
        assert node.glue_after is False
        assert node.content == "Some text"

    def test_parse_glue_after(self):
        """Test parse_glue method with glue after content"""
        node = Node(
            node_type=NodeType.BASE,
            raw_content="Some text<>",
            level=0,
            line_number=1,
            content="Some text<>",
        )
        node.parse_glue()
        assert node.glue_before is False
        assert node.glue_after is True
        assert node.content == "Some text"

    def test_parse_glue_none_content(self):
        """Test parse_glue method with None content"""
        node = Node(
            node_type=NodeType.BASE,
            raw_content="Some text",
            level=0,
            line_number=1,
            content=None,
        )
        node.parse_glue()  # Should not raise an error
        assert node.glue_before is False
        assert node.glue_after is False

    def test_parse_instruction(self):
        """Test parse_instruction method"""
        node = Node(
            node_type=NodeType.BASE,
            raw_content="Some text # CLEAR",
            level=0,
            line_number=1,
            content="Some text # CLEAR",
        )
        node.parse_instruction()
        assert node.content == "Some text "
        assert node.instruction == " CLEAR"

    def test_parse_instruction_none_content(self):
        """Test parse_instruction method with None content"""
        node = Node(
            node_type=NodeType.BASE,
            raw_content="Some text",
            level=0,
            line_number=1,
            content=None,
        )
        node.parse_instruction()  # Should not raise an error
        assert node.instruction is None

    def test_post_process_choice_with_divert(self):
        """Test post_process method with choice that has divert"""
        node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* [Take sword] You take the sword -> combat",
            level=1,
            line_number=1,
            content="[Take sword] You take the sword -> combat",
        )
        divert_node = node.post_process()

        # Check that choice was parsed
        assert node.choice_text == "Take sword"
        assert node.content == " You take the sword"

        # Check that divert node was created
        assert divert_node is not None
        assert divert_node.node_type == NodeType.DIVERT
        assert divert_node.name == "combat"

    def test_post_process_base_with_glue_and_instruction(self):
        """Test post_process method with base content having glue and instruction"""
        node = Node(
            node_type=NodeType.BASE,
            raw_content="<>Some text # CLEAR",
            level=0,
            line_number=1,
            content="<>Some text # CLEAR",
        )
        divert_node = node.post_process()

        assert divert_node is None
        assert node.glue_before is True
        assert node.content == "Some text "
        assert node.instruction == " CLEAR"

    def test_post_process_with_divert_and_glue(self):
        """Test post_process method where both main and divert nodes have glue"""
        node = Node(
            node_type=NodeType.BASE,
            raw_content="<>Text<> -> <>target<>",
            level=0,
            line_number=1,
            content="<>Text<> -> <>target<>",
        )
        divert_node = node.post_process()

        assert node.glue_before is True
        assert node.glue_after is True
        assert node.content == "Text"

        assert divert_node is not None
        assert divert_node.glue_before is False
        assert divert_node.glue_after is False
        assert divert_node.name == "<>target<>"


class TestRawKnot:
    """Test the RawKnot class"""

    def setup_method(self):
        """Reset ID counter before each test"""
        Node.reset_id_counter()

    def test_raw_knot_creation(self):
        """Test RawKnot creation"""
        header = {
            1: Node(
                node_type=NodeType.BASE,
                raw_content="Knot header",
                level=0,
                line_number=1,
                content="Knot header",
            )
        }
        stitches = {}
        stitches_info = {}

        knot = RawKnot(header=header, stitches=stitches, stitches_info=stitches_info)
        assert knot.header == header
        assert knot.stitches == stitches
        assert knot.stitches_info == stitches_info

    def test_block_name_to_id_property(self):
        """Test block_name_to_id property"""
        Node.reset_id_counter()

        stitches_node = Node(
            node_type=NodeType.STITCHES,
            raw_content="= village",
            level=0,
            line_number=1,
            name="village",
        )
        content_node = Node(
            node_type=NodeType.BASE,
            raw_content="Village content",
            level=0,
            line_number=2,
            content="Village content",
        )

        stitches = {stitches_node.item_id: {content_node.item_id: content_node}}
        stitches_info = {stitches_node.item_id: stitches_node}

        knot = RawKnot(header={}, stitches=stitches, stitches_info=stitches_info)
        name_to_id = knot.block_name_to_id
        assert "village" in name_to_id
        assert name_to_id["village"] == content_node.item_id

    def test_get_blocks(self):
        """Test get_blocks method"""
        header = {
            1: Node(
                node_type=NodeType.BASE,
                raw_content="Header",
                level=0,
                line_number=1,
                content="Header",
            )
        }
        stitches = {
            2: {
                3: Node(
                    node_type=NodeType.BASE,
                    raw_content="Stitch content",
                    level=0,
                    line_number=2,
                    content="Stitch content",
                )
            }
        }

        knot = RawKnot(header=header, stitches=stitches, stitches_info={})
        blocks = knot.get_blocks()
        assert len(blocks) == 2  # header + 1 stitch
        assert blocks[0] == header
        assert blocks[1] == stitches[2]

    def test_first_id_with_header(self):
        """Test first_id property with header"""
        node = Node(
            node_type=NodeType.BASE,
            raw_content="Header",
            level=0,
            line_number=1,
            content="Header",
        )
        header = {node.item_id: node}

        knot = RawKnot(header=header, stitches={}, stitches_info={})
        assert knot.first_id == node.item_id

    def test_first_id_without_header(self):
        """Test first_id property without header"""
        node = Node(
            node_type=NodeType.BASE,
            raw_content="Header",
            level=0,
            line_number=1,
            content="Header",
        )
        stitches = {2: {node.item_id: node}}

        knot = RawKnot(header={}, stitches=stitches, stitches_info={})
        assert knot.first_id == node.item_id

    def test_get_node(self):
        """Test get_node method"""
        Node.reset_id_counter()

        header_node = Node(
            node_type=NodeType.BASE,
            raw_content="Header",
            level=0,
            line_number=1,
            content="Header",
        )
        stitches_info_node = Node(
            node_type=NodeType.STITCHES,
            raw_content="= stitch",
            level=0,
            line_number=2,
            name="stitch",
        )
        stitch_content_node = Node(
            node_type=NodeType.BASE,
            raw_content="Stitch content",
            level=0,
            line_number=3,
            content="Stitch content",
        )

        header = {header_node.item_id: header_node}
        stitches_info = {stitches_info_node.item_id: stitches_info_node}
        stitches = {
            stitches_info_node.item_id: {
                stitch_content_node.item_id: stitch_content_node
            }
        }

        knot = RawKnot(header=header, stitches=stitches, stitches_info=stitches_info)

        assert knot.get_node(header_node.item_id) == header_node
        assert knot.get_node(stitches_info_node.item_id) == stitches_info_node
        assert knot.get_node(stitch_content_node.item_id) == stitch_content_node
        assert knot.get_node(999) is None


class TestRawStory:
    """Test the RawStory class"""

    def setup_method(self):
        """Reset ID counter before each test"""
        Node.reset_id_counter()

    def test_raw_story_creation(self):
        """Test RawStory creation"""
        header = {}
        knots = {}
        knots_info = {}

        story = RawStory(header=header, knots=knots, knots_info=knots_info)
        assert story.header == header
        assert story.knots == knots
        assert story.knots_info == knots_info

    def test_block_name_to_id_property(self):
        """Test block_name_to_id property with knots and stitches"""
        Node.reset_id_counter()

        # Create knot info node
        knot_info_node = Node(
            node_type=NodeType.KNOT,
            raw_content="== forest ==",
            level=0,
            line_number=1,
            name="forest",
        )

        # Create knot header content
        knot_header_node = Node(
            node_type=NodeType.BASE,
            raw_content="You enter the forest",
            level=0,
            line_number=2,
            content="You enter the forest",
        )

        # Create stitches
        stitches_info_node = Node(
            node_type=NodeType.STITCHES,
            raw_content="= clearing",
            level=0,
            line_number=3,
            name="clearing",
        )

        stitches_content_node = Node(
            node_type=NodeType.BASE,
            raw_content="A peaceful clearing",
            level=0,
            line_number=4,
            content="A peaceful clearing",
        )

        # Build the knot structure
        knot_header = {knot_header_node.item_id: knot_header_node}
        stitches = {
            stitches_info_node.item_id: {
                stitches_content_node.item_id: stitches_content_node
            }
        }
        stitches_info = {stitches_info_node.item_id: stitches_info_node}

        raw_knot = RawKnot(
            header=knot_header, stitches=stitches, stitches_info=stitches_info
        )

        knots = {knot_info_node.item_id: raw_knot}
        knots_info = {knot_info_node.item_id: knot_info_node}

        story = RawStory(header={}, knots=knots, knots_info=knots_info)
        name_to_id = story.block_name_to_id

        assert "forest" in name_to_id
        assert name_to_id["forest"] == knot_header_node.item_id
        assert "forest.clearing" in name_to_id
        assert name_to_id["forest.clearing"] == stitches_content_node.item_id

    def test_get_node(self):
        """Test get_node method"""
        Node.reset_id_counter()

        # Create header node
        header_node = Node(
            node_type=NodeType.BASE,
            raw_content="Story header",
            level=0,
            line_number=1,
            content="Story header",
        )

        # Create knot info node
        knot_info_node = Node(
            node_type=NodeType.KNOT,
            raw_content="== chapter1 ==",
            level=0,
            line_number=2,
            name="chapter1",
        )

        # Create knot content
        knot_content_node = Node(
            node_type=NodeType.BASE,
            raw_content="Chapter begins",
            level=0,
            line_number=3,
            content="Chapter begins",
        )

        header = {header_node.item_id: header_node}
        knots_info = {knot_info_node.item_id: knot_info_node}
        raw_knot = RawKnot(
            header={knot_content_node.item_id: knot_content_node},
            stitches={},
            stitches_info={},
        )
        knots = {knot_info_node.item_id: raw_knot}

        story = RawStory(header=header, knots=knots, knots_info=knots_info)

        assert story.get_node(header_node.item_id) == header_node
        assert story.get_node(knot_info_node.item_id) == knot_info_node
        assert story.get_node(knot_content_node.item_id) == knot_content_node
        assert story.get_node(999) is None
