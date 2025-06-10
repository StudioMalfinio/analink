import pytest

from analink.parser.node import (
    Node,
    NodeType,
    RawKnot,
    RawStory,
    clean_lines,
    count_leading_chars,
    extract_knot_name,
    parse_node,
)


class TestExtractKnotName:
    """Test the extract_knot_name function"""

    def test_extract_double_equals(self):
        """Test extracting knot name with double equals"""
        assert extract_knot_name("== forest_path ==") == "forest_path"

    def test_extract_multiple_equals(self):
        """Test extracting with multiple equals"""
        assert extract_knot_name("=== village ===") == "village"

    def test_extract_uneven_equals(self):
        """Test extracting with uneven equals"""
        assert extract_knot_name("== castle_gate =") == "castle_gate"

    def test_extract_only_leading_equals(self):
        """Test extracting with only leading equals"""
        assert extract_knot_name("== dungeon") == "dungeon"

    def test_extract_with_spaces(self):
        """Test extracting with spaces around name"""
        assert extract_knot_name("==   mountain_peak   ==") == "mountain_peak"

    def test_extract_simple_text(self):
        """Test with text that doesn't match pattern"""
        assert extract_knot_name("simple text") == "simple text"


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


class TestCountLeadingChars:
    """Test the count_leading_chars function"""

    def test_no_leading_chars(self):
        """Test line with no leading characters"""
        count, text = count_leading_chars("hello world", "*")
        assert count == 0
        assert text == "hello world"

    def test_single_leading_char(self):
        """Test line with single leading character"""
        count, text = count_leading_chars("*hello world", "*")
        assert count == 1
        assert text == "hello world"

    def test_multiple_leading_chars(self):
        """Test line with multiple leading characters"""
        count, text = count_leading_chars("***hello world", "*")
        assert count == 3
        assert text == "hello world"

    def test_leading_chars_with_spaces(self):
        """Test line with leading characters followed by spaces"""
        count, text = count_leading_chars("*  hello world", "*")
        assert count == 1
        assert text == "hello world"

    def test_leading_chars_with_tabs(self):
        """Test line with leading characters followed by tabs"""
        count, text = count_leading_chars("*\t\thello world", "*")
        assert count == 1
        assert text == "hello world"

    def test_leading_chars_with_mixed_whitespace(self):
        """Test line with leading characters followed by mixed whitespace"""
        count, text = count_leading_chars("** \t hello world", "*")
        assert count == 2
        assert text == "hello world"

    def test_only_leading_chars(self):
        """Test line with only leading characters"""
        count, text = count_leading_chars("***", "*")
        assert count == 3
        assert text == ""

    def test_different_char(self):
        """Test with different leading character"""
        count, text = count_leading_chars("---hello", "-")
        assert count == 3
        assert text == "hello"

    def test_empty_string(self):
        """Test with empty string"""
        count, text = count_leading_chars("", "*")
        assert count == 0
        assert text == ""

    def test_only_whitespace(self):
        """Test with only whitespace"""
        count, text = count_leading_chars("   ", "*")
        assert count == 0
        assert text == ""


