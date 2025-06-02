import pytest

from analink.parser.node import (
    Node,
    NodeType,
    clean_lines,
    count_leading_chars,
    parse_node,
)


class TestNodeType:
    """Test the NodeType enum"""

    def test_node_type_values(self):
        """Test that NodeType enum has correct values"""
        assert NodeType.CHOICE.value == "choice"
        assert NodeType.GATHER.value == "gather"
        assert NodeType.BASE.value == "base_content"

    def test_node_type_members(self):
        """Test that all expected members exist"""
        assert hasattr(NodeType, "CHOICE")
        assert hasattr(NodeType, "GATHER")
        assert hasattr(NodeType, "BASE")


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

    def test_node_creation_with_optional_fields(self):
        """Test node creation with optional fields"""
        node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Choice text",
            level=1,
            line_number=5,
            content="Choice text",
            choice_text="Choice text",
        )
        assert node.node_type == NodeType.CHOICE
        assert node.raw_content == "* Choice text"
        assert node.level == 1
        assert node.line_number == 5
        assert node.content == "Choice text"
        assert node.choice_text == "Choice text"

    def test_item_id_property(self):
        """Test that item_id returns the private _id"""
        node = Node(node_type=NodeType.BASE, raw_content="test", level=0, line_number=1)
        # The first node should have ID 1
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
        # Create a node to increment the counter
        Node(node_type=NodeType.BASE, raw_content="test", level=0, line_number=1)

        # Reset counter
        Node.reset_id_counter()

        # Next node should have ID 1
        node = Node(node_type=NodeType.BASE, raw_content="test", level=0, line_number=1)
        assert node.item_id == 1

    def test_get_next_id_class_method(self):
        """Test the _get_next_id class method"""
        # Reset to ensure predictable state
        Node.reset_id_counter()

        # Test that _get_next_id returns incremental values
        id1 = Node._get_next_id()
        id2 = Node._get_next_id()
        id3 = Node._get_next_id()

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3


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
        result = parse_node("", 1)
        assert result is None

    def test_parse_whitespace_only_line(self):
        """Test parsing whitespace-only line returns None"""
        result = parse_node("   \t  ", 1)
        assert result is None

    def test_parse_comment_line(self):
        """Test parsing comment line returns None"""
        result = parse_node("// This is a comment", 1)
        assert result is None

    def test_parse_comment_line_with_leading_whitespace(self):
        """Test parsing comment line with leading whitespace returns None"""
        result = parse_node("  // This is a comment", 1)
        assert result is None

    def test_parse_directive_line(self):
        """Test parsing directive line returns None"""
        result = parse_node("-> END", 1)
        assert result is None

    def test_parse_directive_line_with_whitespace(self):
        """Test parsing directive line with whitespace returns None"""
        result = parse_node("  -> DONE  ", 1)
        assert result is None

    def test_parse_choice_single_star(self):
        """Test parsing single star choice"""
        result = parse_node("* This is a choice", 5)

        assert result is not None
        assert result.node_type == NodeType.CHOICE
        assert result.level == 1
        assert result.content == "This is a choice"
        assert result.raw_content == "* This is a choice"
        assert result.line_number == 5

    def test_parse_choice_multiple_stars(self):
        """Test parsing multiple star choice"""
        result = parse_node("*** Deep choice", 10)

        assert result is not None
        assert result.node_type == NodeType.CHOICE
        assert result.level == 3
        assert result.content == "Deep choice"
        assert result.raw_content == "*** Deep choice"
        assert result.line_number == 10

    def test_parse_choice_with_whitespace(self):
        """Test parsing choice with leading/trailing whitespace"""
        result = parse_node("  ** Choice with spaces  ", 2)

        assert result is not None
        assert result.node_type == NodeType.CHOICE
        assert result.level == 2
        assert result.content == "Choice with spaces"
        assert result.raw_content == "  ** Choice with spaces  "
        assert result.line_number == 2

    def test_parse_gather_single_dash(self):
        """Test parsing single dash gather"""
        result = parse_node("- This is a gather", 3)

        assert result is not None
        assert result.node_type == NodeType.GATHER
        assert result.level == 1
        assert result.content == "This is a gather"
        assert result.raw_content == "- This is a gather"
        assert result.line_number == 3

    def test_parse_gather_multiple_dashes(self):
        """Test parsing multiple dash gather"""
        result = parse_node("--- Deep gather", 7)

        assert result is not None
        assert result.node_type == NodeType.GATHER
        assert result.level == 3
        assert result.content == "Deep gather"
        assert result.raw_content == "--- Deep gather"
        assert result.line_number == 7

    def test_parse_base_content(self):
        """Test parsing base content"""
        result = parse_node("This is base content", 1)

        assert result is not None
        assert result.node_type == NodeType.BASE
        assert result.level == 0
        assert result.content == "This is base content"
        assert result.raw_content == "This is base content"
        assert result.line_number == 1

    def test_parse_base_content_with_whitespace(self):
        """Test parsing base content with whitespace"""
        result = parse_node("  Base content with spaces  ", 4)

        assert result is not None
        assert result.node_type == NodeType.BASE
        assert result.level == 0
        assert result.content == "Base content with spaces"
        assert result.raw_content == "  Base content with spaces  "
        assert result.line_number == 4

    def test_parse_choice_empty_content(self):
        """Test parsing choice with empty content"""
        result = parse_node("*", 1)

        assert result is not None
        assert result.node_type == NodeType.CHOICE
        assert result.level == 1
        assert result.content == ""
        assert result.raw_content == "*"
        assert result.line_number == 1

    def test_parse_gather_empty_content(self):
        """Test parsing gather with empty content"""
        result = parse_node("-", 1)

        assert result is not None
        assert result.node_type == NodeType.GATHER
        assert result.level == 1
        assert result.content == ""
        assert result.raw_content == "-"
        assert result.line_number == 1


