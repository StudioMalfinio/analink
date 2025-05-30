from analink.parser.utils import count_leading_chars
from analink.models import Choice
import re

def extract_parts(text):
    # Use re.DOTALL flag to make . match newlines too
    pattern = r'(.*)(?<!\\)\[([^\]]*)\](.*)'
    
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

def parse_only_once_choice(buffer: list[str], line_number: int) -> Choice:
    display_text, text_after_choice = extract_parts("\n".join(buffer))
    return Choice(
        display_text=display_text,
        text_after_choice=text_after_choice,
        line_number=line_number,
        sticky=False,
    )


def parse_choices(lines:str)->list[Choice]:
    lines_list = lines.split('\n')
    i = 0
    choices=[]
    while i < len(lines_list):
        line = lines_list[i]
        stripped = line.strip()
        if count_leading_chars(stripped, "*") > 0:
            line_number = i
            choice_buffer = [line.lstrip("*").strip()]
            i += 1
            while i < len(lines_list):
                line = lines_list[i]
                stripped = line.strip()
                if count_leading_chars(stripped, "*") == 0:
                    choice_buffer.append(stripped)
                    i += 1
                else:
                    # Don't increment i here - we want to process this line in the outer loop
                    break
            # print(choice_buffer)
            choices.append(parse_only_once_choice(choice_buffer, line_number))
        else:
            i += 1
    return choices