from analink.core.line_parser import InkLineParser, LineMerger
from analink.core.models import Node, NodeType


class TestInkLineParser:
    """Test the InkLineParser class"""

    def setup_method(self):
        """Reset ID counter before each test"""
        Node.reset_id_counter()

    def test_is_comment_or_empty_single_line_comment(self):
        """Test single line comment detection"""
        parser = InkLineParser()
        assert parser.is_comment_or_empty("// This is a comment") is True
        assert parser.is_comment_or_empty("  // This is a comment  ") is True

    def test_is_comment_or_empty_multiline_comment(self):
        """Test multiline comment detection"""
        parser = InkLineParser()
        assert parser.is_comment_or_empty("/* Start comment") is True
        assert parser.in_comment is True
        assert parser.is_comment_or_empty("Inside comment") is True
        assert parser.is_comment_or_empty("End comment */") is True
        assert parser.in_comment is False

    def test_is_comment_or_empty_regular_text(self):
        """Test regular text is not considered comment"""
        parser = InkLineParser()
        assert parser.is_comment_or_empty("Regular text") is False
        assert parser.is_comment_or_empty("Text with // inside") is False

    def test_parse_divert(self):
        """Test parsing divert lines"""
        parser = InkLineParser()
        result = parser.parse_divert("-> END", 5, 10)
        assert result is not None
        assert result.node_type == NodeType.DIVERT
        assert result.name == "END"
        assert result.level == 5
        assert result.line_number == 10

    def test_parse_divert_with_whitespace(self):
        """Test parsing divert with whitespace"""
        parser = InkLineParser()
        result = parser.parse_divert("  -> DONE  ", 3, 15)
        assert result is not None
        assert result.name == "DONE"

    def test_parse_divert_non_divert(self):
        """Test parsing non-divert line returns None"""
        parser = InkLineParser()
        result = parser.parse_divert("Regular text", 0, 1)
        assert result is None

    def test_parse_knot_or_stitches_knot(self):
        """Test parsing knot with double equals"""
        parser = InkLineParser()
        result = parser.parse_knot_or_stitches("== forest_path ==", 1)
        assert result is not None
        assert result.node_type == NodeType.KNOT
        assert result.name == "forest_path"
        assert result.level == 0

    def test_parse_knot_or_stitches_stitches(self):
        """Test parsing stitches with single equals"""
        parser = InkLineParser()
        result = parser.parse_knot_or_stitches("= village_entrance", 1)
        assert result is not None
        assert result.node_type == NodeType.STITCHES
        assert result.name == "village_entrance"
        assert result.level == 0

    def test_parse_knot_or_stitches_non_match(self):
        """Test parsing non-knot/stitches line returns None"""
        parser = InkLineParser()
        result = parser.parse_knot_or_stitches("Regular text", 1)
        assert result is None

    def test_parse_choice_or_gather_choice(self):
        """Test parsing choice line"""
        parser = InkLineParser()
        result = parser.parse_choice_or_gather("*** Deep choice", 5)
        assert result is not None
        node, level = result
        assert node.node_type == NodeType.CHOICE
        assert node.level == 3
        assert node.content == "Deep choice"
        assert level == 3

    def test_parse_choice_or_gather_gather(self):
        """Test parsing gather line"""
        parser = InkLineParser()
        result = parser.parse_choice_or_gather("-- Gather point", 8)
        assert result is not None
        node, level = result
        assert node.node_type == NodeType.GATHER
        assert node.level == 2
        assert node.content == "Gather point"
        assert level == 2

    def test_parse_choice_or_gather_non_match(self):
        """Test parsing non-choice/gather line returns None"""
        parser = InkLineParser()
        result = parser.parse_choice_or_gather("Regular text", 1)
        assert result is None

    def test_parse_line_empty(self):
        """Test parsing empty line returns None"""
        parser = InkLineParser()
        result = parser.parse_line("", 1, 0)
        assert result == (None, 0)

    def test_parse_line_comment(self):
        """Test parsing comment line returns None"""
        parser = InkLineParser()
        result = parser.parse_line("// This is a comment", 1, 0)
        assert result == (None, 0)

    def test_parse_line_divert(self):
        """Test parsing divert line"""
        parser = InkLineParser()
        result, level = parser.parse_line("-> END", 1, 2)
        assert result is not None
        assert result.node_type == NodeType.DIVERT
        assert result.name == "END"
        assert level == 2

    def test_parse_line_knot(self):
        """Test parsing knot line"""
        parser = InkLineParser()
        result, level = parser.parse_line("== forest ==", 1, 5)
        assert result is not None
        assert result.node_type == NodeType.KNOT
        assert result.name == "forest"
        assert level == 0

    def test_parse_line_choice(self):
        """Test parsing choice line"""
        parser = InkLineParser()
        result, level = parser.parse_line("* Choice text", 1, 0)
        assert result is not None
        assert result.node_type == NodeType.CHOICE
        assert result.level == 1
        assert result.content == "Choice text"
        assert level == 1

    def test_parse_line_base_content(self):
        """Test parsing base content line"""
        parser = InkLineParser()
        result, level = parser.parse_line("Regular text", 1, 3)
        assert result is not None
        assert result.node_type == NodeType.BASE
        assert result.content == "Regular text"
        assert result.level == 3
        assert level == 3


