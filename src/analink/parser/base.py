from pydantic import BaseModel, Field, PrivateAttr, computed_field
from typing import Optional
from typing import ClassVar
from analink.parser.condition import Condition


class Container(BaseModel):
    # Instance fields
    _id: int = PrivateAttr(default_factory=lambda: Container._get_next_id())
    content: Optional[str] = None
    children: list[tuple[Condition, "Container", Optional[int]]] = Field(
        default_factory=list
    )  # Added container_id for condition evaluation
    is_choice: bool = False
    choice_text: Optional[str] = None
    sticky: bool = False

    _next_id: ClassVar[int] = 1

    @computed_field
    @property
    def item_id(self) -> int:
        return self._id

    @classmethod
    def _get_next_id(cls) -> int:
        """Get the next available ID and increment the counter"""
        current_id = cls._next_id
        cls._next_id += 1
        return current_id

    @classmethod
    def reset_id_counter(cls) -> None:
        """Reset the ID counter (useful for testing)"""
        cls._next_id = 1
