"""
Unit tests for the story engine module.
"""

from unittest.mock import Mock, mock_open, patch

import pytest

from analink.core.story_engine import StoryEngine
from analink.parser.node import Node, NodeType


class TestStoryEngine:
    """Test suite for the StoryEngine class."""

    @pytest.fixture
    def simple_story(self):
        """Simple story for basic testing."""
        return """
Hello world.
* Choice A
    Response A
* Choice B
    Response B
"""

    @pytest.fixture
    def complex_story(self):
        """Complex story with gather nodes and base content."""
        return """
Start content.
* First choice
    First response
    - Gather point
        Gather content
        * Sub choice A
            Sub response A
        * Sub choice B
            Sub response B
* Second choice
    Second response
    Base content line
    - Same gather
        Final content
"""

    @pytest.fixture
    def linear_story(self):
        """Linear story with no choices."""
        return """
Line one.
Line two.
Line three.
"""

    @pytest.fixture
    def empty_story(self):
        """Empty story for edge case testing."""
        return ""

    def test_init_basic(self, simple_story):
        """Test basic initialization."""
        engine = StoryEngine(simple_story, typing_speed=0.1)

        assert engine.typing_speed == 0.1
        assert isinstance(engine.nodes, dict)
        assert isinstance(engine.edges, list)
        assert len(engine.story_history) == 0
        assert engine.current_node_id is not None
        assert not engine.is_story_complete
        assert engine.on_content_added is None
        assert engine.on_choices_updated is None
        assert engine.on_story_complete is None

    def test_init_default_typing_speed(self, simple_story):
        """Test initialization with default typing speed."""
        engine = StoryEngine(simple_story)
        assert engine.typing_speed == 0.05

    @patch("builtins.open", new_callable=mock_open, read_data="Test story content")
    def test_from_file(self, mock_file):
        """Test creating engine from file."""
        engine = StoryEngine.from_file("test.ink", typing_speed=0.2)

        mock_file.assert_called_once_with("test.ink", "r", encoding="utf-8")
        assert engine.typing_speed == 0.2

    @patch("builtins.open", new_callable=mock_open, read_data="Test story content")
    def test_from_file_default_kwargs(self, mock_file):
        """Test creating engine from file with default parameters."""
        engine = StoryEngine.from_file("test.ink")

        mock_file.assert_called_once_with("test.ink", "r", encoding="utf-8")
        assert engine.typing_speed == 0.05

    def test_find_start_node_with_edges(self, simple_story):
        """Test finding start node when edges exist."""
        engine = StoryEngine(simple_story)
        start_node = engine._find_start_node()

        # Should find a node that has no incoming edges
        assert isinstance(start_node, int)
        assert start_node == -2

    def test_find_start_node_no_edges(self, empty_story):
        """Test finding start node when no edges exist."""
        engine = StoryEngine(empty_story)

        if engine.nodes:
            start_node = engine._find_start_node()
            assert start_node == -2
        else:
            start_node = engine._find_start_node()
            assert start_node == 1

    def test_find_start_node_no_candidates(self):
        """Test finding start node when all nodes have incoming edges."""
        engine = StoryEngine("Test")

        # Mock a scenario where all nodes have incoming edges
        engine.edges = [(1, 2), (2, 1)]  # Circular
        engine.nodes = {1: Mock(), 2: Mock()}

        start_node = engine._find_start_node()
        assert start_node == -2  # Should return first node
        assert (-2, 1) in engine.edges

    def test_start_story_with_content(self, simple_story):
        """Test starting story with initial content."""
        engine = StoryEngine(simple_story)
        content_callback = Mock()
        choices_callback = Mock()

        engine.on_content_added = content_callback
        engine.on_choices_updated = choices_callback

        engine.start_story()

        # Should have added initial content
        assert len(engine.story_history) > 0
        content_callback.assert_called()
        choices_callback.assert_called()

    def test_start_story_no_initial_content(self):
        """Test starting story with no initial content."""
        engine = StoryEngine("* Choice only")
        content_callback = Mock()
        choices_callback = Mock()

        engine.on_content_added = content_callback
        engine.on_choices_updated = choices_callback

        # Mock current node with no content
        mock_node = Mock()
        mock_node.content = None
        engine.nodes[engine.current_node_id] = mock_node

        engine.start_story()

        choices_callback.assert_called()

    def test_make_choice_valid(self, simple_story):
        """Test making a valid choice."""
        engine = StoryEngine(simple_story)
        engine.start_story()

        choices = engine.get_available_choices()
        assert len(choices) > 0

        choice = choices[0]
        result = engine.make_choice(choice)

        assert result is True
        assert choice.choice_text in str(engine.story_history)

    def test_make_choice_invalid(self, simple_story):
        """Test making an invalid choice."""
        engine = StoryEngine(simple_story)
        engine.start_story()

        # Create a fake choice node not in available choices
        fake_choice = Node(
            node_type=NodeType.CHOICE,
            raw_content="* Fake choice",
            level=1,
            line_number=999,
            content="Fake choice",
            choice_text="Fake choice",
            item_id=9999,
        )

        result = engine.make_choice(fake_choice)
        assert result is False

    def test_make_choice_story_complete(self, simple_story):
        """Test making choice when story is already complete."""
        engine = StoryEngine(simple_story)
        engine.start_story()
        engine.is_story_complete = True

        choices = engine.get_available_choices()
        if choices:
            choice = choices[0]
            result = engine.make_choice(choice)
            assert result is False

    def test_make_choice_with_content_different_from_choice_text(self, simple_story):
        """Test making choice where content differs from choice text."""
        engine = StoryEngine(simple_story)
        engine.start_story()

        choices = engine.get_available_choices()
        if choices:
            choice = choices[0]
            # Ensure choice has different content from choice text
            if choice.content == choice.choice_text:
                choice.content = "Different content"

            initial_history_length = len(engine.story_history)
            engine.make_choice(choice)

            # Should have added both choice text and content
            assert len(engine.story_history) > initial_history_length

    def test_make_choice_with_same_content_as_choice_text(self, simple_story):
        """Test making choice where content is same as choice text."""
        engine = StoryEngine(simple_story)
        engine.start_story()

        choices = engine.get_available_choices()
        if choices:
            choice = choices[0]
            # Ensure choice has same content as choice text
            choice.content = choice.choice_text

            initial_history_length = len(engine.story_history)
            engine.make_choice(choice)

            # Should not add duplicate content
            history_added = len(engine.story_history) - initial_history_length
            assert (
                history_added == 2
            )  # Only choice text should be added and the END OF STORY

    def test_make_choice_with_empty_content(self, simple_story):
        """Test making choice with empty content."""
        engine = StoryEngine(simple_story)
        engine.start_story()

        choices = engine.get_available_choices()
        if choices:
            choice = choices[0]
            choice.content = "   "  # Whitespace only

            initial_history_length = len(engine.story_history)
            engine.make_choice(choice)

            # Should not add empty content
            history_text = "\n".join(engine.story_history[initial_history_length:])
            assert "   " not in history_text

    def test_follow_story_path_to_end(self, linear_story):
        """Test following story path to completion."""
        engine = StoryEngine(linear_story)
        complete_callback = Mock()
        engine.on_story_complete = complete_callback

        engine.start_story()

        assert engine.is_story_complete
        assert "AUTO END OF STORY generated by the software" in engine.story_history
        # we did not put an end
        complete_callback.assert_called_once()

    def test_follow_story_path_infinite_loop_prevention(self):
        """Test that infinite loops are prevented."""
        engine = StoryEngine("Test content")

        # Create a circular reference
        engine.current_node_id = 1
        engine.graph.add_edge(1, 2)
        engine.graph.add_edge(2, 1)
        Node.reset_id_counter()
        # Mock nodes
        engine.nodes[1] = Node(
            node_type=NodeType.BASE,
            raw_content="Content 1",
            level=0,
            line_number=1,
            content="Content 1",
            choice_text=None,
        )
        engine.nodes[2] = Node(
            node_type=NodeType.BASE,
            raw_content="Content 2",
            level=0,
            line_number=2,
            content="Content 2",
            choice_text=None,
        )

        initial_history_length = len(engine.story_history)
        engine._follow_story_path()

        # Should not run forever
        assert len(engine.story_history) >= initial_history_length

    def test_follow_story_path_with_gather_node(self, complex_story):
        """Test following path through gather nodes."""
        engine = StoryEngine(complex_story)
        engine.start_story()

        # Find and make a choice that leads to gather
        choices = engine.get_available_choices()
        if choices:
            engine.make_choice(choices[0])

            # Should have processed gather node content
            _ = "\n".join(engine.story_history)
            # Check that gather content was added (this depends on story structure)
            assert len(engine.story_history) > 1

    def test_follow_story_path_with_base_content(self, complex_story):
        """Test following path through base content nodes."""
        engine = StoryEngine(complex_story)
        engine.start_story()

        choices = engine.get_available_choices()
        if len(choices) > 1:
            # Choose second option which should have base content
            engine.make_choice(choices[1])

            # Should have processed base content
            assert len(engine.story_history) > 1

    def test_get_next_nodes_existing(self, simple_story):
        """Test getting next nodes for existing node."""
        engine = StoryEngine(simple_story)
        engine.start_story()

        next_nodes = engine._get_next_nodes(engine.current_node_id)
        assert isinstance(next_nodes, list)

    def test_get_next_nodes_nonexistent(self, simple_story):
        """Test getting next nodes for non-existent node."""
        engine = StoryEngine(simple_story)

        next_nodes = engine._get_next_nodes(9999)
        assert next_nodes == []

    def test_get_choice_nodes(self, simple_story):
        """Test filtering choice nodes."""
        engine = StoryEngine(simple_story)
        engine.start_story()

        # Get all next nodes
        next_node_ids = engine._get_next_nodes(engine.current_node_id)
        choice_nodes = engine._get_choice_nodes(next_node_ids)

        assert isinstance(choice_nodes, list)
        for node in choice_nodes:
            assert node.node_type == NodeType.CHOICE

    def test_get_choice_nodes_mixed_types(self):
        """Test filtering choice nodes from mixed node types."""
        engine = StoryEngine("Test")
        Node.reset_id_counter()
        # Create mixed node types
        engine.nodes[1] = Node(
            node_type=NodeType.CHOICE,
            raw_content="Choice",
            level=1,
            line_number=1,
            content="Choice",
            choice_text="Choice",
        )
        engine.nodes[2] = Node(
            node_type=NodeType.BASE,
            raw_content="Base",
            level=0,
            line_number=2,
            content="Base",
            choice_text=None,
        )
        engine.nodes[3] = Node(
            node_type=NodeType.GATHER,
            raw_content="Gather",
            level=1,
            line_number=3,
            content="Gather",
            choice_text=None,
        )

        choice_nodes = engine._get_choice_nodes([1, 2, 3])

        assert len(choice_nodes) == 1
        assert choice_nodes[0].item_id == 1

    def test_get_choice_nodes_nonexistent_ids(self, simple_story):
        """Test filtering choice nodes with non-existent IDs."""
        engine = StoryEngine(simple_story)

        choice_nodes = engine._get_choice_nodes([9999, 9998])
        assert choice_nodes == []

    def test_get_available_choices(self, simple_story):
        """Test getting available choices."""
        engine = StoryEngine(simple_story)
        engine.start_story()

        choices = engine.get_available_choices()
        assert isinstance(choices, list)
        for choice in choices:
            assert isinstance(choice, Node)
            assert choice.node_type == NodeType.CHOICE

    def test_get_available_choices_story_complete(self, simple_story):
        """Test getting available choices when story is complete."""
        engine = StoryEngine(simple_story)
        engine.is_story_complete = True

        choices = engine.get_available_choices()
        assert choices == []

    def test_get_story_history(self, simple_story):
        """Test getting story history copy."""
        engine = StoryEngine(simple_story)
        engine.story_history = ["Line 1", "Line 2"]

        history = engine.get_story_history()

        assert history == ["Line 1", "Line 2"]
        assert history is not engine.story_history  # Should be a copy

        # Modifying returned history shouldn't affect original
        history.append("Line 3")
        assert len(engine.story_history) == 2

    def test_add_content(self, simple_story):
        """Test adding content with callback."""
        engine = StoryEngine(simple_story)
        callback = Mock()
        engine.on_content_added = callback

        engine._add_content("Test content")

        assert "Test content" in engine.story_history
        callback.assert_called_once_with("Test content")

    def test_add_content_no_callback(self, simple_story):
        """Test adding content without callback."""
        engine = StoryEngine(simple_story)
        engine.on_content_added = None

        engine._add_content("Test content")

        assert "Test content" in engine.story_history

    def test_notify_choices_updated(self, simple_story):
        """Test notifying choices updated with callback."""
        engine = StoryEngine(simple_story)
        engine.start_story()
        callback = Mock()
        engine.on_choices_updated = callback

        engine._notify_choices_updated()

        callback.assert_called_once()
        args = callback.call_args[0]
        assert isinstance(args[0], list)

    def test_notify_choices_updated_no_callback(self, simple_story):
        """Test notifying choices updated without callback."""
        engine = StoryEngine(simple_story)
        engine.start_story()
        engine.on_choices_updated = None

        # Should not raise exception
        engine._notify_choices_updated()

    def test_reset_story(self, simple_story):
        """Test resetting story to beginning."""
        engine = StoryEngine(simple_story)
        engine.start_story()

        # Make some progress
        choices = engine.get_available_choices()
        if choices:
            engine.make_choice(choices[0])

        original_start = engine._find_start_node()

        # Reset
        engine.reset_story()

        assert len(engine.story_history) == 0
        assert engine.current_node_id == original_start
        assert not engine.is_story_complete

    def test_get_story_stats(self, simple_story):
        """Test getting story statistics."""
        engine = StoryEngine(simple_story)
        engine.start_story()

        stats = engine.get_story_stats()

        required_keys = {
            "total_nodes",
            "total_edges",
            "current_node",
            "history_length",
            "choices_available",
            "is_complete",
        }

        assert isinstance(stats, dict)
        assert set(stats.keys()) == required_keys
        assert isinstance(stats["total_nodes"], int)
        assert isinstance(stats["total_edges"], int)
        assert isinstance(stats["current_node"], int)
        assert isinstance(stats["history_length"], int)
        assert isinstance(stats["choices_available"], int)
        assert isinstance(stats["is_complete"], bool)

    def test_get_story_stats_values(self, simple_story):
        """Test story statistics values are correct."""
        engine = StoryEngine(simple_story)
        engine.start_story()

        stats = engine.get_story_stats()

        assert stats["total_nodes"] == len(engine.nodes)
        assert stats["total_edges"] == len(engine.edges)
        assert stats["current_node"] == engine.current_node_id
        assert stats["history_length"] == len(engine.story_history)
        assert stats["choices_available"] == len(engine.get_available_choices())
        assert stats["is_complete"] == engine.is_story_complete

    def test_complete_workflow(self, simple_story):
        """Test complete workflow from start to finish."""
        engine = StoryEngine(simple_story)

        # Track all callbacks
        content_calls = []
        choice_calls = []
        complete_calls = []

        def content_callback(content):
            content_calls.append(content)

        def choices_callback(choices):
            choice_calls.append(choices)

        def complete_callback():
            complete_calls.append(True)

        engine.on_content_added = content_callback
        engine.on_choices_updated = choices_callback
        engine.on_story_complete = complete_callback

        # Start story
        engine.start_story()
        assert len(content_calls) > 0
        assert len(choice_calls) > 0

        # Make choices until story ends
        max_iterations = 10  # Prevent infinite loops in tests
        iterations = 0

        while not engine.is_story_complete and iterations < max_iterations:
            choices = engine.get_available_choices()
            if not choices:
                break

            engine.make_choice(choices[0])
            iterations += 1

        # Verify callbacks were called appropriately
        assert len(content_calls) > 0
        assert len(choice_calls) > 0

    def test_edge_case_empty_nodes(self):
        """Test edge case with empty nodes dictionary."""
        engine = StoryEngine("")
        engine.nodes = {}
        engine.edges = []

        start_node = engine._find_start_node()
        assert start_node == -2

        choices = engine.get_available_choices()
        assert choices == []

        next_nodes = engine._get_next_nodes(1)
        assert next_nodes == []

    def test_edge_case_node_without_content(self):
        """Test edge case with node that has no content."""
        engine = StoryEngine("Test")
        Node.reset_id_counter()
        # Create node without content
        mock_node = Node(
            node_type=NodeType.BASE,
            raw_content="",
            level=0,
            line_number=1,
            content=None,
            choice_text=None,
        )
        engine.nodes[1] = mock_node
        engine.current_node_id = 1
        engine._follow_story_path()

        # Should handle gracefully
        assert True  # Test passes if no exception is raised


