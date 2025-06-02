from unittest.mock import patch

import pytest

from analink.parser.graph_story import (
    find_leaves_from_node,
    graph_to_mermaid,
    parse_story,
)
from analink.parser.node import Node, NodeType


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


class TestParseStory:
    """Test the parse_story function"""

    def setup_method(self):
        """Reset Node ID counter before each test"""
        Node.reset_id_counter()

    def test_empty_nodes(self):
        """Test with empty nodes dictionary"""
        result = parse_story({})
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

        result = parse_story(nodes)
        assert result == []  # No edges for single node

    def test_multiple_base_nodes_same_level(self):
        """Test multiple base nodes at same level"""
        node1 = Node(
            node_type=NodeType.BASE, raw_content="Base 1", level=0, line_number=1
        )
        node2 = Node(
            node_type=NodeType.BASE, raw_content="Base 2", level=0, line_number=2
        )

        nodes = {node1.item_id: node1, node2.item_id: node2}

        result = parse_story(nodes)
        assert result == []  # No connections between same-level base nodes

    def test_base_nodes_different_levels(self):
        """Test base nodes at different levels"""
        node1 = Node(
            node_type=NodeType.BASE, raw_content="Base 1", level=0, line_number=1
        )
        node2 = Node(
            node_type=NodeType.BASE, raw_content="Base 2", level=1, line_number=2
        )

        nodes = {node1.item_id: node1, node2.item_id: node2}

        result = parse_story(nodes)
        # Should connect level 0 to level 1
        assert result == [(node1.item_id, node2.item_id)]

    def test_single_choice_node(self):
        """Test with single choice node"""
        base_node = Node(
            node_type=NodeType.BASE, raw_content="Base", level=0, line_number=1
        )
        choice_node = Node(
            node_type=NodeType.CHOICE, raw_content="* Choice", level=1, line_number=2
        )

        nodes = {base_node.item_id: base_node, choice_node.item_id: choice_node}

        result = parse_story(nodes)
        assert result == [(base_node.item_id, choice_node.item_id)]

    def test_multiple_choices_same_level(self):
        """Test multiple choices at same level"""
        base_node = Node(
            node_type=NodeType.BASE, raw_content="Base", level=0, line_number=1
        )
        choice1 = Node(
            node_type=NodeType.CHOICE, raw_content="* Choice 1", level=1, line_number=2
        )
        choice2 = Node(
            node_type=NodeType.CHOICE, raw_content="* Choice 2", level=1, line_number=3
        )

        nodes = {
            base_node.item_id: base_node,
            choice1.item_id: choice1,
            choice2.item_id: choice2,
        }

        result = parse_story(nodes)
        expected = [
            (base_node.item_id, choice1.item_id),
            (base_node.item_id, choice2.item_id),
        ]
        assert result == expected

    def test_nested_choices(self):
        """Test nested choices at different levels"""
        base_node = Node(
            node_type=NodeType.BASE, raw_content="Base", level=0, line_number=1
        )
        choice1 = Node(
            node_type=NodeType.CHOICE, raw_content="* Choice 1", level=1, line_number=2
        )
        choice2 = Node(
            node_type=NodeType.CHOICE,
            raw_content="** Nested choice",
            level=2,
            line_number=3,
        )

        nodes = {
            base_node.item_id: base_node,
            choice1.item_id: choice1,
            choice2.item_id: choice2,
        }

        result = parse_story(nodes)
        expected = [
            (base_node.item_id, choice1.item_id),
            (choice1.item_id, choice2.item_id),
        ]
        assert result == expected

    def test_gather_node_simple(self):
        """Test simple gather node"""
        choice1 = Node(
            node_type=NodeType.CHOICE, raw_content="* Choice 1", level=1, line_number=1
        )
        choice2 = Node(
            node_type=NodeType.CHOICE, raw_content="* Choice 2", level=1, line_number=2
        )
        gather = Node(
            node_type=NodeType.GATHER, raw_content="- Gather", level=1, line_number=3
        )

        nodes = {
            choice1.item_id: choice1,
            choice2.item_id: choice2,
            gather.item_id: gather,
        }

        with patch(
            "analink.parser.graph_story.find_leaves_from_node"
        ) as mock_find_leaves:
            # Mock the find_leaves_from_node function
            mock_find_leaves.side_effect = lambda node_id, edges: [
                node_id
            ]  # Each node is its own leaf

            result = parse_story(nodes)

            # Should have edges from both choices to gather
            expected_edges = [
                (choice1.item_id, gather.item_id),
                (choice2.item_id, gather.item_id),
            ]
            assert all(edge in result for edge in expected_edges)

    def test_gather_node_with_complex_structure(self):
        """Test gather node with complex preceding structure"""
        base_node = Node(
            node_type=NodeType.BASE, raw_content="Base", level=0, line_number=1
        )
        choice1 = Node(
            node_type=NodeType.CHOICE, raw_content="* Choice 1", level=1, line_number=2
        )
        choice2 = Node(
            node_type=NodeType.CHOICE, raw_content="* Choice 2", level=1, line_number=3
        )
        nested_choice = Node(
            node_type=NodeType.CHOICE, raw_content="** Nested", level=2, line_number=4
        )
        gather = Node(
            node_type=NodeType.GATHER, raw_content="- Gather", level=1, line_number=5
        )

        nodes = {
            base_node.item_id: base_node,
            choice1.item_id: choice1,
            choice2.item_id: choice2,
            nested_choice.item_id: nested_choice,
            gather.item_id: gather,
        }

        # Mock find_leaves_from_node to return expected leaves
        with patch(
            "analink.parser.graph_story.find_leaves_from_node"
        ) as mock_find_leaves:

            def mock_leaves(node_id, edges):
                # choice1 leads to nested_choice, so nested_choice is the leaf
                if node_id == choice1.item_id:
                    return [nested_choice.item_id]
                # choice2 is its own leaf
                elif node_id == choice2.item_id:
                    return [choice2.item_id]
                else:
                    return [node_id]

            mock_find_leaves.side_effect = mock_leaves

            result = parse_story(nodes)

            # Verify that gather gets connected to leaves
            gather_edges = [
                (nested_choice.item_id, gather.item_id),
                (choice2.item_id, gather.item_id),
            ]
            assert all(edge in result for edge in gather_edges)

    def test_gather_node_level_manipulation(self):
        """Test that gather node properly manipulates level structure"""
        choice1 = Node(
            node_type=NodeType.CHOICE, raw_content="* Choice 1", level=1, line_number=1
        )
        gather = Node(
            node_type=NodeType.GATHER, raw_content="- Gather", level=1, line_number=2
        )
        next_choice = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Next choice",
            level=1,
            line_number=3,
        )

        nodes = {
            choice1.item_id: choice1,
            gather.item_id: gather,
            next_choice.item_id: next_choice,
        }

        with patch(
            "analink.parser.graph_story.find_leaves_from_node"
        ) as mock_find_leaves:
            mock_find_leaves.return_value = [choice1.item_id]

            result = parse_story(nodes)

            # Should connect choice1 to gather, and gather should be at level 0 for next connections
            assert (choice1.item_id, gather.item_id) in result
            assert (gather.item_id, next_choice.item_id) in result

    def test_verbose_parameter(self):
        """Test that verbose parameter doesn't affect functionality"""
        node = Node(node_type=NodeType.BASE, raw_content="Base", level=0, line_number=1)
        nodes = {node.item_id: node}

        result_false = parse_story(nodes, verbose=False)
        result_true = parse_story(nodes, verbose=True)

        assert result_false == result_true

    def test_max_level_tracking(self):
        """Test that max_level_seen is properly tracked"""
        node1 = Node(
            node_type=NodeType.BASE, raw_content="Base", level=0, line_number=1
        )
        node2 = Node(
            node_type=NodeType.CHOICE, raw_content="* Choice", level=3, line_number=2
        )
        node3 = Node(
            node_type=NodeType.CHOICE, raw_content="* Choice", level=1, line_number=3
        )

        nodes = {node1.item_id: node1, node2.item_id: node2, node3.item_id: node3}

        # This should work without errors (max_level_seen should be 3)
        result = parse_story(nodes)
        assert isinstance(result, list)

    def test_choice_without_previous_level(self):
        """Test choice node without previous level"""
        choice = Node(
            node_type=NodeType.CHOICE, raw_content="* Choice", level=1, line_number=1
        )
        nodes = {choice.item_id: choice}

        result = parse_story(nodes)
        assert result == []  # No previous level to connect to

    def test_base_without_previous_level(self):
        """Test base node without previous level"""
        base = Node(node_type=NodeType.BASE, raw_content="Base", level=1, line_number=1)
        nodes = {base.item_id: base}

        result = parse_story(nodes)
        assert result == []  # No previous level to connect to

    def test_gather_without_same_level_nodes(self):
        """Test gather node when no nodes exist at the same level"""
        gather = Node(
            node_type=NodeType.GATHER, raw_content="- Gather", level=1, line_number=1
        )
        nodes = {gather.item_id: gather}

        result = parse_story(nodes)
        assert result == []


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

    def test_single_edge(self):
        """Test with two nodes and single edge"""
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
        lines = result.split("\n")

        assert f'    {node1.item_id}["Node 1"]' in lines
        assert f'    {node2.item_id}["Node 2"]' in lines
        assert f"    {node1.item_id} --> {node2.item_id}" in lines

    def test_multiple_edges(self):
        """Test with multiple edges"""
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
        node3 = Node(
            node_type=NodeType.BASE,
            raw_content="Node 3",
            level=0,
            line_number=3,
            content="Node 3",
        )

        nodes = {node1.item_id: node1, node2.item_id: node2, node3.item_id: node3}
        edges = [(node1.item_id, node2.item_id), (node2.item_id, node3.item_id)]

        result = graph_to_mermaid(nodes, edges)
        lines = result.split("\n")

        assert f"    {node1.item_id} --> {node2.item_id}" in lines
        assert f"    {node2.item_id} --> {node3.item_id}" in lines

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

    def test_content_with_quotes(self):
        """Test content containing quotes"""
        node = Node(
            node_type=NodeType.BASE,
            raw_content='Content with "quotes"',
            level=0,
            line_number=1,
            content='Content with "quotes"',
        )
        nodes = {node.item_id: node}

        result = graph_to_mermaid(nodes, [])

        # Quotes should be replaced with single quotes
        assert f"    {node.item_id}[\"Content with 'quotes'\"]" in result

    def test_content_with_newlines(self):
        """Test content containing newlines"""
        node = Node(
            node_type=NodeType.BASE,
            raw_content="Line 1\nLine 2",
            level=0,
            line_number=1,
            content="Line 1\nLine 2",
        )
        nodes = {node.item_id: node}

        result = graph_to_mermaid(nodes, [])

        # Newlines should be replaced with spaces
        assert f'    {node.item_id}["Line 1 Line 2"]' in result

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
        expected_content = long_content[:47] + "..."
        assert f'    {node.item_id}["{expected_content}"]' in result

    def test_content_exactly_50_chars(self):
        """Test content that is exactly 50 characters"""
        content_50 = "x" * 50  # Exactly 50 characters
        node = Node(
            node_type=NodeType.BASE,
            raw_content=content_50,
            level=0,
            line_number=1,
            content=content_50,
        )
        nodes = {node.item_id: node}

        result = graph_to_mermaid(nodes, [])

        # Should not be truncated
        assert f'    {node.item_id}["{content_50}"]' in result

    def test_content_51_chars(self):
        """Test content that is 51 characters (should be truncated)"""
        content_51 = "x" * 51  # 51 characters
        node = Node(
            node_type=NodeType.BASE,
            raw_content=content_51,
            level=0,
            line_number=1,
            content=content_51,
        )
        nodes = {node.item_id: node}

        result = graph_to_mermaid(nodes, [])

        # Should be truncated
        expected_content = content_51[:47] + "..."
        assert f'    {node.item_id}["{expected_content}"]' in result

    def test_node_with_none_content(self):
        """Test node with None content"""
        node = Node(
            node_type=NodeType.BASE,
            raw_content="Raw content",
            level=0,
            line_number=1,
            content=None,
        )
        nodes = {node.item_id: node}

        result = graph_to_mermaid(nodes, [])

        # Should display empty string for None content
        assert f'    {node.item_id}[""]' in result

    def test_complex_mermaid_structure(self):
        """Test complex graph structure"""
        nodes = {}
        edges = []

        # Create multiple nodes
        for i in range(1, 4):
            node = Node(
                node_type=NodeType.BASE,
                raw_content=f"Node {i}",
                level=0,
                line_number=i,
                content=f"Node {i}",
            )
            nodes[node.item_id] = node
            if i > 1:
                prev_id = list(nodes.keys())[i - 2]
                edges.append((prev_id, node.item_id))

        result = graph_to_mermaid(nodes, edges)
        lines = result.split("\n")

        # Check structure
        assert lines[0] == "```mermaid"
        assert lines[1] == "flowchart TD"
        assert lines[-1] == "```"

        # Check all nodes are present
        for node_id in nodes.keys():
            node_line = f'    {node_id}["Node {list(nodes.keys()).index(node_id) + 1}"]'
            assert any(node_line in line for line in lines)

        # Check all edges are present
        for source, target in edges:
            edge_line = f"    {source} --> {target}"
            assert edge_line in lines


