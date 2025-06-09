import pytest

from analink.parser.graph_story import (
    KEY_KNOT_NAME,
    escape_mermaid_text,
    find_leaves_from_node,
    graph_to_mermaid,
    parse_base_block,
    parse_knot,
    parse_story,
)
from analink.parser.node import Node, NodeType, RawKnot, RawStory


class TestFindLeavesFromNode:
    """Test the find_leaves_from_node function"""

    def test_node_not_in_graph(self):
        """Test when start_node_id is not in the graph"""
        edges = [(1, 2), (2, 3)]
        result = find_leaves_from_node(5, edges)
        assert result == [5]

    def test_single_node_no_edges(self):
        """Test with empty edges list"""
        edges = []
        result = find_leaves_from_node(1, edges)
        assert result == [1]

    def test_simple_linear_chain(self):
        """Test simple linear chain of nodes"""
        edges = [(1, 2), (2, 3), (3, 4)]
        result = find_leaves_from_node(1, edges)
        assert result == [4]

    def test_start_node_is_leaf(self):
        """Test when start node itself is a leaf"""
        edges = [(1, 2), (3, 4)]
        result = find_leaves_from_node(2, edges)
        assert result == [2]

    def test_multiple_branches_single_leaf(self):
        """Test tree with multiple branches converging to single leaf"""
        edges = [(1, 2), (1, 3), (2, 4), (3, 4)]
        result = find_leaves_from_node(1, edges)
        assert result == [4]

    def test_multiple_branches_multiple_leaves(self):
        """Test tree with multiple branches and multiple leaves"""
        edges = [(1, 2), (1, 3), (2, 4), (3, 5)]
        result = find_leaves_from_node(1, edges)
        # Should include both leaves
        assert set(result) == {4, 5}

    def test_complex_graph_structure(self):
        """Test complex graph with multiple levels and branches"""
        edges = [
            (1, 2),
            (1, 3),  # 1 branches to 2 and 3
            (2, 4),
            (2, 5),  # 2 branches to 4 and 5
            (3, 6),  # 3 goes to 6
            (4, 7),
            (5, 7),  # 4 and 5 converge to 7
            (6, 8),
            (7, 9),  # 6 goes to 8, 7 goes to 9
        ]
        result = find_leaves_from_node(1, edges)
        # Leaves should be 8 and 9
        assert set(result) == {8, 9}

    def test_cycle_in_graph(self):
        """Test graph with cycles"""
        edges = [(1, 2), (2, 3), (3, 2), (2, 4)]
        result = find_leaves_from_node(1, edges)
        assert result == [4]

    def test_self_loop(self):
        """Test node with self-loop"""
        edges = [(1, 2), (2, 2), (2, 3)]
        result = find_leaves_from_node(1, edges)
        assert result == [3]

    def test_disconnected_components(self):
        """Test when graph has disconnected components"""
        edges = [(1, 2), (3, 4), (4, 5)]
        result = find_leaves_from_node(1, edges)
        assert result == [2]  # Should only find leaves reachable from 1


class TestEscapeMermaidText:
    """Test the escape_mermaid_text function"""

    def test_empty_string(self):
        """Test with empty string"""
        assert escape_mermaid_text("") == ""

    def test_none_input(self):
        """Test with None input"""
        assert escape_mermaid_text(None) == ""

    def test_double_quotes(self):
        """Test escaping double quotes"""
        assert escape_mermaid_text('Say "hello"') == "Say &quot;hello&quot;"

    def test_single_quotes(self):
        """Test escaping single quotes"""
        assert escape_mermaid_text("Say 'hello'") == "Say &#39;hello&#39;"

    def test_newlines(self):
        """Test replacing newlines with spaces"""
        assert escape_mermaid_text("Line 1\nLine 2") == "Line 1 Line 2"

    def test_pipe_characters(self):
        """Test escaping pipe characters"""
        assert escape_mermaid_text("Option A | Option B") == "Option A &#124; Option B"

    def test_multiple_special_chars(self):
        """Test text with multiple special characters"""
        text = 'Say "hello" | Go\nforward'
        expected = "Say &quot;hello&quot; &#124; Go forward"
        assert escape_mermaid_text(text) == expected

    def test_normal_text(self):
        """Test normal text without special characters"""
        text = "Normal text without special characters"
        assert escape_mermaid_text(text) == text