class TestParseNode:
    """Test the parse_node function"""

    def setup_method(self):
        """Reset ID counter before each test"""
        Node.reset_id_counter()

    def test_parse_empty_line(self):
        """Test parsing empty line returns None"""
        result = parse_node("", 1, 0)
        assert result == (None, 0)

    def test_parse_whitespace_only_line(self):
        """Test parsing whitespace-only line returns None"""
        result = parse_node("   \t  ", 1, 0)
        assert result == (None, 0)

    def test_parse_comment_line(self):
        """Test parsing comment line returns None"""
        result = parse_node("// This is a comment", 1, 0)
        assert result == (None, 0)

    def test_parse_comment_line_with_leading_whitespace(self):
        """Test parsing comment line with leading whitespace returns None"""
        result = parse_node("  // This is a comment", 1, 0)
        assert result == (None, 0)

    def test_parse_directive_line(self):
        """Test parsing directive line returns DIVERT node"""
        result, _ = parse_node("-> END", 1, 0)
        assert result is not None
        assert result.node_type == NodeType.DIVERT
        assert result.name == "END"

    def test_parse_directive_line_with_whitespace(self):
        """Test parsing directive line with whitespace"""
        result, actual_level = parse_node("  -> DONE  ", 1, 4)
        assert result is not None
        assert result.node_type == NodeType.DIVERT
        assert result.name == "DONE"
        assert actual_level == 4

    def test_parse_knot_double_equals(self):
        """Test parsing knot with double equals"""
        result, actual_level = parse_node("== forest_path ==", 1, 5)
        assert result is not None
        assert result.node_type == NodeType.KNOT
        assert result.name == "forest_path"
        assert result.level == 0
        assert actual_level == 0

    def test_parse_stitches_single_equals(self):
        """Test parsing stitches with single equals"""
        result, actual_level = parse_node("= village_entrance", 1, 5)
        assert result is not None
        assert result.node_type == NodeType.STITCHES
        assert result.name == "village_entrance"
        assert result.level == 0
        assert actual_level == 0

    def test_parse_choice_single_star(self):
        """Test parsing single star choice"""
        result, actual_level = parse_node("* This is a choice", 5, 5)

        assert result is not None
        assert result.node_type == NodeType.CHOICE
        assert result.level == 1
        assert result.content == "This is a choice"
        assert result.raw_content == "* This is a choice"
        assert result.line_number == 5
        assert actual_level == 1

    def test_parse_choice_multiple_stars(self):
        """Test parsing multiple star choice"""
        result, actual_level = parse_node("*** Deep choice", 10, 10)

        assert result is not None
        assert result.node_type == NodeType.CHOICE
        assert result.level == 3
        assert result.content == "Deep choice"
        assert result.raw_content == "*** Deep choice"
        assert result.line_number == 10
        assert actual_level == 3

    def test_parse_choice_with_whitespace(self):
        """Test parsing choice with leading/trailing whitespace"""
        result, actual_level = parse_node("  ** Choice with spaces  ", 2, 5)

        assert result is not None
        assert result.node_type == NodeType.CHOICE
        assert result.level == 2
        assert result.content == "Choice with spaces"
        assert result.raw_content == "  ** Choice with spaces  "
        assert result.line_number == 2
        assert actual_level == 2

    def test_parse_gather_single_dash(self):
        """Test parsing single dash gather"""
        result, _ = parse_node("- This is a gather", 3, 0)

        assert result is not None
        assert result.node_type == NodeType.GATHER
        assert result.level == 1
        assert result.content == "This is a gather"
        assert result.raw_content == "- This is a gather"
        assert result.line_number == 3

    def test_parse_gather_multiple_dashes(self):
        """Test parsing multiple dash gather"""
        result, actual_level = parse_node("--- Deep gather", 7, 10)

        assert result is not None
        assert result.node_type == NodeType.GATHER
        assert result.level == 3
        assert result.content == "Deep gather"
        assert result.raw_content == "--- Deep gather"
        assert result.line_number == 7
        assert actual_level == 3

    def test_parse_base_content(self):
        """Test parsing base content"""
        result, actual_level = parse_node("This is base content", 1, 10)

        assert result is not None
        assert result.node_type == NodeType.BASE
        assert result.level == 10
        assert result.content == "This is base content"
        assert result.raw_content == "This is base content"
        assert result.line_number == 1
        assert actual_level == 10

    def test_parse_base_content_with_whitespace(self):
        """Test parsing base content with whitespace"""
        result, _ = parse_node("  Base content with spaces  ", 4, 0)

        assert result is not None
        assert result.node_type == NodeType.BASE
        assert result.level == 0
        assert result.content == "Base content with spaces"
        assert result.raw_content == "  Base content with spaces  "
        assert result.line_number == 4

    def test_parse_choice_empty_content(self):
        """Test parsing choice with empty content"""
        result, _ = parse_node("*", 1, 1)

        assert result is not None
        assert result.node_type == NodeType.CHOICE
        assert result.level == 1
        assert result.content == ""
        assert result.raw_content == "*"
        assert result.line_number == 1

    def test_parse_gather_empty_content(self):
        """Test parsing gather with empty content"""
        result, _ = parse_node("-", 1, 0)

        assert result is not None
        assert result.node_type == NodeType.GATHER
        assert result.level == 1
        assert result.content == ""
        assert result.raw_content == "-"
        assert result.line_number == 1


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


