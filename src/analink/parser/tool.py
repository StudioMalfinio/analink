from analink.parser.condition import Condition, ConditionType, UnaryCondition
from analink.parser.container import Container
from analink.parser.line import InkLine, InkLineType
from analink.parser.status import ContainerStatus

fake_condition = UnaryCondition(
    condition_type=ConditionType.STATUS_EQUALS, expected_value=ContainerStatus.ACTIVE
)


class ParseState:
    """Helper class to manage parsing state and avoid infinite loops"""

    def __init__(self, lines: list[InkLine]):
        self.lines = lines
        self.index = 0

    def current_line(self) -> InkLine:
        return self.lines[self.index]

    def transform_consumed_lines(self) -> None:
        current_line = self.current_line()
        self.lines[self.index] = InkLine(
            level=current_line.level,
            line_type=InkLineType.BASE,
            text=current_line.text,
            raw_line=current_line.raw_line,
            line_number=current_line.line_number,
        )

    def advance(self):
        self.index += 1

    def has_more(self) -> bool:
        return self.index < len(self.lines)


def parse_story_recursive(
    state: ParseState,
    target_level: int,
    verbose=False,
) -> Container:
    """
    Parse Ink story lines into a Container structure using a state object.

    Args:
        state: ParseState object managing current position
        target_level: The level we're currently parsing at
    """
    children: list[tuple[Condition, Container]] = []
    content = ""
    # Track containers at current level for gather processing
    while state.has_more():
        current_line = state.current_line()

        if current_line.line_type == InkLineType.BASE:
            # We will merge later for simplicity
            content = current_line.text
            state.advance()

        elif current_line.line_type == InkLineType.CHOICE:
            if current_line.level > target_level:
                # This choice starts a new deeper container
                state.transform_consumed_lines()
                child_container = parse_story_recursive(state, current_line.level)
                child_tuple = (fake_condition, child_container)
                children.append(child_tuple)

                # containers_at_level.append(child_tuple)

            elif current_line.level == target_level:
                break
            else:  # current_line.level < target_level
                break

        elif current_line.line_type == InkLineType.GATHER:
            if current_line.level > target_level:
                # Deeper gather
                # No idea what to do for the moment
                print(current_line.text, content)
                for _, cont in children:
                    print(cont.content)
                state.transform_consumed_lines()
                gather_container = parse_story_recursive(state, current_line.level - 1)
                gather_tuple = (fake_condition, gather_container)
                if len(children) == 0:
                    return gather_container
                else:
                    # not at the children but a the leaves of all the container inside
                    for child_condition, child_container in children:
                        child_container.append_to_leaves(gather_tuple)
                    break

            elif current_line.level == target_level:
                break
            else:  # current_line.level < target_level
                # Higher level gather - return to parent
                break
    container = Container(content=content, children=children)
    return container


def parse_story(lines: list[InkLine]) -> Container:
    """
    Main entry point for parsing Ink story lines.
    """
    state = ParseState(lines)
    return parse_story_recursive(state, 0)
