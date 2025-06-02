from unittest.mock import Mock, patch

import pytest

# Mock the imported classes since we don't have the actual implementations
from analink.parser.condition import ConditionType, UnaryCondition
from analink.parser.line import InkLine, InkLineType
from analink.parser.status import ContainerStatus

# Assuming your module is named analink.parser.tool.py and the imports work
from analink.parser.tool import (
    ParseState,
    fake_condition,
    parse_story,
    parse_story_recursive,
)


class TestParseState:
    """Test the ParseState helper class"""

    def test_init(self):
        """Test ParseState initialization"""
        lines = [Mock(spec=InkLine), Mock(spec=InkLine)]
        state = ParseState(lines)

        assert state.lines == lines
        assert state.index == 0

    def test_current_line(self):
        """Test getting current line"""
        line1 = Mock(spec=InkLine)
        line2 = Mock(spec=InkLine)
        lines = [line1, line2]
        state = ParseState(lines)

        assert state.current_line() == line1
        state.index = 1
        assert state.current_line() == line2

    def test_transform_consumed_lines(self):
        """Test transforming current line to BASE type"""
        # Create a mock line with all required attributes
        original_line = Mock(spec=InkLine)
        original_line.level = 2
        original_line.text = "Some text"
        original_line.raw_line = "* Some text"
        original_line.line_number = 5

        lines = [original_line]
        state = ParseState(lines)

        # Transform the line
        state.transform_consumed_lines()

        # Check that the line was replaced with a BASE type line
        transformed_line = state.lines[0]
        assert transformed_line.level == 2
        assert transformed_line.line_type == InkLineType.BASE
        assert transformed_line.text == "Some text"
        assert transformed_line.raw_line == "* Some text"
        assert transformed_line.line_number == 5

    def test_advance(self):
        """Test advancing the index"""
        lines = [Mock(spec=InkLine), Mock(spec=InkLine)]
        state = ParseState(lines)

        assert state.index == 0
        state.advance()
        assert state.index == 1
        state.advance()
        assert state.index == 2

    def test_has_more_true(self):
        """Test has_more returns True when there are more lines"""
        lines = [Mock(spec=InkLine), Mock(spec=InkLine)]
        state = ParseState(lines)

        assert state.has_more() is True
        state.advance()  # index = 1
        assert state.has_more() is True

    def test_has_more_false(self):
        """Test has_more returns False when no more lines"""
        lines = [Mock(spec=InkLine)]
        state = ParseState(lines)

        state.advance()  # index = 1, beyond list
        assert state.has_more() is False

    def test_has_more_empty_lines(self):
        """Test has_more with empty lines list"""
        state = ParseState([])
        assert state.has_more() is False


