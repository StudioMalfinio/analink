from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, model_validator

from analink.core.status import ContainerStateProvider, ContainerStatus


class ConditionType(Enum):
    """Types of conditions we can check"""

    STATUS_EQUALS = "status_equals"  # Check if container status equals X
    SEEN_COUNT_GT = "seen_count_gt"  # Check if seen count > X
    SEEN_COUNT_LT = "seen_count_lt"  # Check if seen count < X
    SEEN_COUNT_EQ = "seen_count_eq"  # Check if seen count == X
    VARIABLE_EQ = "variable_eq"  # Check if game variable == X
    VARIABLE_GT = "variable_gt"  # Check if game variable > X
    VARIABLE_LT = "variable_lt"  # Check if game variable < X
    TURN_GT = "turn_gt"  # Check if current turn > X


class UnaryCondition(BaseModel):
    """Single condition check - pure description of what to check"""

    condition_type: ConditionType
    container_reference: Optional[str] = (
        None  # Reference to container for container-based conditions
    )
    expected_value: Union[ContainerStatus, int, str, bool, dict[str, Union[str, int]]]

    @model_validator(mode="after")
    def validate_expected_value_type(self) -> "UnaryCondition":
        """Validate that expected_value matches the condition_type requirements"""
        condition_type = self.condition_type
        expected_value = self.expected_value

        match condition_type:
            case ConditionType.STATUS_EQUALS:
                if not isinstance(expected_value, ContainerStatus):
                    raise ValueError(
                        f"STATUS_EQUALS requires ContainerStatus, got {type(expected_value)}"
                    )
                if not self.container_reference:
                    raise ValueError("STATUS_EQUALS requires container_reference")

            case (
                ConditionType.SEEN_COUNT_GT
                | ConditionType.SEEN_COUNT_LT
                | ConditionType.SEEN_COUNT_EQ
            ):
                if not isinstance(expected_value, int) or expected_value < 0:
                    raise ValueError(
                        f"{condition_type.value} requires non-negative integer, got {expected_value}"
                    )
                if not self.container_reference:
                    raise ValueError(
                        f"{condition_type.value} requires container_reference"
                    )

            case ConditionType.TURN_GT:
                if not isinstance(expected_value, int) or expected_value < 0:
                    raise ValueError(
                        f"{condition_type.value} requires non-negative integer, got {expected_value}"
                    )

            case (
                ConditionType.VARIABLE_EQ
                | ConditionType.VARIABLE_GT
                | ConditionType.VARIABLE_LT
            ):
                if not isinstance(expected_value, dict):
                    raise ValueError(
                        f"{condition_type.value} requires dict with 'variable' and 'value' keys"
                    )
                if "variable" not in expected_value or "value" not in expected_value:
                    raise ValueError(
                        f"{condition_type.value} requires dict with 'variable' and 'value' keys"
                    )
                if not isinstance(expected_value["variable"], str):
                    raise ValueError(
                        f"{condition_type.value} requires 'variable' to be string"
                    )

        return self

    def evaluate(self, provider: ContainerStateProvider) -> bool:
        """Evaluate this condition using the provider"""
        match self.condition_type:
            case ConditionType.STATUS_EQUALS:
                container_state = provider.get_container_state(self.container_reference)
                if container_state is None:
                    return False
                return container_state.status == self.expected_value

            case ConditionType.SEEN_COUNT_GT:
                container_state = provider.get_container_state(self.container_reference)
                if container_state is None:
                    return False
                return container_state.seen_count > self.expected_value  # type: ignore

            case ConditionType.SEEN_COUNT_LT:
                container_state = provider.get_container_state(self.container_reference)
                if container_state is None:
                    return False
                return container_state.seen_count < self.expected_value  # type: ignore

            case ConditionType.SEEN_COUNT_EQ:
                container_state = provider.get_container_state(self.container_reference)
                if container_state is None:
                    return False
                return container_state.seen_count == self.expected_value

            case ConditionType.VARIABLE_EQ:
                game_state = provider.get_game_variables()
                var_name: str = self.expected_value["variable"]  # type: ignore[index, assignment, no-redef]
                var_value = self.expected_value["value"]  # type: ignore[index]
                return game_state.get(var_name) == var_value

            case ConditionType.VARIABLE_GT:
                game_state = provider.get_game_variables()
                var_name: str = self.expected_value["variable"]  # type: ignore[index, assignment, no-redef]
                var_value = self.expected_value["value"]  # type: ignore[index]
                return game_state.get(var_name, 0) > var_value

            case ConditionType.VARIABLE_LT:
                game_state = provider.get_game_variables()
                var_name: str = self.expected_value["variable"]  # type: ignore[index, assignment, no-redef]
                var_value = self.expected_value["value"]  # type: ignore[index]
                return game_state.get(var_name, 0) < var_value

            case ConditionType.TURN_GT:
                current_turn = provider.get_current_turn()
                return current_turn > self.expected_value  # type: ignore

            case _:
                return False


class BinaryCondition(BaseModel):
    """AND/OR condition with two operands"""

    left: Union["UnaryCondition", "BinaryCondition"]
    operator: str  # "AND" or "OR"
    right: Union["UnaryCondition", "BinaryCondition"]

    def evaluate(self, provider: ContainerStateProvider) -> bool:
        """Evaluate this binary condition using the provider"""
        left_result = self.left.evaluate(provider)
        right_result = self.right.evaluate(provider)

        if self.operator == "AND":
            return left_result and right_result
        elif self.operator == "OR":
            return left_result or right_result
        return False


# Union type for any condition
Condition = Union[UnaryCondition, BinaryCondition]