# Integration tests for edge cases and error conditions
class TestStoryEngineIntegration:
    """Integration tests for complex scenarios."""

    def test_story_with_no_choices_ever(self):
        """Test story that never presents choices."""
        story = """
This is line one.
This is line two.
This is the end.
"""
        engine = StoryEngine(story)
        engine.start_story()

        assert engine.is_story_complete
        assert "AUTO END OF STORY generated by the software" in engine.story_history
        assert len(engine.get_available_choices()) == 0

    #     def test_story_with_immediate_choices(self):
    #         # TODO : decide what to if we meet such a case for the moment it just take the first choice and end
    #         """Test story that presents choices immediately."""
    #         story = """
    # * Immediate choice A
    # * Immediate choice B
    # """
    #         engine = StoryEngine(story)
    #         engine.start_story()

    #         assert not engine.is_story_complete
    #         choices = engine.get_available_choices()
    #         assert len(choices) >= 2

    def test_deeply_nested_story(self):
        """Test story with deep nesting levels."""
        story = """
Start
* Level 1A
    Content 1A
    * * Level 2A
        Content 2A
        * * * Level 3A
            Content 3A
        * * * Level 3B
            Content 3B
    * * Level 2B
        Content 2B
* Level 1B
    Content 1B
"""
        engine = StoryEngine(story)
        engine.start_story()

        # Navigate through nested choices
        choices = engine.get_available_choices()
        assert len(choices) >= 2

        # Make first choice
        engine.make_choice(choices[0])

        # Should have more choices available
        nested_choices = engine.get_available_choices()
        assert len(nested_choices) >= 1


if __name__ == "__main__":
    pytest.main(
        [__file__, "-v", "--cov=analink.core.story_engine", "--cov-report=html"]
    )
