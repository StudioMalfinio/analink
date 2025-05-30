from analink.parser.choice import parse_choices

# we do many test with valid ink code
# The code comes from https://github.com/inkle/ink/blob/master/Documentation/WritingWithInk.md
# we test if the codes are valid in inky


def test_parse_choices():
    # With
    expected_display = [
        '"I am somewhat tired."',
        '"Nothing, Monsieur!"',
        '"I said, this journey is appalling."',
    ]
    expected_text_after_choice = [
        '"I am somewhat tired," I repeated.\n"Really," he responded. "How deleterious."',
        '"Nothing, Monsieur!" I replied.\n"Very good, then."',
        '"I said, this journey is appalling and I want no more of it."\n"Ah," he replied, not unkindly. "I see you are feeling frustrated. Tomorrow, things will improve."\n',
    ]
    expected_line_number = [2,4,6]
    ink_code = """
"What's that?" my master asked.
*	"I am somewhat tired[."]," I repeated.
	"Really," he responded. "How deleterious."
*	"Nothing, Monsieur!"[] I replied.
	"Very good, then."
*  "I said, this journey is appalling[."] and I want no more of it."
	"Ah," he replied, not unkindly. "I see you are feeling frustrated. Tomorrow, things will improve."
"""
    # When
    parsed_ink_code = parse_choices(ink_code)

    # Then
    for k, choice in enumerate(parsed_ink_code):
        assert choice.display_text == expected_display[k]
        assert choice.text_after_choice == expected_text_after_choice[k]
        assert choice.line_number == expected_line_number[k]
        assert not choice.sticky
