import pytest

from analink.core.parser import Node, NodeType, clean_lines
from analink.parser.graph_story import graph_to_mermaid, parse_story


@pytest.mark.parametrize(
    "ink_code, expected_nodes, expected_mermaid",
    [
        [
            """
- A
*	B
    C
	* * 	AA
    BB
			* * * 	AAA
			* * *  BBB
			- - - 	CCC
			* * *	DDD
					EEE
			* * *	FFF
			* * * 	GGG
	* * 	CC
	- - 	DD
*	C
-  D
""",
            {
                1: {
                    "text": "A",
                    "level": 1,
                    "node_type": NodeType.GATHER,
                    "choice_text": None,
                },
                4: {
                    "text": "B C",
                    "level": 1,
                    "node_type": NodeType.CHOICE,
                    "choice_text": "B C",
                },
                7: {
                    "text": "AA BB",
                    "level": 2,
                    "node_type": NodeType.CHOICE,
                    "choice_text": "AA BB",
                },
                8: {
                    "text": "AAA",
                    "level": 3,
                    "node_type": NodeType.CHOICE,
                    "choice_text": "AAA",
                },
                9: {
                    "text": "BBB",
                    "level": 3,
                    "node_type": NodeType.CHOICE,
                    "choice_text": "BBB",
                },
                10: {
                    "text": "CCC",
                    "level": 3,
                    "node_type": NodeType.GATHER,
                    "choice_text": None,
                },
                13: {
                    "text": "DDD EEE",
                    "level": 3,
                    "node_type": NodeType.CHOICE,
                    "choice_text": "DDD EEE",
                },
                14: {
                    "text": "FFF",
                    "level": 3,
                    "node_type": NodeType.CHOICE,
                    "choice_text": "FFF",
                },
                15: {
                    "text": "GGG",
                    "level": 3,
                    "node_type": NodeType.CHOICE,
                    "choice_text": "GGG",
                },
                16: {
                    "text": "CC",
                    "level": 2,
                    "node_type": NodeType.CHOICE,
                    "choice_text": "CC",
                },
                17: {
                    "text": "DD",
                    "level": 2,
                    "node_type": NodeType.GATHER,
                    "choice_text": None,
                },
                18: {
                    "text": "C",
                    "level": 1,
                    "node_type": NodeType.CHOICE,
                    "choice_text": "C",
                },
                19: {
                    "text": "D",
                    "level": 1,
                    "node_type": NodeType.GATHER,
                    "choice_text": None,
                },
            },
            """```mermaid
flowchart TD
    1["A"]
    4{"B C"}
    7{"AA BB"}
    8{"AAA"}
    9{"BBB"}
    10["CCC"]
    13{"DDD EEE"}
    14{"FFF"}
    15{"GGG"}
    16{"CC"}
    17["DD"]
    18{"C"}
    19["D"]
    1 -->|B C| 4
    4 -->|AA BB| 7
    7 -->|AAA| 8
    7 -->|BBB| 9
    8 --> 10
    9 --> 10
    10 -->|DDD EEE| 13
    10 -->|FFF| 14
    10 -->|GGG| 15
    4 -->|CC| 16
    13 --> 17
    14 --> 17
    15 --> 17
    16 --> 17
    1 -->|C| 18
    17 --> 19
    18 --> 19
```""",
        ],
        [
            """
- A
*	B
    [K]C
	* * 	AA
    BB
			* * * 	AA[U]A
			* * *  BBB
			- - - 	CCC
			* * *	DDD
					EEE
			* * *	FFF
			* * * 	GGG
	* * 	CC
	- - 	DD
*	C
-  D
""",
            {
                1: {
                    "text": "A",
                    "level": 1,
                    "node_type": NodeType.GATHER,
                    "choice_text": None,
                },
                4: {
                    "text": "B C",
                    "level": 1,
                    "node_type": NodeType.CHOICE,
                    "choice_text": "B K",
                },
                7: {
                    "text": "AA BB",
                    "level": 2,
                    "node_type": NodeType.CHOICE,
                    "choice_text": "AA BB",
                },
                8: {
                    "text": "AAA",
                    "level": 3,
                    "node_type": NodeType.CHOICE,
                    "choice_text": "AAU",
                },
                9: {
                    "text": "BBB",
                    "level": 3,
                    "node_type": NodeType.CHOICE,
                    "choice_text": "BBB",
                },
                10: {
                    "text": "CCC",
                    "level": 3,
                    "node_type": NodeType.GATHER,
                    "choice_text": None,
                },
                13: {
                    "text": "DDD EEE",
                    "level": 3,
                    "node_type": NodeType.CHOICE,
                    "choice_text": "DDD EEE",
                },
                14: {
                    "text": "FFF",
                    "level": 3,
                    "node_type": NodeType.CHOICE,
                    "choice_text": "FFF",
                },
                15: {
                    "text": "GGG",
                    "level": 3,
                    "node_type": NodeType.CHOICE,
                    "choice_text": "GGG",
                },
                16: {
                    "text": "CC",
                    "level": 2,
                    "node_type": NodeType.CHOICE,
                    "choice_text": "CC",
                },
                17: {
                    "text": "DD",
                    "level": 2,
                    "node_type": NodeType.GATHER,
                    "choice_text": None,
                },
                18: {
                    "text": "C",
                    "level": 1,
                    "node_type": NodeType.CHOICE,
                    "choice_text": "C",
                },
                19: {
                    "text": "D",
                    "level": 1,
                    "node_type": NodeType.GATHER,
                    "choice_text": None,
                },
            },
            """```mermaid
flowchart TD
    1["A"]
    4{"B C"}
    7{"AA BB"}
    8{"AAA"}
    9{"BBB"}
    10["CCC"]
    13{"DDD EEE"}
    14{"FFF"}
    15{"GGG"}
    16{"CC"}
    17["DD"]
    18{"C"}
    19["D"]
    1 -->|B K| 4
    4 -->|AA BB| 7
    7 -->|AAU| 8
    7 -->|BBB| 9
    8 --> 10
    9 --> 10
    10 -->|DDD EEE| 13
    10 -->|FFF| 14
    10 -->|GGG| 15
    4 -->|CC| 16
    13 --> 17
    14 --> 17
    15 --> 17
    16 --> 17
    1 -->|C| 18
    17 --> 19
    18 --> 19
```""",
        ],
    ],
)
def test_parser_story_full(ink_code, expected_nodes, expected_mermaid):
    # With
    Node.reset_id_counter()

    # When
    actual_nodes, actual_edges = parse_story(clean_lines(ink_code))

    # Then
    assert len(actual_nodes) == len(expected_nodes) + 3
    for k in actual_nodes:
        if k > -1:
            assert actual_nodes[k].content == expected_nodes[k]["text"]
            assert actual_nodes[k].level == expected_nodes[k]["level"]
            assert actual_nodes[k].node_type is expected_nodes[k]["node_type"]
            assert actual_nodes[k].choice_text == expected_nodes[k]["choice_text"]

    # When
    actual_mermaid = graph_to_mermaid(actual_nodes, actual_edges, use_letter=False)

    assert actual_mermaid == expected_mermaid


def test_for_debug():
    from analink.core.parser import Node, clean_lines
    from analink.parser.graph_story import parse_story

    Node.reset_id_counter()
    ink_code_1 = """=== back_in_london ===

We arrived into London at 9.45pm exactly.

*	"There is not a moment to lose!"[] I declared.
	-> hurry_outside

*	"Monsieur, let us savour this moment!"[] I declared.
	My master clouted me firmly around the head and dragged me out of the door.
	-> dragged_outside

*	[We hurried home] -> hurry_outside


=== hurry_outside ===
We hurried home to Savile Row -> as_fast_as_we_could


=== dragged_outside ===
He insisted that we hurried home to Savile Row
-> as_fast_as_we_could


=== as_fast_as_we_could ===
<> as fast as we could."""
    raw_story = clean_lines(ink_code_1)
    nodes, edges = parse_story(raw_story)
    assert True
