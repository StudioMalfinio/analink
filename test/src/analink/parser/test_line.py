# Assuming your module is named analink.parser.line.py
from analink.parser.line import (
    InkLine,
    InkLineType,
    clean_lines,
    count_leading_chars,
    parse_line,
)


class TestInkLineType:
    """Test the InkLineType enum"""

    def test_enum_values(self):
        """Test that enum values are correct"""
        assert InkLineType.CHOICE.value == "choice"
        assert InkLineType.GATHER.value == "gather"
        assert InkLineType.BASE.value == "base_content"

    def test_enum_members(self):
        """Test that all expected enum members exist"""
        assert len(InkLineType) == 3
        assert InkLineType.CHOICE in InkLineType
        assert InkLineType.GATHER in InkLineType
        assert InkLineType.BASE in InkLineType


class TestInkLine:
    """Test the InkLine model"""

    def test_inkline_creation(self):
        """Test creating an InkLine instance"""
        line = InkLine(
            level=1,
            line_type=InkLineType.CHOICE,
            text="Some choice text",
            raw_line="* Some choice text",
            line_number=5,
        )
        assert line.level == 1
        assert line.line_type == InkLineType.CHOICE
        assert line.text == "Some choice text"
        assert line.raw_line == "* Some choice text"
        assert line.line_number == 5

    def test_inkline_with_all_types(self):
        """Test InkLine with different line types"""
        choice_line = InkLine(
            level=2,
            line_type=InkLineType.CHOICE,
            text="Choice",
            raw_line="** Choice",
            line_number=1,
        )
        gather_line = InkLine(
            level=1,
            line_type=InkLineType.GATHER,
            text="Gather",
            raw_line="- Gather",
            line_number=2,
        )
        base_line = InkLine(
            level=-1,
            line_type=InkLineType.BASE,
            text="Base content",
            raw_line="Base content",
            line_number=3,
        )

        assert choice_line.line_type == InkLineType.CHOICE
        assert gather_line.line_type == InkLineType.GATHER
        assert base_line.line_type == InkLineType.BASE


class TestCountLeadingChars:
    """Test the count_leading_chars function"""

    def test_no_leading_chars(self):
        """Test line with no leading characters"""
        count, text = count_leading_chars("Hello world", "*")
        assert count == 0
        assert text == "Hello world"

    def test_single_leading_char(self):
        """Test line with single leading character"""
        count, text = count_leading_chars("* Choice text", "*")
        assert count == 1
        assert text == "Choice text"

    def test_multiple_leading_chars(self):
        """Test line with multiple leading characters"""
        count, text = count_leading_chars("*** Deep choice", "*")
        assert count == 3
        assert text == "Deep choice"

    def test_leading_chars_with_spaces(self):
        """Test leading characters with spaces"""
        count, text = count_leading_chars("*  Choice with spaces", "*")
        assert count == 1
        assert text == "Choice with spaces"

    def test_leading_chars_with_tabs(self):
        """Test leading characters with tabs"""
        count, text = count_leading_chars("*\t\tChoice with tabs", "*")
        assert count == 1
        assert text == "Choice with tabs"

    def test_mixed_spaces_and_tabs(self):
        """Test leading characters with mixed spaces and tabs"""
        count, text = count_leading_chars("** \t Mixed whitespace", "*")
        assert count == 2
        assert text == "Mixed whitespace"

    def test_different_char_types(self):
        """Test with different character types"""
        count, text = count_leading_chars("-- Gather text", "-")
        assert count == 2
        assert text == "Gather text"

    def test_only_leading_chars(self):
        """Test line with only leading characters"""
        count, text = count_leading_chars("***", "*")
        assert count == 3
        assert text == ""

    def test_leading_chars_with_only_whitespace_after(self):
        """Test leading chars followed by only whitespace"""
        count, text = count_leading_chars("**   \t  ", "*")
        assert count == 2
        assert text == ""

    def test_empty_string(self):
        """Test empty string"""
        count, text = count_leading_chars("", "*")
        assert count == 0
        assert text == ""

    def test_whitespace_only(self):
        """Test string with only whitespace"""
        count, text = count_leading_chars("   \t  ", "*")
        assert count == 0
        assert text == ""