class TestLineMerger:
    """Test the LineMerger class"""

    def setup_method(self):
        """Reset ID counter before each test"""
        Node.reset_id_counter()

    def test_can_merge_with_previous_base_after_choice(self):
        """Test that BASE can merge with previous CHOICE"""
        merger = LineMerger()
        choice_node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Choice",
            level=1,
            line_number=1,
            content="Choice",
        )
        merger.add_node(choice_node)

        base_node = Node(
            node_type=NodeType.BASE,
            raw_content="Continuation",
            level=1,
            line_number=2,
            content="Continuation",
        )
        assert merger.can_merge_with_previous(base_node) is True

    def test_can_merge_with_previous_base_after_gather(self):
        """Test that BASE can merge with previous GATHER"""
        merger = LineMerger()
        gather_node = Node(
            node_type=NodeType.GATHER,
            raw_content="- Gather",
            level=1,
            line_number=1,
            content="Gather",
        )
        merger.add_node(gather_node)

        base_node = Node(
            node_type=NodeType.BASE,
            raw_content="Continuation",
            level=1,
            line_number=2,
            content="Continuation",
        )
        assert merger.can_merge_with_previous(base_node) is True

    def test_can_merge_with_previous_base_after_base(self):
        """Test that BASE can merge with previous BASE"""
        merger = LineMerger()
        first_base = Node(
            node_type=NodeType.BASE,
            raw_content="First",
            level=0,
            line_number=1,
            content="First",
        )
        merger.add_node(first_base)

        second_base = Node(
            node_type=NodeType.BASE,
            raw_content="Second",
            level=0,
            line_number=2,
            content="Second",
        )
        assert merger.can_merge_with_previous(second_base) is True

    def test_cannot_merge_non_base_node(self):
        """Test that non-BASE nodes cannot merge"""
        merger = LineMerger()
        choice_node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Choice",
            level=1,
            line_number=1,
            content="Choice",
        )
        assert merger.can_merge_with_previous(choice_node) is False

    def test_cannot_merge_without_previous(self):
        """Test that nodes cannot merge without previous node"""
        merger = LineMerger()
        base_node = Node(
            node_type=NodeType.BASE,
            raw_content="Base",
            level=0,
            line_number=1,
            content="Base",
        )
        assert merger.can_merge_with_previous(base_node) is False

    def test_merge_with_previous(self):
        """Test merging nodes"""
        merger = LineMerger()
        choice_node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Choice",
            level=1,
            line_number=1,
            content="Choice",
        )
        merger.add_node(choice_node)

        base_node = Node(
            node_type=NodeType.BASE,
            raw_content="Continuation",
            level=1,
            line_number=2,
            content="Continuation",
        )
        merged = merger.merge_with_previous(base_node)

        assert merged.node_type == NodeType.CHOICE
        assert merged.content == "Choice Continuation"
        assert merged.raw_content == "* Choice\nContinuation"
        assert merged.line_number == 1

    def test_add_node_without_merge(self):
        """Test adding node that doesn't merge"""
        merger = LineMerger()
        choice_node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Choice",
            level=1,
            line_number=1,
            content="Choice",
        )
        merger.add_node(choice_node)

        lines = merger.get_lines()
        assert len(lines) == 1
        assert choice_node.item_id in lines

    def test_add_node_with_merge(self):
        """Test adding node that merges"""
        merger = LineMerger()
        choice_node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Choice",
            level=1,
            line_number=1,
            content="Choice",
        )
        merger.add_node(choice_node)

        base_node = Node(
            node_type=NodeType.BASE,
            raw_content="Continuation",
            level=1,
            line_number=2,
            content="Continuation",
        )
        merger.add_node(base_node)

        lines = merger.get_lines()
        assert len(lines) == 1  # Should be merged into one
        merged_node = next(iter(lines.values()))
        assert merged_node.content == "Choice Continuation"

    def test_custom_separator(self):
        """Test custom separator in merging"""
        merger = LineMerger(" | ")
        choice_node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Choice",
            level=1,
            line_number=1,
            content="Choice",
        )
        merger.add_node(choice_node)

        base_node = Node(
            node_type=NodeType.BASE,
            raw_content="Continuation",
            level=1,
            line_number=2,
            content="Continuation",
        )
        merger.add_node(base_node)

        lines = merger.get_lines()
        merged_node = next(iter(lines.values()))
        assert merged_node.content == "Choice | Continuation"