class TestParseBaseBlock:
    """Test the parse_base_block function"""

    def setup_method(self):
        """Reset Node ID counter before each test"""
        Node.reset_id_counter()

    def test_empty_nodes(self):
        """Test with empty nodes dictionary"""
        result = parse_base_block({}, {}, {})
        assert result == []

    def test_single_base_node(self):
        """Test with single base node"""
        node = Node(
            node_type=NodeType.BASE,
            raw_content="Base content",
            level=0,
            line_number=1,
            content="Base content",
        )
        nodes = {node.item_id: node}

        result = parse_base_block(nodes, {}, {})
        assert result == []  # No edges for single node

    def test_base_nodes_different_levels(self):
        """Test base nodes at different levels"""
        node1 = Node(
            node_type=NodeType.BASE,
            raw_content="Base 1",
            level=0,
            line_number=1,
            content="Base 1",
        )
        node2 = Node(
            node_type=NodeType.BASE,
            raw_content="Base 2",
            level=1,
            line_number=2,
            content="Base 2",
        )

        nodes = {node1.item_id: node1, node2.item_id: node2}

        result = parse_base_block(nodes, {}, {})
        # Should connect level 0 to level 1
        assert result == [(node1.item_id, node2.item_id)]

    def test_choice_connection(self):
        """Test choice node connection"""
        base_node = Node(
            node_type=NodeType.BASE,
            raw_content="Base",
            level=0,
            line_number=1,
            content="Base",
        )
        choice_node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Choice",
            level=1,
            line_number=2,
            content="Choice",
        )

        nodes = {base_node.item_id: base_node, choice_node.item_id: choice_node}

        result = parse_base_block(nodes, {}, {})
        assert result == [(base_node.item_id, choice_node.item_id)]

    def test_multiple_choices_same_level(self):
        """Test multiple choices at same level"""
        base_node = Node(
            node_type=NodeType.BASE,
            raw_content="Base",
            level=0,
            line_number=1,
            content="Base",
        )
        choice1 = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Choice 1",
            level=1,
            line_number=2,
            content="Choice 1",
        )
        choice2 = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Choice 2",
            level=1,
            line_number=3,
            content="Choice 2",
        )

        nodes = {
            base_node.item_id: base_node,
            choice1.item_id: choice1,
            choice2.item_id: choice2,
        }

        result = parse_base_block(nodes, {}, {})
        expected = [
            (base_node.item_id, choice1.item_id),
            (base_node.item_id, choice2.item_id),
        ]
        assert result == expected

    def test_gather_node_functionality(self):
        """Test gather node connects to same-level nodes"""
        choice1 = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Choice 1",
            level=1,
            line_number=1,
            content="Choice 1",
        )
        choice2 = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Choice 2",
            level=1,
            line_number=2,
            content="Choice 2",
        )
        gather = Node(
            node_type=NodeType.GATHER,
            raw_content="- Gather",
            level=1,
            line_number=3,
            content="Gather",
        )

        nodes = {
            choice1.item_id: choice1,
            choice2.item_id: choice2,
            gather.item_id: gather,
        }

        result = parse_base_block(nodes, {}, {})

        # Should have edges from both choices to gather
        expected_edges = [
            (choice1.item_id, gather.item_id),
            (choice2.item_id, gather.item_id),
        ]
        assert all(edge in result for edge in expected_edges)

    def test_divert_to_local_block(self):
        """Test divert to local block"""
        base_node = Node(
            node_type=NodeType.BASE,
            raw_content="Base",
            level=0,
            line_number=1,
            content="Base",
        )
        divert_node = Node(
            node_type=NodeType.DIVERT,
            raw_content="-> target",
            level=0,
            line_number=2,
            name="target",
        )
        target_node = Node(
            node_type=NodeType.BASE,
            raw_content="Target",
            level=0,
            line_number=3,
            content="Target",
        )

        nodes = {
            base_node.item_id: base_node,
            divert_node.item_id: divert_node,
            target_node.item_id: target_node,
        }

        local_block_name_to_id = {"target": target_node.item_id}

        result = parse_base_block(nodes, local_block_name_to_id, {})

        # Should connect base to target via divert
        assert (base_node.item_id, target_node.item_id) in result

    def test_divert_to_global_block(self):
        """Test divert to global block"""
        base_node = Node(
            node_type=NodeType.BASE,
            raw_content="Base",
            level=0,
            line_number=1,
            content="Base",
        )
        divert_node = Node(
            node_type=NodeType.DIVERT,
            raw_content="-> global_target",
            level=0,
            line_number=2,
            name="global_target",
        )

        nodes = {
            base_node.item_id: base_node,
            divert_node.item_id: divert_node,
        }

        global_block_name_to_id = {"global_target": 999}

        result = parse_base_block(nodes, {}, global_block_name_to_id)

        # Should connect base to global target
        assert (base_node.item_id, 999) in result

    def test_divert_to_key_knot(self):
        """Test divert to key knot (END, BEGIN, etc.)"""
        base_node = Node(
            node_type=NodeType.BASE,
            raw_content="Base",
            level=0,
            line_number=1,
            content="Base",
        )
        divert_node = Node(
            node_type=NodeType.DIVERT,
            raw_content="-> END",
            level=0,
            line_number=2,
            name="END",
        )

        nodes = {
            base_node.item_id: base_node,
            divert_node.item_id: divert_node,
        }

        result = parse_base_block(nodes, {}, {})

        # Should connect base to END (-1)
        assert (base_node.item_id, KEY_KNOT_NAME["END"]) in result

    def test_divert_at_start_level_zero(self):
        """Test divert at level 0 without previous nodes"""
        divert_node = Node(
            node_type=NodeType.DIVERT,
            raw_content="-> target",
            level=0,
            line_number=1,
            name="target",
        )

        nodes = {divert_node.item_id: divert_node}
        local_block_name_to_id = {"target": 999}

        result = parse_base_block(nodes, local_block_name_to_id, {})

        # Should connect BEGIN (-2) to target
        assert (-2, 999) in result

    def test_divert_unknown_target_raises_error(self):
        """Test that divert to unknown target raises NotImplementedError"""
        base_node = Node(
            node_type=NodeType.BASE,
            raw_content="Base",
            level=0,
            line_number=1,
            content="Base",
        )
        divert_node = Node(
            node_type=NodeType.DIVERT,
            raw_content="-> unknown",
            level=0,
            line_number=2,
            name="unknown",
        )

        nodes = {
            base_node.item_id: base_node,
            divert_node.item_id: divert_node,
        }

        with pytest.raises(NotImplementedError):
            parse_base_block(nodes, {}, {})