class TestParseLine:
    """Test the parse_line function"""

    def test_parse_empty_line(self):
        """Test parsing empty line returns None"""
        result = parse_line("", 1)
        assert result is None

    def test_parse_whitespace_only_line(self):
        """Test parsing whitespace-only line returns None"""
        result = parse_line("   \t  ", 1)
        assert result is None

    def test_parse_comment_line(self):
        """Test parsing comment line returns None"""
        result = parse_line("// This is a comment", 1)
        assert result is None

    def test_parse_comment_with_leading_spaces(self):
        """Test parsing comment with leading spaces returns None"""
        result = parse_line("   // Comment with spaces", 1)
        assert result is None

    def test_parse_directive_line(self):
        """Test parsing directive line returns None"""
        result = parse_line("-> END", 1)
        assert result is None

    def test_parse_directive_with_spaces(self):
        """Test parsing directive with spaces returns None"""
        result = parse_line("  -> DONE  ", 1)
        assert result is None

    def test_parse_single_choice(self):
        """Test parsing single-level choice"""
        result = parse_line("* This is a choice", 5)
        assert result is not None
        assert result.level == 1
        assert result.line_type == InkLineType.CHOICE
        assert result.text == "This is a choice"
        assert result.raw_line == "* This is a choice"
        assert result.line_number == 5

    def test_parse_multiple_choice_levels(self):
        """Test parsing multiple choice levels"""
        result = parse_line("*** Deep nested choice", 10)
        assert result is not None
        assert result.level == 3
        assert result.line_type == InkLineType.CHOICE
        assert result.text == "Deep nested choice"
        assert result.raw_line == "*** Deep nested choice"
        assert result.line_number == 10

    def test_parse_choice_with_spaces(self):
        """Test parsing choice with leading spaces"""
        result = parse_line("*   Choice with spaces", 2)
        assert result is not None
        assert result.level == 1
        assert result.line_type == InkLineType.CHOICE
        assert result.text == "Choice with spaces"

    def test_parse_single_gather(self):
        """Test parsing single-level gather"""
        result = parse_line("- This is a gather", 3)
        assert result is not None
        assert result.level == 1
        assert result.line_type == InkLineType.GATHER
        assert result.text == "This is a gather"
        assert result.raw_line == "- This is a gather"
        assert result.line_number == 3

    def test_parse_multiple_gather_levels(self):
        """Test parsing multiple gather levels"""
        result = parse_line("-- Nested gather", 7)
        assert result is not None
        assert result.level == 2
        assert result.line_type == InkLineType.GATHER
        assert result.text == "Nested gather"
        assert result.raw_line == "-- Nested gather"
        assert result.line_number == 7

    def test_parse_gather_with_spaces(self):
        """Test parsing gather with spaces"""
        result = parse_line("-  Gather with spaces", 4)
        assert result is not None
        assert result.level == 1
        assert result.line_type == InkLineType.GATHER
        assert result.text == "Gather with spaces"

    def test_parse_base_content(self):
        """Test parsing base content"""
        result = parse_line("This is base content", 1)
        assert result is not None
        assert result.level == -1
        assert result.line_type == InkLineType.BASE
        assert result.text == "This is base content"
        assert result.raw_line == "This is base content"
        assert result.line_number == 1

    def test_parse_base_content_with_leading_spaces(self):
        """Test parsing base content with leading spaces"""
        result = parse_line("   Base content with spaces   ", 8)
        assert result is not None
        assert result.level == -1
        assert result.line_type == InkLineType.BASE
        assert result.text == "Base content with spaces"
        assert result.raw_line == "   Base content with spaces   "
        assert result.line_number == 8

    def test_choice_takes_precedence_over_gather(self):
        """Test that if both * and - are present, choice takes precedence"""
        result = parse_line("* Choice with - dash", 1)
        assert result is not None
        assert result.line_type == InkLineType.CHOICE
        assert result.level == 1
        assert result.text == "Choice with - dash"


