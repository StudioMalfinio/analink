import pytest

from analink.parser.container import Container
from analink.parser.line import InkLineType, clean_lines
from analink.parser.tool import parse_story


@pytest.mark.parametrize(
    "ink_code, expected_lines, expected_tree, expected_mermaid",
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
                0: {"text": "A", "level": 1, "line_type": InkLineType.GATHER},
                1: {"text": "B C", "level": 1, "line_type": InkLineType.CHOICE},
                2: {"text": "AA BB", "level": 2, "line_type": InkLineType.CHOICE},
                3: {"text": "AAA", "level": 3, "line_type": InkLineType.CHOICE},
                4: {"text": "BBB", "level": 3, "line_type": InkLineType.CHOICE},
                5: {"text": "CCC", "level": 3, "line_type": InkLineType.GATHER},
                6: {"text": "DDD EEE", "level": 3, "line_type": InkLineType.CHOICE},
                7: {"text": "FFF", "level": 3, "line_type": InkLineType.CHOICE},
                8: {"text": "GGG", "level": 3, "line_type": InkLineType.CHOICE},
                9: {"text": "CC", "level": 2, "line_type": InkLineType.CHOICE},
                10: {"text": "DD", "level": 2, "line_type": InkLineType.GATHER},
                11: {"text": "C", "level": 1, "line_type": InkLineType.CHOICE},
                12: {"text": "D", "level": 1, "line_type": InkLineType.GATHER},
            },
            """=== CONTAINER ID : 13 ===
    A
├── === CONTAINER ID : 10 ===
│   B C
│   ├── === CONTAINER ID : 7 ===
│   │   AA BB
│   │   ├── === CONTAINER ID : 1 ===
│   │   │   AAA
│   │   │   └── === CONTAINER ID : 6 ===
│   │   │       CCC
│   │   │       ├── === CONTAINER ID : 3 ===
│   │   │       │   DDD EEE
│   │   │       │   └── === CONTAINER ID : 9 ===
│   │   │       │       DD
│   │   │       │       └── === CONTAINER ID : 12 ===
│   │   │       │           D
│   │   │       ├── === CONTAINER ID : 4 ===
│   │   │       │   FFF
│   │   │       │   └── === CONTAINER ID : 9 ===
│   │   │       │       DD
│   │   │       │       └── === CONTAINER ID : 12 ===
│   │   │       │           D
│   │   │       └── === CONTAINER ID : 5 ===
│   │   │           GGG
│   │   │           └── === CONTAINER ID : 9 ===
│   │   │               DD
│   │   │               └── === CONTAINER ID : 12 ===
│   │   │                   D
│   │   └── === CONTAINER ID : 2 ===
│   │       BBB
│   │       └── === CONTAINER ID : 6 ===
│   │           CCC
│   │           ├── === CONTAINER ID : 3 ===
│   │           │   DDD EEE
│   │           │   └── === CONTAINER ID : 9 ===
│   │           │       DD
│   │           │       └── === CONTAINER ID : 12 ===
│   │           │           D
│   │           ├── === CONTAINER ID : 4 ===
│   │           │   FFF
│   │           │   └── === CONTAINER ID : 9 ===
│   │           │       DD
│   │           │       └── === CONTAINER ID : 12 ===
│   │           │           D
│   │           └── === CONTAINER ID : 5 ===
│   │               GGG
│   │               └── === CONTAINER ID : 9 ===
│   │                   DD
│   │                   └── === CONTAINER ID : 12 ===
│   │                       D
│   └── === CONTAINER ID : 8 ===
│       CC
│       └── === CONTAINER ID : 9 ===
│           DD
│           └── === CONTAINER ID : 12 ===
│               D
└── === CONTAINER ID : 11 ===
    C
    └── === CONTAINER ID : 12 ===
        D""",
            """```mermaid
flowchart TD
    13["A"]
    13 --> 10
    10["B C"]
    10 --> 7
    7["AA BB"]
    7 --> 1
    1["AAA"]
    1 --> 6
    6["CCC"]
    6 --> 3
    3["DDD EEE"]
    3 --> 9
    9["DD"]
    9 --> 12
    12["D"]
    6 --> 4
    4["FFF"]
    4 --> 9
    6 --> 5
    5["GGG"]
    5 --> 9
    7 --> 2
    2["BBB"]
    2 --> 6
    10 --> 8
    8["CC"]
    8 --> 9
    13 --> 11
    11["C"]
    11 --> 12
```""",
        ]
    ],
)
def test_parser_story_full(ink_code, expected_lines, expected_tree, expected_mermaid):
    # With
    Container.reset_id_counter()

    # When
    actual_lines = clean_lines(ink_code)

    # Then
    assert len(actual_lines) == len(expected_lines)
    for k in range(len(actual_lines)):
        assert actual_lines[k].text == expected_lines[k]["text"]
        assert actual_lines[k].level == expected_lines[k]["level"]
        assert actual_lines[k].line_type is expected_lines[k]["line_type"]

    # When
    actual_container = parse_story(actual_lines)
    actual_tree = actual_container.print_tree()
    actual_mermaid = actual_container.container_to_mermaid()

    assert actual_tree == expected_tree
    assert actual_mermaid == expected_mermaid
