import pytest

from analink.parser.graph_story import graph_to_mermaid, parse_story
from analink.parser.node import Node, NodeType, clean_lines


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
                1: {"text": "A", "level": 1, "node_type": NodeType.GATHER},
                4: {"text": "B C", "level": 1, "node_type": NodeType.CHOICE},
                7: {"text": "AA BB", "level": 2, "node_type": NodeType.CHOICE},
                8: {"text": "AAA", "level": 3, "node_type": NodeType.CHOICE},
                9: {"text": "BBB", "level": 3, "node_type": NodeType.CHOICE},
                10: {"text": "CCC", "level": 3, "node_type": NodeType.GATHER},
                13: {"text": "DDD EEE", "level": 3, "node_type": NodeType.CHOICE},
                14: {"text": "FFF", "level": 3, "node_type": NodeType.CHOICE},
                15: {"text": "GGG", "level": 3, "node_type": NodeType.CHOICE},
                16: {"text": "CC", "level": 2, "node_type": NodeType.CHOICE},
                17: {"text": "DD", "level": 2, "node_type": NodeType.GATHER},
                18: {"text": "C", "level": 1, "node_type": NodeType.CHOICE},
                19: {"text": "D", "level": 1, "node_type": NodeType.GATHER},
            },
            """```mermaid
flowchart TD
    1["A"]
    4["B C"]
    7["AA BB"]
    8["AAA"]
    9["BBB"]
    10["CCC"]
    13["DDD EEE"]
    14["FFF"]
    15["GGG"]
    16["CC"]
    17["DD"]
    18["C"]
    19["D"]
    1 --> 4
    4 --> 7
    7 --> 8
    7 --> 9
    8 --> 10
    9 --> 10
    10 --> 13
    10 --> 14
    10 --> 15
    4 --> 16
    13 --> 17
    14 --> 17
    15 --> 17
    16 --> 17
    1 --> 18
    17 --> 19
    18 --> 19
```""",
        ]
    ],
)
def test_parser_story_full(ink_code, expected_nodes, expected_mermaid):
    # With
    Node.reset_id_counter()

    # When
    actual_nodes = clean_lines(ink_code)

    # Then
    assert len(actual_nodes) == len(expected_nodes)
    for k in actual_nodes:
        assert actual_nodes[k].content == expected_nodes[k]["text"]
        assert actual_nodes[k].level == expected_nodes[k]["level"]
        assert actual_nodes[k].node_type is expected_nodes[k]["node_type"]

    # When
    actual_edges = parse_story(actual_nodes)
    actual_mermaid = graph_to_mermaid(actual_nodes, actual_edges)

    assert actual_mermaid == expected_mermaid