class TestCleanLines:
    """Test the clean_lines function"""

    def test_empty_input(self):
        """Test empty input"""
        result = clean_lines("")
        assert result == []

    def test_whitespace_only_input(self):
        """Test whitespace-only input"""
        result = clean_lines("   \n  \t  \n   ")
        assert result == []

    def test_single_base_line(self):
        """Test single base content line"""
        result = clean_lines("Hello world")
        assert len(result) == 1
        assert result[0].level == 0
        assert result[0].line_type == InkLineType.BASE
        assert result[0].text == "Hello world"
        assert result[0].line_number == 1

    def test_multiple_base_lines_concatenated(self):
        """Test multiple base lines get concatenated"""
        result = clean_lines("First line\nSecond line\nThird line")
        assert len(result) == 1
        assert result[0].level == 0
        assert result[0].line_type == InkLineType.BASE
        assert result[0].text == "First line Second line Third line"
        assert result[0].line_number == 1

    def test_custom_separator(self):
        """Test custom separator for concatenating base lines"""
        result = clean_lines("First line\nSecond line", clean_text_sep=" | ")
        assert len(result) == 1
        assert result[0].text == "First line | Second line"

    def test_single_choice(self):
        """Test single choice line"""
        result = clean_lines("* Choice option")
        assert len(result) == 1
        assert result[0].level == 1
        assert result[0].line_type == InkLineType.CHOICE
        assert result[0].text == "Choice option"
        assert result[0].line_number == 1

    def test_multiple_choices(self):
        """Test multiple choice lines"""
        result = clean_lines("* First choice\n* Second choice\n** Nested choice")
        assert len(result) == 3
        assert all(line.line_type == InkLineType.CHOICE for line in result)
        assert result[0].level == 1
        assert result[1].level == 1
        assert result[2].level == 2
        assert result[0].text == "First choice"
        assert result[1].text == "Second choice"
        assert result[2].text == "Nested choice"

    def test_single_gather(self):
        """Test single gather line"""
        result = clean_lines("- Gather point")
        assert len(result) == 1
        assert result[0].level == 1
        assert result[0].line_type == InkLineType.GATHER
        assert result[0].text == "Gather point"
        assert result[0].line_number == 1

    def test_mixed_content_types(self):
        """Test mixing different content types"""
        ink_code = """This is base content
More base content
* First choice
* Second choice
- Gather point
Final base content"""

        result = clean_lines(ink_code)
        assert len(result) == 4

        # First item: concatenated base content
        assert result[0].line_type == InkLineType.BASE
        assert result[0].text == "This is base content More base content"
        assert result[0].level == 0

        # Choices
        assert result[1].line_type == InkLineType.CHOICE
        assert result[1].text == "First choice"
        assert result[2].line_type == InkLineType.CHOICE
        assert result[2].text == "Second choice"

        # Gather followed by base content
        assert result[3].line_type == InkLineType.GATHER
        assert result[3].text == "Gather point Final base content"

    def test_comments_and_directives_ignored(self):
        """Test that comments and directives are ignored"""
        ink_code = """// This is a comment
Base content line
-> SOME_DIRECTIVE
* Choice line
// Another comment
- Gather line"""

        result = clean_lines(ink_code)
        assert len(result) == 3
        assert result[0].line_type == InkLineType.BASE
        assert result[0].text == "Base content line"
        assert result[1].line_type == InkLineType.CHOICE
        assert result[1].text == "Choice line"
        assert result[2].line_type == InkLineType.GATHER
        assert result[2].text == "Gather line"

    def test_empty_lines_ignored(self):
        """Test that empty lines are ignored"""
        ink_code = """Base content

* Choice

- Gather

More base"""

        result = clean_lines(ink_code)
        assert len(result) == 3
        assert result[0].text == "Base content"
        assert result[1].text == "Choice"
        assert result[2].text == "Gather More base"

    def test_line_numbers_preserved(self):
        """Test that line numbers are correctly preserved"""
        ink_code = """// Comment line 1
Base content line 2
// Comment line 3

* Choice line 5"""

        result = clean_lines(ink_code)
        assert len(result) == 2
        assert result[0].line_number == 2  # Base content starts at line 2
        assert result[1].line_number == 5  # Choice is at line 5

    def test_complex_nested_structure(self):
        """Test complex nested structure"""
        ink_code = """Story introduction
Some more story text
* First choice option
** Nested choice A
** Nested choice B
- Gather after choices
-- Deep gather
* Another top choice
Final story text"""

        result = clean_lines(ink_code)
        assert len(result) == 7

        # Check structure
        assert result[0].line_type == InkLineType.BASE
        assert result[0].text == "Story introduction Some more story text"
        assert result[1].text == "First choice option"
        assert result[1].line_type == InkLineType.CHOICE
        assert result[1].level == 1
        assert result[2].text == "Nested choice A"
        assert result[2].line_type == InkLineType.CHOICE
        assert result[2].level == 2
        assert result[3].line_type == InkLineType.CHOICE
        assert result[3].level == 2
        assert result[4].line_type == InkLineType.GATHER
        assert result[4].level == 1
        assert result[5].line_type == InkLineType.GATHER
        assert result[5].level == 2
        assert result[6].line_type == InkLineType.CHOICE
        assert result[6].level == 1
        assert result[6].text == "Another top choice Final story text"

    def test_base_content_raw_line_concatenation(self):
        """Test that raw_line is properly concatenated for base content"""
        ink_code = "First line\nSecond line"
        result = clean_lines(ink_code)

        assert len(result) == 1
        assert result[0].raw_line == "First line\nSecond line"

    def test_only_comments_and_directives(self):
        """Test input with only comments and directives"""
        ink_code = """// Comment 1
-> DIRECTIVE
// Comment 2
-> ANOTHER_DIRECTIVE"""

        result = clean_lines(ink_code)
        assert result == []