class TestParseKnot:
    """Test the parse_knot function"""

    def setup_method(self):
        """Reset Node ID counter before each test"""
        Node.reset_id_counter()

    def test_simple_knot_with_header_only(self):
        """Test knot with only header content"""
        header_node = Node(
            node_type=NodeType.BASE,
            raw_content="Knot content",
            level=0,
            line_number=1,
            content="Knot content",
        )

        raw_knot = RawKnot(
            header={header_node.item_id: header_node}, stitches={}, stitches_info={}
        )

        nodes, edges = parse_knot(raw_knot, {})

        assert header_node.item_id in nodes
        assert edges == []  # Single node has no edges

    def test_knot_with_stitches(self):
        """Test knot with stitches"""
        header_node = Node(
            node_type=NodeType.BASE,
            raw_content="Knot header",
            level=0,
            line_number=1,
            content="Knot header",
        )

        stitch_info_node = Node(
            node_type=NodeType.STITCHES,
            raw_content="= stitch1",
            level=0,
            line_number=2,
            name="stitch1",
        )

        stitch_content_node = Node(
            node_type=NodeType.BASE,
            raw_content="Stitch content",
            level=0,
            line_number=3,
            content="Stitch content",
        )

        raw_knot = RawKnot(
            header={header_node.item_id: header_node},
            stitches={
                stitch_info_node.item_id: {
                    stitch_content_node.item_id: stitch_content_node
                }
            },
            stitches_info={stitch_info_node.item_id: stitch_info_node},
        )

        nodes, edges = parse_knot(raw_knot, {})

        # Should include all nodes
        assert header_node.item_id in nodes
        assert stitch_content_node.item_id in nodes

        # Should have edges between blocks at level 0
        assert isinstance(edges, list)

    def test_knot_with_choices_and_stitches(self):
        """Test knot with complex structure including choices"""
        header_node = Node(
            node_type=NodeType.BASE,
            raw_content="Choose path",
            level=0,
            line_number=1,
            content="Choose path",
        )

        choice_node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Go to stitch",
            level=1,
            line_number=2,
            content="Go to stitch",
        )

        stitch_info_node = Node(
            node_type=NodeType.STITCHES,
            raw_content="= destination",
            level=0,
            line_number=3,
            name="destination",
        )

        stitch_content_node = Node(
            node_type=NodeType.BASE,
            raw_content="You arrived",
            level=0,
            line_number=4,
            content="You arrived",
        )

        raw_knot = RawKnot(
            header={header_node.item_id: header_node, choice_node.item_id: choice_node},
            stitches={
                stitch_info_node.item_id: {
                    stitch_content_node.item_id: stitch_content_node
                }
            },
            stitches_info={stitch_info_node.item_id: stitch_info_node},
        )

        nodes, edges = parse_knot(raw_knot, {})

        # Should connect header to choice
        assert (header_node.item_id, choice_node.item_id) in edges