class TestCleanLines:
    """Test the clean_lines function"""

    def setup_method(self):
        """Reset ID counter before each test"""
        Node.reset_id_counter()

    def test_empty_input(self):
        """Test with empty input"""
        result = clean_lines("")
        assert result == {}

    def test_single_base_content(self):
        """Test with single base content line"""
        ink_code = "Hello world"
        result = clean_lines(ink_code)

        assert len(result) == 1
        node = next(iter(result.values()))
        assert node.node_type == NodeType.BASE
        assert node.content == "Hello world"
        assert node.raw_content == "Hello world"
        assert node.line_number == 1
        assert node.level == 0

    def test_single_choice(self):
        """Test with single choice"""
        ink_code = "* First choice"
        result = clean_lines(ink_code)

        assert len(result) == 1
        node = next(iter(result.values()))
        assert node.node_type == NodeType.CHOICE
        assert node.content == "First choice"
        assert node.level == 1

    def test_single_gather(self):
        """Test with single gather"""
        ink_code = "- First gather"
        result = clean_lines(ink_code)

        assert len(result) == 1
        node = next(iter(result.values()))
        assert node.node_type == NodeType.GATHER
        assert node.content == "First gather"
        assert node.level == 1

    def test_consecutive_base_content_merge(self):
        """Test that consecutive base content lines are merged"""
        ink_code = """First line
Second line
Third line"""
        result = clean_lines(ink_code)

        assert len(result) == 1
        node = next(iter(result.values()))
        assert node.node_type == NodeType.BASE
        assert node.content == "First line Second line Third line"
        assert node.raw_content == "First line\nSecond line\nThird line"
        assert node.line_number == 1  # Should keep the first line number
        assert node.level == 0

    def test_base_content_merge_custom_separator(self):
        """Test base content merge with custom separator"""
        ink_code = """First line
Second line"""
        result = clean_lines(ink_code, clean_text_sep=" | ")

        assert len(result) == 1
        node = next(iter(result.values()))
        assert node.content == "First line | Second line"

    def test_mixed_content_no_merge(self):
        """Test that non-base content doesn't merge"""
        ink_code = """Base content
* Choice
- Gather"""
        result = clean_lines(ink_code)

        assert len(result) == 3
        nodes = list(result.values())

        # Should be in order of creation
        assert nodes[0].node_type == NodeType.BASE
        assert nodes[0].content == "Base content"

        assert nodes[1].node_type == NodeType.CHOICE
        assert nodes[1].content == "Choice"

        assert nodes[2].node_type == NodeType.GATHER
        assert nodes[2].content == "Gather"

    def test_base_content_interrupted_by_choice(self):
        """Test base content merge interrupted by choice"""
        ink_code = """First base
Second base
* Choice
Third base"""
        result = clean_lines(ink_code)

        assert len(result) == 2
        nodes = list(result.values())

        # First merged base content
        assert nodes[0].node_type == NodeType.BASE
        assert nodes[0].content == "First base Second base"

        # Choice
        assert nodes[1].node_type == NodeType.CHOICE
        assert nodes[1].content == "Choice Third base"

    def test_skip_empty_lines(self):
        """Test that empty lines are skipped"""
        ink_code = """First line

Second line"""
        result = clean_lines(ink_code)

        assert len(result) == 1
        node = next(iter(result.values()))
        assert node.content == "First line Second line"

    def test_skip_comments(self):
        """Test that comment lines are skipped"""
        ink_code = """First line
// This is a comment
Second line"""
        result = clean_lines(ink_code)

        assert len(result) == 1
        node = next(iter(result.values()))
        assert node.content == "First line Second line"

    def test_skip_directives(self):
        """Test that directive lines are skipped"""
        ink_code = """First line
-> END
Second line"""
        result = clean_lines(ink_code)

        assert len(result) == 1
        node = next(iter(result.values()))
        assert node.content == "First line Second line"

    def test_complex_ink_structure(self):
        """Test complex Ink structure with various elements"""
        ink_code = """Opening text
More opening text

// Comment should be ignored
* First choice
  Choice continuation
* Second choice
- Gather point
  Gather continuation

-> END

Final text"""
        result = clean_lines(ink_code)

        assert len(result) == 4
        nodes = list(result.values())

        # Merged opening text
        assert nodes[0].node_type == NodeType.BASE
        assert nodes[0].content == "Opening text More opening text"

        # First choice with continuation
        assert nodes[1].node_type == NodeType.CHOICE
        assert nodes[1].content == "First choice Choice continuation"

        # Second choice
        assert nodes[2].node_type == NodeType.CHOICE
        assert nodes[2].content == "Second choice"

        # Gather with continuation
        assert nodes[3].node_type == NodeType.GATHER
        assert nodes[3].content == "Gather point Gather continuation Final text"

    def test_only_skipped_lines(self):
        """Test with only lines that should be skipped"""
        ink_code = """
// Comment 1
-> DONE
// Comment 2

"""
        result = clean_lines(ink_code)
        assert result == {}

    def test_whitespace_handling(self):
        """Test proper whitespace handling in input"""
        ink_code = "  \n  First line  \n  \n  Second line  \n  "
        result = clean_lines(ink_code)

        assert len(result) == 1
        node = next(iter(result.values()))
        assert node.content == "First line Second line"


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