class TestParseStoryRecursive:
    """Test the recursive story parsing function"""

    def create_mock_line(self, line_type, level=0, text="test"):
        """Helper to create mock InkLine"""
        line = Mock(spec=InkLine)
        line.line_type = line_type
        line.level = level
        line.text = text
        line.raw_line = f"raw_{text}"
        line.line_number = 1
        return line

    @patch("analink.parser.tool.Container")
    def test_empty_lines(self, mock_container_class):
        """Test parsing with empty lines"""
        mock_container = Mock()
        mock_container_class.return_value = mock_container

        state = ParseState([])
        result = parse_story_recursive(state, 0)

        # Should create container with empty content and no children
        mock_container_class.assert_called_once_with(content="", children=[])
        assert result == mock_container

    @patch("analink.parser.tool.Container")
    def test_single_base_line(self, mock_container_class):
        """Test parsing single base content line"""
        mock_container = Mock()
        mock_container_class.return_value = mock_container

        base_line = self.create_mock_line(InkLineType.BASE, text="Base content")
        state = ParseState([base_line])

        result = parse_story_recursive(state, 0)

        mock_container_class.assert_called_once_with(
            content="Base content", children=[]
        )
        assert result == mock_container
        assert state.index == 1  # Should have advanced

    @patch("analink.parser.tool.Container")
    def test_choice_equal_to_target_level(self, mock_container_class):
        """Test choice with level equal to target level (should break)"""
        mock_container = Mock()
        mock_container_class.return_value = mock_container

        choice_line = self.create_mock_line(
            InkLineType.CHOICE, level=1, text="Choice text"
        )
        state = ParseState([choice_line])

        _ = parse_story_recursive(state, 1)  # target_level = 1, choice_level = 1

        mock_container_class.assert_called_once_with(content="", children=[])
        assert state.index == 0  # Should not have advanced (broke out of loop)

    @patch("analink.parser.tool.Container")
    def test_choice_less_than_target_level(self, mock_container_class):
        """Test choice with level less than target level (should break)"""
        mock_container = Mock()
        mock_container_class.return_value = mock_container

        choice_line = self.create_mock_line(
            InkLineType.CHOICE, level=0, text="Choice text"
        )
        state = ParseState([choice_line])

        _ = parse_story_recursive(state, 2)  # target_level = 2, choice_level = 0

        mock_container_class.assert_called_once_with(content="", children=[])
        assert state.index == 0  # Should not have advanced

    @patch("analink.parser.tool.Container")
    def test_gather_equal_to_target_level(self, mock_container_class):
        """Test gather with level equal to target level (should break)"""
        mock_container = Mock()
        mock_container_class.return_value = mock_container

        gather_line = self.create_mock_line(
            InkLineType.GATHER, level=1, text="Gather text"
        )
        state = ParseState([gather_line])

        _ = parse_story_recursive(state, 1)  # target_level = 1, gather_level = 1

        mock_container_class.assert_called_once_with(content="", children=[])
        assert state.index == 0  # Should not have advanced

    @patch("analink.parser.tool.Container")
    def test_gather_less_than_target_level(self, mock_container_class):
        """Test gather with level less than target level (should break)"""
        mock_container = Mock()
        mock_container_class.return_value = mock_container

        gather_line = self.create_mock_line(
            InkLineType.GATHER, level=0, text="Gather text"
        )
        state = ParseState([gather_line])

        _ = parse_story_recursive(state, 2)  # target_level = 2, gather_level = 0

        mock_container_class.assert_called_once_with(content="", children=[])
        assert state.index == 0  # Should not have advanced

    @patch("analink.parser.tool.Container")
    def test_verbose_parameter(self, mock_container_class):
        """Test that verbose parameter is accepted (even if not used in current implementation)"""
        mock_container = Mock()
        mock_container_class.return_value = mock_container

        state = ParseState([])
        result = parse_story_recursive(state, 0, verbose=True)

        assert result == mock_container

    @patch("analink.parser.tool.Container")
    def test_mixed_content_sequence(self, mock_container_class):
        """Test parsing sequence with mixed content types"""
        mock_main_container = Mock()
        mock_child_container = Mock()
        mock_container_class.side_effect = [mock_child_container, mock_main_container]

        base_line = self.create_mock_line(InkLineType.BASE, text="Base content")
        choice_line = self.create_mock_line(InkLineType.CHOICE, level=1, text="Choice")

        state = ParseState([base_line, choice_line])

        _ = parse_story_recursive(state, 0)

        # Should process base content first, then choice
        expected_children = [(fake_condition, mock_child_container)]
        mock_container_class.assert_called_with(
            content="Base content", children=expected_children
        )


class TestParseStory:
    """Test the main parse_story entry point"""

    @patch("analink.parser.tool.ParseState")
    @patch("analink.parser.tool.parse_story_recursive")
    def test_parse_story_calls_recursive(
        self, mock_parse_recursive, mock_parse_state_class
    ):
        """Test that parse_story creates ParseState and calls recursive function"""
        mock_state = Mock()
        mock_parse_state_class.return_value = mock_state
        mock_result = Mock()
        mock_parse_recursive.return_value = mock_result

        lines = [Mock(spec=InkLine), Mock(spec=InkLine)]
        result = parse_story(lines)

        # Should create ParseState with the lines
        mock_parse_state_class.assert_called_once_with(lines)

        # Should call recursive parser with state and target_level=0
        mock_parse_recursive.assert_called_once_with(mock_state, 0)

        # Should return the result from recursive parser
        assert result == mock_result

    @patch("analink.parser.tool.parse_story_recursive")
    def test_parse_story_empty_lines(self, mock_parse_recursive):
        """Test parse_story with empty lines list"""
        mock_result = Mock()
        mock_parse_recursive.return_value = mock_result

        result = parse_story([])

        # Should still call the recursive parser
        mock_parse_recursive.assert_called_once()
        assert result == mock_result

    @patch("analink.parser.tool.parse_story_recursive")
    def test_parse_story_single_line(self, mock_parse_recursive):
        """Test parse_story with single line"""
        mock_result = Mock()
        mock_parse_recursive.return_value = mock_result

        line = Mock(spec=InkLine)
        _ = parse_story([line])

        mock_parse_recursive.assert_called_once()
        # Check that ParseState was created with the correct line
        call_args = mock_parse_recursive.call_args[0]
        state = call_args[0]
        assert state.lines == [line]
        assert state.index == 0


