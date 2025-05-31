from enum import Enum
from typing import Optional

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