class TestIntegration:
    """Integration tests combining multiple functions"""

    def setup_method(self):
        """Reset Node ID counter before each test"""
        Node.reset_id_counter()

    def test_full_workflow(self):
        """Test complete workflow from nodes to mermaid"""
        # Create a story structure
        base = Node(
            node_type=NodeType.BASE,
            raw_content="Start",
            level=0,
            line_number=1,
            content="Start",
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
        gather = Node(
            node_type=NodeType.GATHER,
            raw_content="- Gather",
            level=1,
            line_number=4,
            content="Gather",
        )

        nodes = {
            base.item_id: base,
            choice1.item_id: choice1,
            choice2.item_id: choice2,
            gather.item_id: gather,
        }

        # Parse the story to get edges
        edges = parse_story(nodes)

        # Generate mermaid diagram
        mermaid = graph_to_mermaid(nodes, edges)

        # Verify the mermaid contains expected elements
        assert "```mermaid" in mermaid
        assert "flowchart TD" in mermaid
        assert "Start" in mermaid
        assert "Choice 1" in mermaid
        assert "Choice 2" in mermaid
        assert "Gather" in mermaid
        assert "-->" in mermaid

    def test_find_leaves_integration_with_parse_story(self):
        """Test find_leaves_from_node integration with parse_story"""
        # Create a branching structure
        choice1 = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Choice 1",
            level=1,
            line_number=1,
            content="Choice 1",
        )
        choice2 = Node(
            node_type=NodeType.CHOICE,
            raw_content="** Nested 1",
            level=2,
            line_number=2,
            content="Nested 1",
        )
        choice3 = Node(
            node_type=NodeType.CHOICE,
            raw_content="** Nested 2",
            level=2,
            line_number=3,
            content="Nested 2",
        )
        choice4 = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Choice 2",
            level=1,
            line_number=4,
            content="Choice 2",
        )
        gather = Node(
            node_type=NodeType.GATHER,
            raw_content="- Gather",
            level=1,
            line_number=5,
            content="Gather",
        )

        nodes = {
            choice1.item_id: choice1,
            choice2.item_id: choice2,
            choice3.item_id: choice3,
            choice4.item_id: choice4,
            gather.item_id: gather,
        }

        # Parse story
        edges = parse_story(nodes)

        # Test find_leaves_from_node with the generated edges
        leaves_from_choice1 = find_leaves_from_node(choice1.item_id, edges)

        # Should find the nested choices as leaves
        assert gather.item_id in leaves_from_choice1


