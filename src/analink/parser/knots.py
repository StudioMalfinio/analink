from pydantic import Field
from analink.parser.base import BaseObject
from analink.parser.choice import Choice
from analink.parser.choice import parse_choices

class Content(BaseObject):
    content : str

class Knot(BaseObject):
    header: Content
    choices: list[Choice] = Field(default_factory=list)



def parse_knots(lines: str) -> Knot:
    lines_list = lines.split("*")
    header = lines_list[0]
    choices = "*"+"*".join(lines_list[1:])
    return Knot(key_id=0, choices=parse_choices(choices), header=Content(content=header))
