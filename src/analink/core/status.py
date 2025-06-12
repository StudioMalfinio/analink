from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class ContainerStatus(Enum):
    """Possible statuses a container can have"""

    CLICKED = "clicked"
    NOT_CLICKED = "not_clicked"
    SEEN = "seen"
    NOT_SEEN = "not_seen"
    DISABLED = "disabled"
    ACTIVE = "active"
    # Add more statuses as needed


class ContainerState(BaseModel):
    """Tracks the state of a specific container"""

    status: ContainerStatus = ContainerStatus.NOT_CLICKED
    seen_count: int = 0
    last_seen_turn: Optional[int] = None
    # Add any other container-specific state you need


class ContainerStateProvider(ABC):
    """Interface for providing container states to conditions"""

    @abstractmethod
    def get_container_state(
        self, container_reference: Optional[str]
    ) -> Optional[ContainerState]:
        """Get container state by reference"""
        pass

    @abstractmethod
    def get_game_variables(self) -> dict[str, Any]:
        """Get current game variables"""
        pass

    @abstractmethod
    def get_current_turn(self) -> int:
        """Get current turn number"""
        pass