# Fixtures for common test data
@pytest.fixture
def sample_story_nodes():
    """Sample story nodes for testing"""
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
    )
    choice2 = Node(
        node_type=NodeType.CHOICE,
        raw_content="* Go right",
        level=1,
        line_number=3,
        content="Go right",
    )
    gather = Node(
        node_type=NodeType.GATHER,
        raw_content="- You continue",
        level=1,
        line_number=4,
        content="You continue",
    )

    return {
        base.item_id: base,
        choice1.item_id: choice1,
        choice2.item_id: choice2,
        gather.item_id: gather,
    }


@pytest.fixture
def complex_story_nodes():
    """Complex story structure for testing"""
    Node.reset_id_counter()

    nodes = {}

    # Level 0 - Base content
    base = Node(
        node_type=NodeType.BASE,
        raw_content="Story start",
        level=0,
        line_number=1,
        content="Story start",
    )
    nodes[base.item_id] = base

    # Level 1 - Main choices
    choice1 = Node(
        node_type=NodeType.CHOICE,
        raw_content="* Path A",
        level=1,
        line_number=2,
        content="Path A",
    )
    choice2 = Node(
        node_type=NodeType.CHOICE,
        raw_content="* Path B",
        level=1,
        line_number=3,
        content="Path B",
    )
    nodes[choice1.item_id] = choice1
    nodes[choice2.item_id] = choice2

    # Level 2 - Nested choices
    nested1 = Node(
        node_type=NodeType.CHOICE,
        raw_content="** Nested A1",
        level=2,
        line_number=4,
        content="Nested A1",
    )
    nested2 = Node(
        node_type=NodeType.CHOICE,
        raw_content="** Nested A2",
        level=2,
        line_number=5,
        content="Nested A2",
    )
    nodes[nested1.item_id] = nested1
    nodes[nested2.item_id] = nested2

    # Level 1 - Gather
    gather = Node(
        node_type=NodeType.GATHER,
        raw_content="- Convergence",
        level=1,
        line_number=6,
        content="Convergence",
    )
    nodes[gather.item_id] = gather

    return nodes
