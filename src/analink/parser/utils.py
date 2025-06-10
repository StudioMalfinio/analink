import re


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


def extract_parts(text):
    # Use re.DOTALL flag to make . match newlines too
    pattern = r"(.*)(?<!\\)\[([^\]]*)\](.*)"
    bracket_pattern = r"(?<!\\)\[[^\]]*\]"
    matches = re.findall(bracket_pattern, text, re.DOTALL)
    if len(matches) > 1:
        raise ValueError(f"Multiple bracket patterns found: {len(matches)} occurrences")
    match = re.match(pattern, text, re.DOTALL)

    if match:
        before, inside, after = match.groups()

        # Version 1: before + inside
        version1 = before + inside

        # Version 2: before + after
        version2 = before + after

        return version1, version2
    else:
        # No brackets found, return original text twice
        return text, text
