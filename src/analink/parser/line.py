from enum import Enum
from typing import Optional

from pydantic import BaseModel


class InkLineType(Enum):
    CHOICE = "choice"
    GATHER = "gather"
    BASE = "base_content"


class InkLine(BaseModel):
    """Represents a parsed line from Ink code"""

    level: int  # Number of * or - characters
    line_type: InkLineType
    text: str
    raw_line: str
    line_number: int


def count_leading_chars(line: str, char: str) -> tuple[int, str]:
    """Count leading characters (for nesting level) and return the text without the leading char"""
    count = 0
    idx = 0
    for c in line:
        if c == char:
            count += 1
            idx += 1
        elif c == " " or c == "\t":
            idx += 1
            continue
        else:
            break
    return count, line[idx:]


def parse_line(line: str, line_number: int) -> Optional[InkLine]:
    """Parse a single line of Ink code"""
    stripped = line.strip()
    # Skip empty lines and comments
    if not stripped or stripped.startswith("//"):
        return None

    # Skip special directives like -> END
    if stripped.startswith("->"):
        return None

    # Check for choices (stars) and gathers (dashes) in the stripped line
    choice_count, text_choice = count_leading_chars(stripped, "*")
    gather_count, text_gather = count_leading_chars(stripped, "-")
    if choice_count > 0:
        return InkLine(
            level=choice_count,
            line_type=InkLineType.CHOICE,
            text=text_choice,
            raw_line=line,
            line_number=line_number,
        )
    if gather_count > 0:
        return InkLine(
            level=gather_count,
            line_type=InkLineType.GATHER,
            text=text_gather,
            raw_line=line,
            line_number=line_number,
        )

    return InkLine(
        level=-1,
        line_type=InkLineType.BASE,
        text=stripped,
        raw_line=line,
        line_number=line_number,
    )


def clean_lines(ink_code: str, clean_text_sep=" ") -> list[InkLine]:
    lines: list[InkLine] = []
    raw_lines = ink_code.strip().split("\n")
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        parsed_line = parse_line(line, i + 1)
        if parsed_line is None:
            i += 1
            continue
        if parsed_line.line_type is InkLineType.BASE:
            if lines == []:
                lines.append(
                    InkLine(
                        level=0,
                        line_type=InkLineType.BASE,
                        text=parsed_line.text,
                        raw_line=parsed_line.raw_line,
                        line_number=parsed_line.line_number,
                    )
                )
            else:
                lines[-1] = InkLine(
                    level=lines[-1].level,
                    line_type=lines[-1].line_type,
                    text=lines[-1].text + clean_text_sep + parsed_line.text,
                    raw_line=lines[-1].text + "\n" + parsed_line.raw_line,
                    line_number=lines[-1].line_number,
                )
        else:
            lines.append(parsed_line)
        i += 1
    return lines
