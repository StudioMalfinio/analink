# test_node.py

import pytest

from analink.core.models import Node, NodeType, RawStory
from analink.core.parser import (
    InkParser,
    RawStoryBuilder,
    clean_lines,
)


class TestRawStoryBuilder:
    """Test the RawStoryBuilder class"""

    def setup_method(self):
        """Reset ID counter before each test"""
        Node.reset_id_counter()

    def test_process_knot_node(self):
        """Test processing a knot node"""
        builder = RawStoryBuilder()
        knot_node = Node(
            node_type=NodeType.KNOT,
            raw_content="== forest ==",
            level=0,
            line_number=1,
            name="forest",
        )
        builder.process_node(knot_node)

        assert builder.current_knot_id == knot_node.item_id
        assert knot_node.item_id in builder.knots_info

    def test_process_stitches_node(self):
        """Test processing a stitches node"""
        builder = RawStoryBuilder()
        # First create a knot
        knot_node = Node(
            node_type=NodeType.KNOT,
            raw_content="== forest ==",
            level=0,
            line_number=1,
            name="forest",
        )
        builder.process_node(knot_node)

        # Then add stitches
        stitches_node = Node(
            node_type=NodeType.STITCHES,
            raw_content="= clearing",
            level=0,
            line_number=2,
            name="clearing",
        )
        builder.process_node(stitches_node)

        assert builder.current_stitches_id == stitches_node.item_id
        assert stitches_node.item_id in builder.current_stitches_info

    def test_process_content_node_in_header(self):
        """Test processing content node when no knot is active"""
        builder = RawStoryBuilder()
        base_node = Node(
            node_type=NodeType.BASE,
            raw_content="Header text",
            level=0,
            line_number=1,
            content="Header text",
        )
        builder.process_node(base_node)

        assert base_node.item_id in builder.header

    def test_process_content_node_in_knot_header(self):
        """Test processing content node in knot header"""
        builder = RawStoryBuilder()
        # Create knot
        knot_node = Node(
            node_type=NodeType.KNOT,
            raw_content="== forest ==",
            level=0,
            line_number=1,
            name="forest",
        )
        builder.process_node(knot_node)

        # Add content to knot
        base_node = Node(
            node_type=NodeType.BASE,
            raw_content="Forest content",
            level=0,
            line_number=2,
            content="Forest content",
        )
        builder.process_node(base_node)

        assert builder.current_knot_header is not None
        assert base_node.item_id in builder.current_knot_header

    def test_process_content_node_in_stitches(self):
        """Test processing content node in stitches"""
        builder = RawStoryBuilder()
        # Create knot and stitches
        knot_node = Node(
            node_type=NodeType.KNOT,
            raw_content="== forest ==",
            level=0,
            line_number=1,
            name="forest",
        )
        builder.process_node(knot_node)

        stitches_node = Node(
            node_type=NodeType.STITCHES,
            raw_content="= clearing",
            level=0,
            line_number=2,
            name="clearing",
        )
        builder.process_node(stitches_node)

        # Add content to stitches
        base_node = Node(
            node_type=NodeType.BASE,
            raw_content="Clearing content",
            level=0,
            line_number=3,
            content="Clearing content",
        )
        builder.process_node(base_node)

        assert base_node.item_id in builder.current_stitches[stitches_node.item_id]

    def test_finalize_current_knot(self):
        """Test finalizing current knot"""
        builder = RawStoryBuilder()
        # Create and process knot with content
        knot_node = Node(
            node_type=NodeType.KNOT,
            raw_content="== forest ==",
            level=0,
            line_number=1,
            name="forest",
        )
        builder.process_node(knot_node)

        base_node = Node(
            node_type=NodeType.BASE,
            raw_content="Forest content",
            level=0,
            line_number=2,
            content="Forest content",
        )
        builder.process_node(base_node)

        # Finalize
        builder.finalize_current_knot()

        assert knot_node.item_id in builder.knots
        assert builder.current_knot_header is None

    def test_build_story(self):
        """Test building complete story"""
        builder = RawStoryBuilder()

        # Create nodes
        header_node = Node(
            node_type=NodeType.BASE,
            raw_content="Story header",
            level=0,
            line_number=1,
            content="Story header",
        )

        knot_node = Node(
            node_type=NodeType.KNOT,
            raw_content="== chapter1 ==",
            level=0,
            line_number=2,
            name="chapter1",
        )

        knot_content_node = Node(
            node_type=NodeType.BASE,
            raw_content="Chapter content",
            level=0,
            line_number=3,
            content="Chapter content",
        )

        nodes = {
            header_node.item_id: header_node,
            knot_node.item_id: knot_node,
            knot_content_node.item_id: knot_content_node,
        }

        story = builder.build_story(nodes)

        assert isinstance(story, RawStory)
        assert header_node.item_id in story.header
        assert knot_node.item_id in story.knots_info
        assert knot_node.item_id in story.knots