class TestCleanLines:
    """Test the clean_lines function"""

    def setup_method(self):
        """Reset ID counter before each test"""
        Node.reset_id_counter()

    def test_empty_input(self):
        """Test with empty input"""
        result = clean_lines("")
        assert isinstance(result, RawStory)
        assert result.header == {}
        assert result.knots == {}
        assert result.knots_info == {}

    def test_single_base_content(self):
        """Test with single base content line"""
        ink_code = "Hello world"
        result = clean_lines(ink_code)

        assert isinstance(result, RawStory)
        assert len(result.header) == 1
        node = next(iter(result.header.values()))
        assert node.node_type == NodeType.BASE
        assert node.content == "Hello world"
        assert node.raw_content == "Hello world"
        assert node.line_number == 1
        assert node.level == 0

    def test_single_choice(self):
        """Test with single choice"""
        ink_code = "* First choice"
        result = clean_lines(ink_code)

        assert isinstance(result, RawStory)
        assert len(result.header) == 1
        node = next(iter(result.header.values()))
        assert node.node_type == NodeType.CHOICE
        assert node.content == "First choice"
        assert node.level == 1

    def test_single_gather(self):
        """Test with single gather"""
        ink_code = "- First gather"
        result = clean_lines(ink_code)

        assert isinstance(result, RawStory)
        assert len(result.header) == 1
        node = next(iter(result.header.values()))
        assert node.node_type == NodeType.GATHER
        assert node.content == "First gather"
        assert node.level == 1

    def test_choice_with_brackets_parsed(self):
        """Test that choices with brackets are properly parsed"""
        ink_code = "* [Open door] You open the door"
        result = clean_lines(ink_code)

        assert len(result.header) == 1
        node = next(iter(result.header.values()))
        assert node.node_type == NodeType.CHOICE
        assert node.choice_text == "Open door"
        assert node.content == " You open the door"

    def test_choice_with_divert(self):
        """Test choice with divert creates additional divert node"""
        ink_code = "* Go to forest -> forest_path"
        result = clean_lines(ink_code)

        assert len(result.header) == 2  # choice + divert
        nodes = list(result.header.values())

        # Find choice and divert nodes
        choice_node = next(n for n in nodes if n.node_type == NodeType.CHOICE)
        divert_node = next(n for n in nodes if n.node_type == NodeType.DIVERT)

        assert choice_node.content == "Go to forest"
        assert divert_node.name == "forest_path"

    def test_knot_structure(self):
        """Test parsing with knots"""
        ink_code = """Opening text
== forest ==
You enter the forest.
* Look around
* Walk deeper"""

        result = clean_lines(ink_code)

        assert len(result.header) == 1  # opening text
        assert len(result.knots_info) == 1  # forest knot info
        assert len(result.knots) == 1  # forest knot

        # Check header
        header_node = next(iter(result.header.values()))
        assert header_node.content == "Opening text"

        # Check knot info
        knot_info = next(iter(result.knots_info.values()))
        assert knot_info.node_type == NodeType.KNOT
        assert knot_info.name == "forest"

        # Check knot content
        knot = next(iter(result.knots.values()))
        assert len(knot.header) == 3  # "You enter..." + 2 choices

    def test_stitches_structure(self):
        """Test parsing with stitches"""
        ink_code = """== main_knot ==
Knot header text
= stitch_one
Stitch one content
= stitch_two
Stitch two content"""

        result = clean_lines(ink_code)

        assert len(result.knots_info) == 1
        knot = next(iter(result.knots.values()))

        assert len(knot.header) == 1  # knot header text
        assert len(knot.stitches_info) == 2  # two stitches
        assert len(knot.stitches) == 2  # two stitch content blocks

        # Check stitches names
        stitch_names = [stitch.name for stitch in knot.stitches_info.values()]
        assert "stitch_one" in stitch_names
        assert "stitch_two" in stitch_names

    def test_consecutive_base_content_merge_in_choice_gather(self):
        """Test that consecutive base content merges with choice/gather"""
        ink_code = """* First choice
  Choice continuation
- Gather point
  Gather continuation"""

        result = clean_lines(ink_code)

        nodes = list(result.header.values())
        choice_node = next(n for n in nodes if n.node_type == NodeType.CHOICE)
        gather_node = next(n for n in nodes if n.node_type == NodeType.GATHER)

        assert "First choice Choice continuation" in choice_node.content
        assert "Gather point Gather continuation" in gather_node.content

    def test_skip_comments_and_directives(self):
        """Test that comments and directives are skipped"""
        ink_code = """First line
// This is a comment
-> SOME_DIRECTIVE
Second line"""

        result = clean_lines(ink_code)

        # Should have base content + divert node
        assert len(result.header) == 3
        nodes = list(result.header.values())

        base_node = next(n for n in nodes if n.node_type == NodeType.BASE)
        divert_node = next(n for n in nodes if n.node_type == NodeType.DIVERT)

        assert "First line" in base_node.content
        assert divert_node.name == "SOME_DIRECTIVE"

    def test_complex_ink_structure(self):
        """Test complex Ink structure with various elements"""
        ink_code = """Opening text
More opening text

== forest_chapter ==
You enter a dark forest.

= clearing
* [Look around] You see a peaceful clearing.
* [Listen carefully] You hear birds singing.

= deep_woods  
- You venture deeper into the woods.
  The path becomes unclear.

== village_chapter ==
You arrive at a small village."""

        result = clean_lines(ink_code)

        # Check header
        assert len(result.header) == 1
        header_node = next(iter(result.header.values()))
        assert "Opening text More opening text" in header_node.content

        # Check knots
        assert len(result.knots_info) == 2
        knot_names = [knot.name for knot in result.knots_info.values()]
        assert "forest_chapter" in knot_names
        assert "village_chapter" in knot_names

        # Check forest knot structure
        forest_knot_id = next(
            knot_id
            for knot_id, knot_info in result.knots_info.items()
            if knot_info.name == "forest_chapter"
        )
        forest_knot = result.knots[forest_knot_id]

        # Should have knot header + 2 stitches
        assert len(forest_knot.header) == 1
        assert len(forest_knot.stitches_info) == 2

        stitch_names = [stitch.name for stitch in forest_knot.stitches_info.values()]
        assert "clearing" in stitch_names
        assert "deep_woods" in stitch_names

    def test_custom_separator(self):
        """Test base content merge with custom separator"""
        ink_code = """First line
Second line"""
        result = clean_lines(ink_code, clean_text_sep=" | ")

        node = next(iter(result.header.values()))
        assert node.content == "First line | Second line"

    def test_only_skipped_lines(self):
        """Test with only lines that should be skipped"""
        ink_code = """
// Comment 1
// Comment 2

"""
        result = clean_lines(ink_code)
        assert result.header == {}
        assert result.knots == {}
        assert result.knots_info == {}

    def test_whitespace_handling(self):
        """Test proper whitespace handling in input"""
        ink_code = "  \n  First line  \n  \n  Second line  \n  "
        result = clean_lines(ink_code)

        assert len(result.header) == 1
        node = next(iter(result.header.values()))
        assert "First line Second line" in node.content

    def test_divert_parsing(self):
        """Test that divert lines create proper DIVERT nodes"""
        ink_code = """Some content
-> END
More content"""

        result = clean_lines(ink_code)

        nodes = list(result.header.values())
        assert len(nodes) == 3

        # Should have base, divert, base
        node_types = [node.node_type for node in nodes]
        assert NodeType.BASE in node_types
        assert NodeType.DIVERT in node_types

        divert_node = next(n for n in nodes if n.node_type == NodeType.DIVERT)
        assert divert_node.name == "END"

    def test_block_name_to_id_integration(self):
        """Test block_name_to_id property with full story"""
        ink_code = """== main ==
Main content
= sub_section
Sub content"""

        result = clean_lines(ink_code)
        name_to_id = result.block_name_to_id

        assert "main" in name_to_id
        assert "main.sub_section" in name_to_id

        # Verify IDs point to correct nodes
        main_id = name_to_id["main"]
        sub_id = name_to_id["main.sub_section"]

        main_node = result.get_node(main_id)
        sub_node = result.get_node(sub_id)

        assert main_node.content == "Main content"
        assert sub_node.content == "Sub content"