class TestFakeCondition:
    """Test the fake_condition global variable"""

    def test_fake_condition_exists(self):
        """Test that fake_condition is properly defined"""
        assert fake_condition is not None
        assert isinstance(fake_condition, UnaryCondition)
        assert fake_condition.condition_type == ConditionType.STATUS_EQUALS
        assert fake_condition.expected_value == ContainerStatus.ACTIVE


class TestIntegration:
    """Integration tests combining multiple components"""

    def create_mock_line(self, line_type, level=0, text="test"):
        """Helper to create mock InkLine"""
        line = Mock(spec=InkLine)
        line.line_type = line_type
        line.level = level
        line.text = text
        line.raw_line = f"raw_{text}"
        line.line_number = 1
        return line

    @patch("analink.parser.tool.Container")
    def test_complex_story_structure(self, mock_container_class):
        """Test parsing a complex story structure"""
        # Create a sequence that exercises multiple code paths
        lines = [
            self.create_mock_line(InkLineType.BASE, text="Story intro"),
            self.create_mock_line(InkLineType.CHOICE, level=1, text="Choice 1"),
            self.create_mock_line(InkLineType.CHOICE, level=2, text="Nested choice"),
            self.create_mock_line(InkLineType.BASE, text="More content"),
        ]

        # Set up mock returns
        mock_containers = [Mock() for _ in range(4)]  # Need multiple containers
        mock_container_class.side_effect = mock_containers

        result = parse_story(lines)

        # Should have processed all lines and created containers
        assert mock_container_class.call_count >= 1
        assert result is not None

    @patch("analink.parser.tool.Container")
    @patch("builtins.print")
    def test_gather_processing_with_debug_output(
        self, mock_print, mock_container_class
    ):
        """Test gather processing that triggers debug print statements"""
        mock_container = Mock()
        mock_container.content = "test content"
        mock_container_class.return_value = mock_container

        lines = [
            self.create_mock_line(InkLineType.CHOICE, level=1, text="Choice"),
            self.create_mock_line(InkLineType.GATHER, level=2, text="Gather"),
        ]

        result = parse_story(lines)

        # Should have triggered the debug print statements in gather processing
        assert mock_print.called
        assert result is not None

    def test_parse_state_integration_with_real_operations(self):
        """Test ParseState with real operations (no mocking of ParseState itself)"""
        line1 = self.create_mock_line(InkLineType.BASE, text="Line 1")
        line2 = self.create_mock_line(InkLineType.CHOICE, level=1, text="Line 2")

        state = ParseState([line1, line2])

        # Test the sequence of operations
        assert state.has_more() is True
        assert state.current_line() == line1

        state.advance()
        assert state.current_line() == line2

        # Transform the current line
        _ = line2.line_type
        state.transform_consumed_lines()
        assert state.current_line().line_type == InkLineType.BASE
        assert state.current_line().text == "Line 2"

        state.advance()
        assert state.has_more() is False


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_parse_state_current_line_out_of_bounds(self):
        """Test accessing current_line when index is out of bounds"""
        state = ParseState([Mock(spec=InkLine)])
        state.index = 1  # Beyond the list

        with pytest.raises(IndexError):
            state.current_line()

    def test_parse_state_transform_out_of_bounds(self):
        """Test transform_consumed_lines when index is out of bounds"""
        state = ParseState([Mock(spec=InkLine)])
        state.index = 1  # Beyond the list

        with pytest.raises(IndexError):
            state.transform_consumed_lines()

    @patch("analink.parser.tool.Container")
    def test_recursive_parser_handles_state_exhaustion(self, mock_container_class):
        """Test recursive parser when state is exhausted during processing"""
        mock_container = Mock()
        mock_container_class.return_value = mock_container

        state = ParseState([])
        state.index = 10  # Way beyond any possible lines

        result = parse_story_recursive(state, 0)

        # Should still create a container with empty content
        mock_container_class.assert_called_once_with(content="", children=[])
        assert result == mock_container
