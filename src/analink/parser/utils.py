def count_leading_chars(line: str, char: str) -> int:
    """Count leading characters (for nesting level)"""
    count = 0
    for c in line:
        if c == char:
            count += 1
        elif c == " " or c == "\t":
            continue
        else:
            break
    return count