// This is a comment
-> DONE"""

        result = clean_lines(ink_code)

        # Should have 4 nodes (merged base content, two choices, merged gather)
        assert len(result) == 4

        nodes = list(result.values())

        # Check the structure
        assert nodes[0].node_type == NodeType.BASE
        assert "You wake up" in nodes[0].content
        assert "There's a door" in nodes[0].content

        assert nodes[1].node_type == NodeType.CHOICE
        assert nodes[1].content == "[Open the door] -> door_path"
        assert nodes[1].level == 1

        assert nodes[2].node_type == NodeType.CHOICE
        assert nodes[2].content == "[Look out the window] -> window_path"
        assert nodes[2].level == 1

        assert nodes[3].node_type == NodeType.GATHER
        assert "You hesitate" in nodes[3].content
        assert "What will you choose" in nodes[3].content
        assert nodes[3].level == 1

    def test_node_id_consistency(self):
        """Test that node IDs remain consistent throughout processing"""
        ink_code = """First
* Choice
Second
Third"""

        result = clean_lines(ink_code)

        # Get the nodes in creation order
        sorted_nodes = sorted(result.items(), key=lambda x: x[0])

        # IDs should be sequential
        assert sorted_nodes[0][0] == sorted_nodes[0][1].item_id
        assert sorted_nodes[1][0] == sorted_nodes[1][1].item_id

        # And should be 1, 2 (after merging, some nodes are deleted and recreated)
        ids = [node_id for node_id, node in sorted_nodes]
        # The exact IDs depend on the merging process, but they should be unique
        assert len(set(ids)) == len(ids)  # All unique


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
* [Go north] You head north into the forest.
** [Follow the river] The river leads to a village.
** [Climb the mountain] The mountain path is treacherous.
* [Go east] You walk east toward the sunrise.
* [Go west] You turn west toward the setting sun.

- After making your choice, you reflect on the decision.
  The journey ahead seems uncertain.

// End of section
-> DONE

Epilogue text that comes after."""