class TestInkParser:
    """Test the InkParser class"""

    def setup_method(self):
        """Reset ID counter before each test"""
        Node.reset_id_counter()

    def test_handle_include_files_no_includes(self):
        """Test handling lines with no includes"""
        parser = InkParser()
        lines = ["Line 1", "Line 2", "Line 3"]
        result = parser.handle_include_files(lines.copy())
        assert result == lines

    def test_parse_simple_ink(self):
        """Test parsing simple ink code"""
        parser = InkParser()
        ink_code = "Hello world"
        story = parser.parse(ink_code)

        assert isinstance(story, RawStory)
        assert len(story.header) == 1
        node = next(iter(story.header.values()))
        assert node.content == "Hello world"

    def test_parse_with_choices(self):
        """Test parsing ink with choices"""
        parser = InkParser()
        ink_code = """Opening text
* First choice
* Second choice"""
        story = parser.parse(ink_code)

        assert len(story.header) == 3  # opening + 2 choices
        nodes = list(story.header.values())
        choice_nodes = [n for n in nodes if n.node_type == NodeType.CHOICE]
        assert len(choice_nodes) == 2

    def test_parse_with_knots(self):
        """Test parsing ink with knots"""
        parser = InkParser()
        ink_code = """Opening text
== forest ==
Forest content"""
        story = parser.parse(ink_code)

        assert len(story.header) == 1
        assert len(story.knots_info) == 1
        assert len(story.knots) == 1

    def test_custom_separator(self):
        """Test parsing with custom separator"""
        parser = InkParser(" | ")
        ink_code = """First line
Second line"""
        story = parser.parse(ink_code)

        node = next(iter(story.header.values()))
        assert " | " in node.content


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
        """Test that comments and directives are handled properly"""
        ink_code = """First line
// This is a comment
-> SOME_DIRECTIVE
Second line"""

        result = clean_lines(ink_code)

        # Should have base content + divert node + second base
        assert len(result.header) == 3
        nodes = list(result.header.values())

        base_nodes = [n for n in nodes if n.node_type == NodeType.BASE]
        divert_nodes = [n for n in nodes if n.node_type == NodeType.DIVERT]

        assert len(base_nodes) == 2
        assert len(divert_nodes) == 1
        assert divert_nodes[0].name == "SOME_DIRECTIVE"

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