class TestIntegration:
    """Integration tests to ensure all components work together"""

    def setup_method(self):
        """Reset ID counter before each test"""
        Node.reset_id_counter()

    def test_full_ink_parsing_workflow(self):
        """Test a complete Ink parsing workflow"""
        ink_code = """You wake up in a dark room.
There's a door to your left and a window to your right.

* [Open the door] -> door_path
* [Look out the window] -> window_path
- You hesitate for a moment.
  What will you choose?

== door_path ==
You open the door and step into a hallway.

== window_path ==  
You look out the window and see a garden.

// This is a comment
-> DONE"""

        result = clean_lines(ink_code)

        # Should have header, 2 knots, and divert
        assert len(result.header) > 0
        assert len(result.knots_info) == 2

        # Check knot names
        knot_names = [knot.name for knot in result.knots_info.values()]
        assert "door_path" in knot_names
        assert "window_path" in knot_names

        # Check that choices have proper divert nodes
        header_nodes = list(result.header.values())
        choice_nodes = [n for n in header_nodes if n.node_type == NodeType.CHOICE]
        divert_nodes = [n for n in header_nodes if n.node_type == NodeType.DIVERT]

        assert len(choice_nodes) == 2
        assert len(divert_nodes) >= 2  # At least choice diverts + final DONE

    def test_node_id_consistency(self):
        """Test that node IDs remain consistent throughout processing"""
        ink_code = """First
* Choice
== knot ==
Second
Third"""

        result = clean_lines(ink_code)

        # Collect all nodes
        all_nodes = []
        all_nodes.extend(result.header.values())
        all_nodes.extend(result.knots_info.values())
        for knot in result.knots.values():
            all_nodes.extend(knot.header.values())
            all_nodes.extend(knot.stitches_info.values())
            for stitch in knot.stitches.values():
                all_nodes.extend(stitch.values())

        # Check that all IDs are unique
        ids = [node.item_id for node in all_nodes]
        assert len(set(ids)) == len(ids)  # All unique

    def test_parse_choice_and_divert_integration(self):
        """Test integration of choice parsing and divert creation"""
        ink_code = "* [Take the sword] You pick up the gleaming sword. -> combat"
        result = clean_lines(ink_code)

        nodes = list(result.header.values())
        choice_node = next(n for n in nodes if n.node_type == NodeType.CHOICE)
        divert_node = next(n for n in nodes if n.node_type == NodeType.DIVERT)

        # Choice should be parsed for brackets
        assert choice_node.choice_text == "Take the sword"
        assert choice_node.content == " You pick up the gleaming sword."

        # Divert should be created
        assert divert_node.name == "combat"

    def test_complex_nesting_structure(self):
        """Test complex nested structure with multiple levels"""
        ink_code = """== prologue ==
The story begins...

= introduction
You are the hero.
* Accept the quest
** Eagerly
** Reluctantly  
* Decline the quest

= conclusion
The introduction ends.

== chapter_one ==
Chapter one begins."""

        result = clean_lines(ink_code)

        # Verify structure
        assert len(result.knots_info) == 2

        prologue_knot_id = next(
            knot_id
            for knot_id, knot_info in result.knots_info.items()
            if knot_info.name == "prologue"
        )
        prologue_knot = result.knots[prologue_knot_id]

        # Check stitches
        assert len(prologue_knot.stitches_info) == 2
        stitch_names = [stitch.name for stitch in prologue_knot.stitches_info.values()]
        assert "introduction" in stitch_names
        assert "conclusion" in stitch_names

        # Check that nested choices have proper levels
        introduction_stitch_id = next(
            stitch_id
            for stitch_id, stitch_info in prologue_knot.stitches_info.items()
            if stitch_info.name == "introduction"
        )
        introduction_nodes = list(
            prologue_knot.stitches[introduction_stitch_id].values()
        )

        choice_nodes = [n for n in introduction_nodes if n.node_type == NodeType.CHOICE]
        choice_levels = [n.level for n in choice_nodes]

        assert 1 in choice_levels  # Single star choices
        assert 2 in choice_levels  # Double star choices


