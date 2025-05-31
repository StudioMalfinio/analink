from pydantic import BaseModel, model_validator
from enum import Enum
from typing import Union, Optional, Any
from analink.parser.status import ContainerStatus, ContainerState


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
    # Add more condition types as needed


class UnaryCondition(BaseModel):
    """Single condition check - pure description of what to check"""

    condition_type: ConditionType
    expected_value: Union[ContainerStatus, int, str, bool, dict[str, int]]

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

            case (
                ConditionType.SEEN_COUNT_GT
                | ConditionType.SEEN_COUNT_LT
                | ConditionType.SEEN_COUNT_EQ
                | ConditionType.TURN_GT
            ):
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
                if not isinstance(expected_value["value"], int):
                    raise ValueError(
                        f"{condition_type.value} requires 'value' to be int"
                    )
                # 'value' can be any type (int, str, bool, etc.)

        return self

    def evaluate(
        self,
        container_state: Optional[ContainerState] = None,
        game_state: Optional[dict[str, Any]] = None,
        current_turn: int = 0,
    ) -> bool:
        """Evaluate this condition against provided state"""
        match self.condition_type:
            case ConditionType.STATUS_EQUALS:
                if container_state is None:
                    return False
                return container_state.status == self.expected_value

            case ConditionType.SEEN_COUNT_GT:
                if container_state is None:
                    return False
                return container_state.seen_count > self.expected_value

            case ConditionType.SEEN_COUNT_LT:
                if container_state is None:
                    return False
                return container_state.seen_count < self.expected_value

            case ConditionType.SEEN_COUNT_EQ:
                if container_state is None:
                    return False
                return container_state.seen_count == self.expected_value

            case ConditionType.VARIABLE_EQ:
                if game_state is None:
                    return False
                var_name = self.expected_value["variable"]
                var_value = self.expected_value["value"]
                return game_state.get(var_name) == var_value

            case ConditionType.VARIABLE_GT:
                if game_state is None:
                    return False
                var_name = self.expected_value["variable"]
                var_value = self.expected_value["value"]
                return game_state.get(var_name, 0) > var_value

            case ConditionType.VARIABLE_LT:
                if game_state is None:
                    return False
                var_name = self.expected_value["variable"]
                var_value = self.expected_value["value"]
                return game_state.get(var_name, 0) < var_value

            case ConditionType.TURN_GT:
                return current_turn > self.expected_value

            case _:
                return False


class BinaryCondition(BaseModel):
    """AND/OR condition with two operands"""

    left: Union["UnaryCondition", "BinaryCondition"]
    operator: str  # "AND" or "OR"
    right: Union["UnaryCondition", "BinaryCondition"]

    def evaluate(
        self,
        container_state: Optional[ContainerState] = None,
        game_state: Optional[dict[str, Any]] = None,
        current_turn: int = 0,
    ) -> bool:
        """Evaluate this binary condition"""
        left_result = self.left.evaluate(container_state, game_state, current_turn)
        right_result = self.right.evaluate(container_state, game_state, current_turn)

        if self.operator == "AND":
            return left_result and right_result
        elif self.operator == "OR":
            return left_result or right_result
        return False


# Union type for any condition
Condition = Union[UnaryCondition, BinaryCondition]