# Additional integration tests
class TestParserIntegration:
    """Test integration between parser components"""

    def setup_method(self):
        """Reset ID counter before each test"""
        Node.reset_id_counter()

    def test_post_processing_integration(self):
        """Test that post-processing is properly integrated"""
        ink_code = "* [Choose option] <> You chose wisely. # CLEAR -> next_section"
        result = clean_lines(ink_code)

        nodes = list(result.header.values())
        choice_node = next(n for n in nodes if n.node_type == NodeType.CHOICE)
        divert_node = next(n for n in nodes if n.node_type == NodeType.DIVERT)

        # Check that all post-processing was applied
        assert choice_node.choice_text == "Choose option"
        assert choice_node.content == "  You chose wisely. "
        assert choice_node.glue_after is True
        assert choice_node.instruction == " CLEAR"

        assert divert_node.name == "next_section"

    def test_complex_choice_parsing(self):
        """Test complex choice parsing with all features"""
        ink_code = "*** [Carefully examine] <> You examine it closely. # INVESTIGATE -> detailed_view"
        result = clean_lines(ink_code)

        nodes = list(result.header.values())
        choice_node = next(n for n in nodes if n.node_type == NodeType.CHOICE)
        divert_node = next(n for n in nodes if n.node_type == NodeType.DIVERT)

        assert choice_node.level == 3
        assert choice_node.choice_text == "Carefully examine"
        assert choice_node.content == "  You examine it closely. "
        assert choice_node.glue_after is True
        assert choice_node.instruction == " INVESTIGATE"

        assert divert_node.name == "detailed_view"

    def test_gather_with_continuation(self):
        """Test gather points with continuation text"""
        ink_code = """* First choice
* Second choice
- <> You made a choice.
  The story continues here."""

        result = clean_lines(ink_code)

        nodes = list(result.header.values())
        gather_node = next(n for n in nodes if n.node_type == NodeType.GATHER)

        assert gather_node.glue_before is True
        assert "You made a choice. The story continues here." in gather_node.content

    def test_multiline_comments_in_complex_structure(self):
        """Test multiline comments within complex structures"""
        ink_code = """== main ==
/* This is a 
   multiline comment
   that should be ignored */
Main content here.

= section
/* Another comment */
Section content."""

        result = clean_lines(ink_code)

        # Should only have knot structure, no comment content
        assert len(result.knots_info) == 1
        knot = next(iter(result.knots.values()))

        # Check that comments were properly filtered out
        all_content = []
        for node in knot.header.values():
            if node.content:
                all_content.append(node.content)
        for stitch_content in knot.stitches.values():
            for node in stitch_content.values():
                if node.content:
                    all_content.append(node.content)

        # Should not contain any comment text
        combined_content = " ".join(all_content)
        assert "multiline comment" not in combined_content
        assert "Another comment" not in combined_content
        assert "Main content here." in combined_content
        assert "Section content." in combined_content

    def test_empty_choices_and_gathers(self):
        """Test handling of empty choices and gathers"""
        ink_code = """*
**
-
--"""

        result = clean_lines(ink_code)

        nodes = list(result.header.values())
        choice_nodes = [n for n in nodes if n.node_type == NodeType.CHOICE]
        gather_nodes = [n for n in nodes if n.node_type == NodeType.GATHER]

        assert len(choice_nodes) == 2
        assert len(gather_nodes) == 2

        # Check levels
        choice_levels = [n.level for n in choice_nodes]
        gather_levels = [n.level for n in gather_nodes]

        assert 1 in choice_levels
        assert 2 in choice_levels
        assert 1 in gather_levels
        assert 2 in gather_levels

    def test_story_name_resolution(self):
        """Test story name to ID resolution"""
        ink_code = """== chapter_one ==
Chapter content.

= intro
Introduction content.

= conclusion
Conclusion content.

== chapter_two ==
Second chapter."""

        result = clean_lines(ink_code)
        name_to_id = result.block_name_to_id

        # Check knot names
        assert "chapter_one" in name_to_id
        assert "chapter_two" in name_to_id

        # Check stitch names
        assert "chapter_one.intro" in name_to_id
        assert "chapter_one.conclusion" in name_to_id

        # Verify IDs point to correct content
        chapter_one_id = name_to_id["chapter_one"]
        intro_id = name_to_id["chapter_one.intro"]
        conclusion_id = name_to_id["chapter_one.conclusion"]

        chapter_one_node = result.get_node(chapter_one_id)
        intro_node = result.get_node(intro_id)
        conclusion_node = result.get_node(conclusion_id)

        assert chapter_one_node.content == "Chapter content."
        assert intro_node.content == "Introduction content."
        assert conclusion_node.content == "Conclusion content."

    def test_edge_case_parsing(self):
        """Test edge cases in parsing"""
        ink_code = """= stitch_at_start
Content before any knot.

==  spaced_knot  ==

=  spaced_stitch  

*  spaced_choice  
-  spaced_gather  
->  spaced_divert  """

        result = clean_lines(ink_code)

        # Should handle spaced elements correctly
        assert len(result.knots_info) == 1
        knot_info = next(iter(result.knots_info.values()))
        assert knot_info.name == "spaced_knot"

        # Check that the initial stitch content went to header
        assert len(result.header) > 0

    def test_mixed_content_merging(self):
        """Test merging of mixed content types"""
        ink_code = """* Start choice
More choice text
Even more choice text

- Gather point
Gather continuation
More gather text

Base content line
Another base line
Final base line"""

        result = clean_lines(ink_code)

        nodes = list(result.header.values())

        # Should have merged content properly
        choice_node = next(n for n in nodes if n.node_type == NodeType.CHOICE)
        gather_node = next(n for n in nodes if n.node_type == NodeType.GATHER)

        assert (
            "Start choice More choice text Even more choice text" in choice_node.content
        )
        assert (
            "Gather point Gather continuation More gather text Base content line Another base line Final base line"
            in gather_node.content
        )


class TestParserErrorHandling:
    """Test error handling and edge cases"""

    def setup_method(self):
        """Reset ID counter before each test"""
        Node.reset_id_counter()

    def test_malformed_knot_headers(self):
        """Test handling of malformed knot headers"""
        ink_code = """== incomplete_knot
=== too_many_equals ===
= just_one_equal
Content after malformed headers."""

        result = clean_lines(ink_code)

        # Should still parse what it can
        assert len(result.header) > 0 or len(result.knots) > 0

    def test_mixed_whitespace_handling(self):
        """Test handling of mixed whitespace"""
        ink_code = "\t* Tab choice\n  * Space choice\n\t  * Mixed choice"
        result = clean_lines(ink_code)

        nodes = list(result.header.values())
        choice_nodes = [n for n in nodes if n.node_type == NodeType.CHOICE]

        assert len(choice_nodes) == 3
        for node in choice_nodes:
            assert node.level == 1  # All should be level 1

    def test_very_long_lines(self):
        """Test handling of very long lines"""
        long_content = "Very " * 1000 + "long content."
        ink_code = f"""* {long_content}
{long_content}"""

        result = clean_lines(ink_code)

        # Should handle long content without issues
        nodes = list(result.header.values())
        assert len(nodes) > 0

    def test_unicode_content(self):
        """Test handling of Unicode content"""
        ink_code = """* Choose café ☕
- Héllo wörld! 🌍
== château ==
Résumé your journey."""

        result = clean_lines(ink_code)

        # Should preserve Unicode content
        nodes = list(result.header.values())
        choice_node = next(n for n in nodes if n.node_type == NodeType.CHOICE)
        assert "café ☕" in choice_node.content

        knot_info = next(iter(result.knots_info.values()))
        assert knot_info.name == "château"