# Fixtures for common test data
@pytest.fixture
def sample_ink_code():
    """Sample Ink code for testing"""
    return """Opening narrative text.
This continues the narrative.

* First choice option
* Second choice option
** Nested choice
- Gather point
  Continued gather text

Final narrative text."""


@pytest.fixture
def complex_ink_code():
    """Complex Ink code with various features"""
    return """You are standing at a crossroads.
The path splits in three directions.

// Player choices
* [Go north] You head north into the forest. -> forest
** [Follow the river] The river leads to a village.
** [Climb the mountain] The mountain path is treacherous.
* [Go east] You walk east toward the sunrise. -> eastern_path
* [Go west] You turn west toward the setting sun. -> western_path

- After making your choice, you reflect on the decision.
  The journey ahead seems uncertain.

== forest ==
You are now in the deep forest.

= river_section
The river flows peacefully here.

= mountain_section  
The mountain looms above you.

== eastern_path ==
The eastern path leads to adventure.

== western_path ==
The western path leads to mystery.

// End of section
-> DONE

Epilogue text that comes after."""


@pytest.fixture
def knot_with_stitches():
    """Ink code with knots and stitches"""
    return """== main_story ==
This is the main story beginning.

= first_section
Content of the first section.
* Choice in first section

= second_section
Content of the second section.
- Gather in second section

Final content in main story."""