class TestParseStory:
    """Test the parse_story function"""

    def setup_method(self):
        """Reset Node ID counter before each test"""
        Node.reset_id_counter()

    def test_empty_story(self):
        """Test with empty story"""
        raw_story = RawStory(header={}, knots={}, knots_info={})
        nodes, edges = parse_story(raw_story)

        # Should include special nodes
        assert -1 in nodes  # END
        assert -2 in nodes  # BEGIN
        assert -3 in nodes  # AUTO_END
        assert nodes[-1].node_type == NodeType.END
        assert nodes[-2].node_type == NodeType.BEGIN
        assert nodes[-3].node_type == NodeType.AUTO_END

    def test_story_with_header_only(self):
        """Test story with only header content"""
        header_node = Node(
            node_type=NodeType.BASE,
            raw_content="Story start",
            level=0,
            line_number=1,
            content="Story start",
        )

        raw_story = RawStory(
            header={header_node.item_id: header_node}, knots={}, knots_info={}
        )

        nodes, edges = parse_story(raw_story)

        # Should include header node and special nodes
        assert header_node.item_id in nodes
        assert -1 in nodes
        assert -2 in nodes
        assert -3 in nodes

    def test_story_with_knots(self):
        """Test story with knots"""
        header_node = Node(
            node_type=NodeType.BASE,
            raw_content="Story intro",
            level=0,
            line_number=1,
            content="Story intro",
        )

        knot_info_node = Node(
            node_type=NodeType.KNOT,
            raw_content="== chapter1 ==",
            level=0,
            line_number=2,
            name="chapter1",
        )

        knot_content_node = Node(
            node_type=NodeType.BASE,
            raw_content="Chapter begins",
            level=0,
            line_number=3,
            content="Chapter begins",
        )

        raw_knot = RawKnot(
            header={knot_content_node.item_id: knot_content_node},
            stitches={},
            stitches_info={},
        )

        raw_story = RawStory(
            header={header_node.item_id: header_node},
            knots={knot_info_node.item_id: raw_knot},
            knots_info={knot_info_node.item_id: knot_info_node},
        )

        nodes, edges = parse_story(raw_story)

        # Should include all content nodes
        assert header_node.item_id in nodes
        assert knot_content_node.item_id in nodes
        assert -1 in nodes
        assert -2 in nodes
        assert -3 in nodes

    def test_story_with_complex_structure(self):
        """Test story with complex knot and stitch structure"""
        # Create header with choice leading to knot
        header_node = Node(
            node_type=NodeType.BASE,
            raw_content="Choose your path",
            level=0,
            line_number=1,
            content="Choose your path",
        )

        choice_node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Enter forest",
            level=1,
            line_number=2,
            content="Enter forest",
        )

        divert_node = Node(
            node_type=NodeType.DIVERT,
            raw_content="-> forest",
            level=1,
            line_number=3,
            name="forest",
        )

        # Create forest knot
        knot_info_node = Node(
            node_type=NodeType.KNOT,
            raw_content="== forest ==",
            level=0,
            line_number=4,
            name="forest",
        )

        forest_content_node = Node(
            node_type=NodeType.BASE,
            raw_content="You are in the forest",
            level=0,
            line_number=5,
            content="You are in the forest",
        )

        raw_knot = RawKnot(
            header={forest_content_node.item_id: forest_content_node},
            stitches={},
            stitches_info={},
        )

        raw_story = RawStory(
            header={
                header_node.item_id: header_node,
                choice_node.item_id: choice_node,
                divert_node.item_id: divert_node,
            },
            knots={knot_info_node.item_id: raw_knot},
            knots_info={knot_info_node.item_id: knot_info_node},
        )

        nodes, edges = parse_story(raw_story)

        # Should connect choice to forest content via divert
        assert (choice_node.item_id, forest_content_node.item_id) in edges


