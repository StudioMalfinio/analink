import pytest

from analink.parser.utils import extract_parts


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
