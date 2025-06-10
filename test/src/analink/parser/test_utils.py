import pytest

from analink.parser.utils import count_leading_chars, extract_knot_name, extract_parts


class TestExtractParts:
    """Test the extract_parts function"""

    def test_extract_with_brackets(self):
        """Test extracting text with brackets"""
        text = "Go [north] into the forest"
        version1, version2 = extract_parts(text)
        assert version1 == "Go north"
        assert version2 == "Go  into the forest"

    def test_extract_with_brackets_at_start(self):
        """Test brackets at the start of text"""
        text = "[Open door] You open the door"
        version1, version2 = extract_parts(text)
        assert version1 == "Open door"
        assert version2 == " You open the door"

    def test_extract_with_brackets_at_end(self):
        """Test brackets at the end of text"""
        text = "Walk towards the [exit]"
        version1, version2 = extract_parts(text)
        assert version1 == "Walk towards the exit"
        assert version2 == "Walk towards the "

    def test_extract_no_brackets(self):
        """Test text without brackets"""
        text = "Simple text without brackets"
        version1, version2 = extract_parts(text)
        assert version1 == text
        assert version2 == text

    def test_extract_empty_brackets(self):
        """Test empty brackets"""
        text = "Text with [] empty brackets"
        version1, version2 = extract_parts(text)
        assert version1 == "Text with "
        assert version2 == "Text with  empty brackets"

    def test_extract_escaped_brackets(self):
        """Test escaped brackets (should not be processed)"""
        text = "Text with \\[escaped\\] brackets"
        version1, version2 = extract_parts(text)
        assert version1 == text
        assert version2 == text

    def test_extract_multiple_brackets_first_only(self):
        """Test that only the first brackets are processed"""
        text = "First [choice] and second [option]"
        with pytest.raises(ValueError) as exc_info:
            _ = extract_parts(text)
        assert "2 occurrences" in str(exc_info)

    def test_extract_multiline_text(self):
        """Test brackets in multiline text"""
        text = "Line one\n[Select] this option\nLine three"
        version1, version2 = extract_parts(text)
        assert version1 == "Line one\nSelect"
        assert version2 == "Line one\n this option\nLine three"


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