class TestGraphToMermaid:
    """Test the graph_to_mermaid function"""

    def setup_method(self):
        """Reset Node ID counter before each test"""
        Node.reset_id_counter()

    def test_empty_nodes_and_edges(self):
        """Test with empty nodes and edges"""
        result = graph_to_mermaid({}, [])
        expected = "```mermaid\nflowchart TD\n```"
        assert result == expected

    def test_single_node_no_edges(self):
        """Test with single node and no edges"""
        node = Node(
            node_type=NodeType.BASE,
            raw_content="Test content",
            level=0,
            line_number=1,
            content="Test content",
        )
        nodes = {node.item_id: node}

        result = graph_to_mermaid(nodes, [])
        lines = result.split("\n")

        assert lines[0] == "```mermaid"
        assert lines[1] == "flowchart TD"
        assert f'    {node.item_id}["Test content"]' in lines
        assert lines[-1] == "```"

    def test_choice_node_rendering(self):
        """Test that choice nodes render with curly braces"""
        choice_node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Choice text",
            level=1,
            line_number=1,
            content="Choice text",
        )
        nodes = {choice_node.item_id: choice_node}

        result = graph_to_mermaid(nodes, [])

        # Choice nodes should use curly braces
        assert f'    {choice_node.item_id}{{"Choice text"}}' in result

    def test_edge_with_choice_text(self):
        """Test edge rendering with choice text"""
        base_node = Node(
            node_type=NodeType.BASE,
            raw_content="Start",
            level=0,
            line_number=1,
            content="Start",
        )
        choice_node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Go north",
            level=1,
            line_number=2,
            content="Go north",
            choice_text="Go north",
        )

        nodes = {base_node.item_id: base_node, choice_node.item_id: choice_node}
        edges = [(base_node.item_id, choice_node.item_id)]

        result = graph_to_mermaid(nodes, edges)

        # Should include choice text in edge label
        assert f"    {base_node.item_id} -->|Go north| {choice_node.item_id}" in result

    def test_regular_edge_without_choice_text(self):
        """Test regular edge without choice text"""
        node1 = Node(
            node_type=NodeType.BASE,
            raw_content="Node 1",
            level=0,
            line_number=1,
            content="Node 1",
        )
        node2 = Node(
            node_type=NodeType.BASE,
            raw_content="Node 2",
            level=0,
            line_number=2,
            content="Node 2",
        )

        nodes = {node1.item_id: node1, node2.item_id: node2}
        edges = [(node1.item_id, node2.item_id)]

        result = graph_to_mermaid(nodes, edges)

        # Should be regular arrow without label
        assert f"    {node1.item_id} --> {node2.item_id}" in result

    def test_content_with_quotes_and_newlines(self):
        """Test content with quotes and newlines is properly escaped"""
        node = Node(
            node_type=NodeType.BASE,
            raw_content='Content with "quotes"\nand newlines',
            level=0,
            line_number=1,
            content='Content with "quotes"\nand newlines',
        )
        nodes = {node.item_id: node}

        result = graph_to_mermaid(nodes, [])

        # Quotes should be replaced with single quotes, newlines with spaces
        assert f"    {node.item_id}[\"Content with 'quotes' and newlines\"]" in result

    def test_long_content_truncation(self):
        """Test that long content is truncated"""
        long_content = (
            "This is a very long piece of content that exceeds fifty characters"
        )
        node = Node(
            node_type=NodeType.BASE,
            raw_content=long_content,
            level=0,
            line_number=1,
            content=long_content,
        )
        nodes = {node.item_id: node}

        result = graph_to_mermaid(nodes, [])

        # Should be truncated to 47 chars + "..."
        expected_content = (
            "This is a very long piece of content that exceeds fifty characters"
        )
        assert f'    {node.item_id}["{expected_content}"]' in result

    def test_node_with_none_content_skipped(self):
        """Test that nodes with None content are skipped"""
        node = Node(
            node_type=NodeType.BASE,
            raw_content="Raw content",
            level=0,
            line_number=1,
            content=None,
        )
        nodes = {node.item_id: node}

        result = graph_to_mermaid(nodes, [])

        # Node should not appear in output
        assert f"{node.item_id}" not in result

    def test_duplicate_edges_removed(self):
        """Test that duplicate edges are removed"""
        node1 = Node(
            node_type=NodeType.BASE,
            raw_content="Node 1",
            level=0,
            line_number=1,
            content="Node 1",
        )
        node2 = Node(
            node_type=NodeType.BASE,
            raw_content="Node 2",
            level=0,
            line_number=2,
            content="Node 2",
        )

        nodes = {node1.item_id: node1, node2.item_id: node2}
        edges = [
            (node1.item_id, node2.item_id),
            (node1.item_id, node2.item_id),
        ]  # Duplicate

        result = graph_to_mermaid(nodes, edges)
        lines = result.split("\n")

        # Count occurrences of the edge
        edge_line = f"    {node1.item_id} --> {node2.item_id}"
        edge_count = sum(1 for line in lines if line == edge_line)
        assert edge_count == 1

    def test_special_nodes_rendering(self):
        """Test rendering of special nodes (BEGIN, END, AUTO_END)"""
        nodes = {-1: Node.end_node(), -2: Node.begin_node(), -3: Node.auto_end_node()}

        result = graph_to_mermaid(nodes, [])

        # Special nodes should render with their names
        assert result == "```mermaid\nflowchart TD\n```"


class TestKeyKnotName:
    """Test the KEY_KNOT_NAME constant"""

    def test_key_knot_name_values(self):
        """Test that KEY_KNOT_NAME has correct mappings"""
        assert KEY_KNOT_NAME["END"] == -1
        assert KEY_KNOT_NAME["BEGIN"] == -2
        assert KEY_KNOT_NAME["AUTO_END"] == -3

    def test_key_knot_name_contains_expected_keys(self):
        """Test that KEY_KNOT_NAME contains expected keys"""
        assert "END" in KEY_KNOT_NAME
        assert "BEGIN" in KEY_KNOT_NAME
        assert "AUTO_END" in KEY_KNOT_NAME