# Integration tests
class TestIntegration:
    """Integration tests combining multiple functions"""

    def test_complete_ink_story_parsing(self):
        """Test parsing a complete Ink story structure"""
        story = """You wake up in a dark room.
There's a door to your left and a window to your right.
* Open the door
** The door creaks open slowly
** You step through confidently  
- You find yourself in a hallway
* Look out the window
The moonlight reveals a garden below.
-> END"""

        result = clean_lines(story)

        # Should have base content, choices, nested choices, gather, choice, and final base
        expected_types = [
            InkLineType.BASE,  # Opening description
            InkLineType.CHOICE,  # Open the door
            InkLineType.CHOICE,  # Door creaks (nested)
            InkLineType.CHOICE,  # Step through (nested)
            InkLineType.GATHER,  # Find hallway
            InkLineType.CHOICE,  # Look out window
        ]

        assert len(result) == len(expected_types)
        for i, expected_type in enumerate(expected_types):
            assert result[i].line_type == expected_type

    def test_edge_case_combinations(self):
        """Test various edge case combinations"""
        story = """
        
// Starting comment
Base text with   spaces   
   // Indented comment
        * Choice with weird spacing   
    ** 
        
    - Gather
    -> SKIP_THIS
    Final text
        """

        result = clean_lines(story)

        # Should handle the weird spacing and empty content properly
        assert len(result) >= 3  # At least base, choice, gather
        assert any(line.line_type == InkLineType.BASE for line in result)
        assert any(line.line_type == InkLineType.CHOICE for line in result)
        assert any(line.line_type == InkLineType.GATHER for line in result)