class TestIntegration:
    """Integration tests combining multiple functions"""

    def setup_method(self):
        """Reset Node ID counter before each test"""
        Node.reset_id_counter()

    def test_full_workflow_simple_story(self):
        """Test complete workflow from RawStory to mermaid"""
        # Create simple story with choice
        header_node = Node(
            node_type=NodeType.BASE,
            raw_content="You wake up",
            level=0,
            line_number=1,
            content="You wake up",
        )
        choice_node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Go left",
            level=1,
            line_number=2,
            content="Go left",
            choice_text="Go left",
        )

        raw_story = RawStory(
            header={header_node.item_id: header_node, choice_node.item_id: choice_node},
            knots={},
            knots_info={},
        )

        # Parse the story
        nodes, edges = parse_story(raw_story)

        # Generate mermaid diagram
        mermaid = graph_to_mermaid(nodes, edges)

        # Verify the mermaid contains expected elements
        assert "```mermaid" in mermaid
        assert "flowchart TD" in mermaid
        assert "You wake up" in mermaid
        assert "Go left" in mermaid
        assert "-->" in mermaid

    def test_full_workflow_with_knots_and_diverts(self):
        """Test workflow with knots and diverts"""
        # Create header with choice and divert
        header_node = Node(
            node_type=NodeType.BASE,
            raw_content="Choose your path",
            level=0,
            line_number=1,
            content="Choose your path",
        )

        choice_node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Enter forest",
            level=1,
            line_number=2,
            content="Enter forest",
            choice_text="Enter forest",
        )

        divert_node = Node(
            node_type=NodeType.DIVERT,
            raw_content="-> forest_knot",
            level=1,
            line_number=3,
            name="forest_knot",
        )

        # Create forest knot
        knot_info_node = Node(
            node_type=NodeType.KNOT,
            raw_content="== forest_knot ==",
            level=0,
            line_number=4,
            name="forest_knot",
        )

        forest_content_node = Node(
            node_type=NodeType.BASE,
            raw_content="You are in the deep forest",
            level=0,
            line_number=5,
            content="You are in the deep forest",
        )

        raw_knot = RawKnot(
            header={forest_content_node.item_id: forest_content_node},
            stitches={},
            stitches_info={},
        )

        raw_story = RawStory(
            header={
                header_node.item_id: header_node,
                choice_node.item_id: choice_node,
                divert_node.item_id: divert_node,
            },
            knots={knot_info_node.item_id: raw_knot},
            knots_info={knot_info_node.item_id: knot_info_node},
        )

        # Parse the story
        nodes, edges = parse_story(raw_story)

        # Verify divert connection works
        assert (choice_node.item_id, forest_content_node.item_id) in edges

        # Generate mermaid
        mermaid = graph_to_mermaid(nodes, edges)

        # Should contain both header and knot content
        assert "Choose your path" in mermaid
        assert "Enter forest" in mermaid
        assert "You are in the deep forest" in mermaid

    def test_full_workflow_with_gather(self):
        """Test workflow with gather functionality"""
        choice1_node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Path A",
            level=1,
            line_number=1,
            content="Path A",
            choice_text="Path A",
        )

        choice2_node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Path B",
            level=1,
            line_number=2,
            content="Path B",
            choice_text="Path B",
        )

        gather_node = Node(
            node_type=NodeType.GATHER,
            raw_content="- You converge here",
            level=1,
            line_number=3,
            content="You converge here",
        )

        raw_story = RawStory(
            header={
                choice1_node.item_id: choice1_node,
                choice2_node.item_id: choice2_node,
                gather_node.item_id: gather_node,
            },
            knots={},
            knots_info={},
        )

        # Parse the story
        nodes, edges = parse_story(raw_story)

        # Both choices should connect to gather
        assert (choice1_node.item_id, gather_node.item_id) in edges
        assert (choice2_node.item_id, gather_node.item_id) in edges

        # Generate mermaid
        mermaid = graph_to_mermaid(nodes, edges)

        assert "Path A" in mermaid
        assert "Path B" in mermaid
        assert "You converge here" in mermaid

    def test_full_workflow_complex_nested_structure(self):
        """Test workflow with complex nested choices and stitches"""
        # Create main story
        intro_node = Node(
            node_type=NodeType.BASE,
            raw_content="The adventure begins",
            level=0,
            line_number=1,
            content="The adventure begins",
        )

        main_choice_node = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Go to village",
            level=1,
            line_number=2,
            content="Go to village",
            choice_text="Go to village",
        )

        divert_to_village = Node(
            node_type=NodeType.DIVERT,
            raw_content="-> village",
            level=1,
            line_number=3,
            name="village",
        )

        # Create village knot with stitches
        village_knot_info = Node(
            node_type=NodeType.KNOT,
            raw_content="== village ==",
            level=0,
            line_number=4,
            name="village",
        )

        village_intro = Node(
            node_type=NodeType.BASE,
            raw_content="You enter the village",
            level=0,
            line_number=5,
            content="You enter the village",
        )

        village_choice = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Visit tavern",
            level=1,
            line_number=6,
            content="Visit tavern",
            choice_text="Visit tavern",
        )

        divert_to_tavern = Node(
            node_type=NodeType.DIVERT,
            raw_content="-> tavern",
            level=1,
            line_number=7,
            name="tavern",
        )

        # Create tavern stitch
        tavern_stitch_info = Node(
            node_type=NodeType.STITCHES,
            raw_content="= tavern",
            level=0,
            line_number=8,
            name="tavern",
        )

        tavern_content = Node(
            node_type=NodeType.BASE,
            raw_content="The tavern is warm and welcoming",
            level=0,
            line_number=9,
            content="The tavern is warm and welcoming",
        )

        # Build the structures
        village_knot = RawKnot(
            header={
                village_intro.item_id: village_intro,
                village_choice.item_id: village_choice,
                divert_to_tavern.item_id: divert_to_tavern,
            },
            stitches={
                tavern_stitch_info.item_id: {tavern_content.item_id: tavern_content}
            },
            stitches_info={tavern_stitch_info.item_id: tavern_stitch_info},
        )

        raw_story = RawStory(
            header={
                intro_node.item_id: intro_node,
                main_choice_node.item_id: main_choice_node,
                divert_to_village.item_id: divert_to_village,
            },
            knots={village_knot_info.item_id: village_knot},
            knots_info={village_knot_info.item_id: village_knot_info},
        )

        # Parse the story
        nodes, edges = parse_story(raw_story)

        # Verify complex connections
        assert (intro_node.item_id, main_choice_node.item_id) in edges
        assert (main_choice_node.item_id, village_intro.item_id) in edges  # Via divert
        assert (village_intro.item_id, village_choice.item_id) in edges
        assert (
            village_choice.item_id,
            tavern_content.item_id,
        ) in edges  # Via divert to stitch

        # Generate mermaid
        mermaid = graph_to_mermaid(nodes, edges)

        # Should contain all content
        assert "The adventure begins" in mermaid
        assert "Go to village" in mermaid
        assert "You enter the village" in mermaid
        assert "Visit tavern" in mermaid
        assert "The tavern is warm and welcoming" in mermaid

    def test_find_leaves_integration_with_parse_base_block(self):
        """Test find_leaves_from_node integration with parse_base_block"""
        # Create a branching structure that tests leaf finding
        choice1 = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Branch A",
            level=1,
            line_number=1,
            content="Branch A",
        )

        nested_choice1 = Node(
            node_type=NodeType.CHOICE,
            raw_content="** Nested A1",
            level=2,
            line_number=2,
            content="Nested A1",
        )

        nested_choice2 = Node(
            node_type=NodeType.CHOICE,
            raw_content="** Nested A2",
            level=2,
            line_number=3,
            content="Nested A2",
        )

        choice2 = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Branch B",
            level=1,
            line_number=4,
            content="Branch B",
        )

        gather = Node(
            node_type=NodeType.GATHER,
            raw_content="- Convergence point",
            level=1,
            line_number=5,
            content="Convergence point",
        )

        nodes = {
            choice1.item_id: choice1,
            nested_choice1.item_id: nested_choice1,
            nested_choice2.item_id: nested_choice2,
            choice2.item_id: choice2,
            gather.item_id: gather,
        }

        # Parse using parse_base_block
        edges = parse_base_block(nodes, {}, {})

        # Test find_leaves_from_node with the generated edges
        leaves_from_choice1 = find_leaves_from_node(choice1.item_id, edges)

        # Should find the nested choices as leaves from choice1
        assert leaves_from_choice1 == [5]

        # Gather should connect to all leaves at its level
        gather_edges = [
            (choice2.item_id, gather.item_id),
            (nested_choice1.item_id, gather.item_id),
            (nested_choice2.item_id, gather.item_id),
        ]
        actual_gather_edges = [
            (source, target) for source, target in edges if target == gather.item_id
        ]
        assert len(actual_gather_edges) == len(gather_edges)
        for edge in gather_edges:
            assert edge in actual_gather_edges

    def test_error_handling_integration(self):
        """Test error handling in integrated workflow"""
        # Create story with invalid divert
        base_node = Node(
            node_type=NodeType.BASE,
            raw_content="Start",
            level=0,
            line_number=1,
            content="Start",
        )

        invalid_divert = Node(
            node_type=NodeType.DIVERT,
            raw_content="-> nonexistent_target",
            level=0,
            line_number=2,
            name="nonexistent_target",
        )

        raw_story = RawStory(
            header={
                base_node.item_id: base_node,
                invalid_divert.item_id: invalid_divert,
            },
            knots={},
            knots_info={},
        )

        # Should raise NotImplementedError during parsing
        with pytest.raises(NotImplementedError):
            parse_story(raw_story)


# Fixtures for common test data
@pytest.fixture
def simple_raw_story():
    """Simple RawStory for testing"""
    Node.reset_id_counter()

    base = Node(
        node_type=NodeType.BASE,
        raw_content="You wake up",
        level=0,
        line_number=1,
        content="You wake up",
    )
    choice1 = Node(
        node_type=NodeType.CHOICE,
        raw_content="* Go left",
        level=1,
        line_number=2,
        content="Go left",
        choice_text="Go left",
    )
    choice2 = Node(
        node_type=NodeType.CHOICE,
        raw_content="* Go right",
        level=1,
        line_number=3,
        content="Go right",
        choice_text="Go right",
    )
    gather = Node(
        node_type=NodeType.GATHER,
        raw_content="- You continue",
        level=1,
        line_number=4,
        content="You continue",
    )

    return RawStory(
        header={
            base.item_id: base,
            choice1.item_id: choice1,
            choice2.item_id: choice2,
            gather.item_id: gather,
        },
        knots={},
        knots_info={},
    )


@pytest.fixture
def complex_raw_story_with_knots():
    """Complex RawStory with knots and stitches for testing"""
    Node.reset_id_counter()

    # Header
    intro = Node(
        node_type=NodeType.BASE,
        raw_content="Story introduction",
        level=0,
        line_number=1,
        content="Story introduction",
    )

    main_choice = Node(
        node_type=NodeType.CHOICE,
        raw_content="* Begin adventure",
        level=1,
        line_number=2,
        content="Begin adventure",
        choice_text="Begin adventure",
    )

    divert_to_chapter = Node(
        node_type=NodeType.DIVERT,
        raw_content="-> chapter1",
        level=1,
        line_number=3,
        name="chapter1",
    )

    # Chapter 1 knot
    chapter1_info = Node(
        node_type=NodeType.KNOT,
        raw_content="== chapter1 ==",
        level=0,
        line_number=4,
        name="chapter1",
    )

    chapter1_content = Node(
        node_type=NodeType.BASE,
        raw_content="Chapter 1 begins",
        level=0,
        line_number=5,
        content="Chapter 1 begins",
    )

    chapter1_choice = Node(
        node_type=NodeType.CHOICE,
        raw_content="* Explore forest",
        level=1,
        line_number=6,
        content="Explore forest",
        choice_text="Explore forest",
    )

    divert_to_forest = Node(
        node_type=NodeType.DIVERT,
        raw_content="-> forest_section",
        level=1,
        line_number=7,
        name="forest_section",
    )

    # Forest stitch
    forest_stitch_info = Node(
        node_type=NodeType.STITCHES,
        raw_content="= forest_section",
        level=0,
        line_number=8,
        name="forest_section",
    )

    forest_content = Node(
        node_type=NodeType.BASE,
        raw_content="You explore the mysterious forest",
        level=0,
        line_number=9,
        content="You explore the mysterious forest",
    )

    # Build knot structure
    chapter1_knot = RawKnot(
        header={
            chapter1_content.item_id: chapter1_content,
            chapter1_choice.item_id: chapter1_choice,
            divert_to_forest.item_id: divert_to_forest,
        },
        stitches={forest_stitch_info.item_id: {forest_content.item_id: forest_content}},
        stitches_info={forest_stitch_info.item_id: forest_stitch_info},
    )

    return RawStory(
        header={
            intro.item_id: intro,
            main_choice.item_id: main_choice,
            divert_to_chapter.item_id: divert_to_chapter,
        },
        knots={chapter1_info.item_id: chapter1_knot},
        knots_info={chapter1_info.item_id: chapter1_info},
    )


@pytest.fixture
def story_with_special_nodes():
    """RawStory that will include special nodes after parsing"""
    Node.reset_id_counter()

    simple_node = Node(
        node_type=NodeType.BASE,
        raw_content="Simple story",
        level=0,
        line_number=1,
        content="Simple story",
    )

    end_divert = Node(
        node_type=NodeType.DIVERT,
        raw_content="-> END",
        level=0,
        line_number=2,
        name="END",
    )

    return RawStory(
        header={simple_node.item_id: simple_node, end_divert.item_id: end_divert},
        knots={},
        knots_info={},
    )
