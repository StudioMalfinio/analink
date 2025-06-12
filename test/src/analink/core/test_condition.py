from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from analink.core.condition import (
    BinaryCondition,
    Condition,
    ConditionType,
    ContainerStateProvider,
    UnaryCondition,
)
from analink.core.status import ContainerState, ContainerStatus


class TestConditionType:
    def test_all_enum_values(self):
        expected_values = {
            "status_equals",
            "seen_count_gt",
            "seen_count_lt",
            "seen_count_eq",
            "variable_eq",
            "variable_gt",
            "variable_lt",
            "turn_gt",
        }
        actual_values = {ct.value for ct in ConditionType}
        assert actual_values == expected_values


class TestUnaryCondition:
    def test_status_equals_valid(self):
        condition = UnaryCondition(
            condition_type=ConditionType.STATUS_EQUALS,
            container_reference="test_container",
            expected_value=ContainerStatus.ACTIVE,
        )
        assert condition.condition_type == ConditionType.STATUS_EQUALS
        assert condition.container_reference == "test_container"
        assert condition.expected_value == ContainerStatus.ACTIVE

    def test_status_equals_invalid_type(self):
        with pytest.raises(ValidationError) as exc_info:
            UnaryCondition(
                condition_type=ConditionType.STATUS_EQUALS,
                container_reference="test_container",
                expected_value="invalid",
            )
        assert "STATUS_EQUALS requires ContainerStatus" in str(exc_info.value)

    def test_status_equals_missing_container_reference(self):
        with pytest.raises(ValidationError) as exc_info:
            UnaryCondition(
                condition_type=ConditionType.STATUS_EQUALS,
                expected_value=ContainerStatus.ACTIVE,
            )
        assert "STATUS_EQUALS requires container_reference" in str(exc_info.value)

    def test_seen_count_gt_valid(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_GT,
            container_reference="test_container",
            expected_value=5,
        )
        assert condition.expected_value == 5
        assert condition.container_reference == "test_container"

    def test_seen_count_gt_missing_container_reference(self):
        with pytest.raises(ValidationError) as exc_info:
            UnaryCondition(condition_type=ConditionType.SEEN_COUNT_GT, expected_value=5)
        assert "seen_count_gt requires container_reference" in str(exc_info.value)

    def test_seen_count_gt_negative_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            UnaryCondition(
                condition_type=ConditionType.SEEN_COUNT_GT,
                container_reference="test_container",
                expected_value=-1,
            )
        assert "requires non-negative integer" in str(exc_info.value)

    def test_seen_count_lt_non_integer_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            UnaryCondition(
                condition_type=ConditionType.SEEN_COUNT_LT,
                container_reference="test_container",
                expected_value="not_int",
            )
        assert "requires non-negative integer" in str(exc_info.value)

    def test_seen_count_eq_valid(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_EQ,
            container_reference="test_container",
            expected_value=0,
        )
        assert condition.expected_value == 0

    def test_turn_gt_valid(self):
        condition = UnaryCondition(
            condition_type=ConditionType.TURN_GT, expected_value=10
        )
        assert condition.expected_value == 10

    def test_variable_eq_valid(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_EQ,
            expected_value={"variable": "health", "value": 100},
        )
        assert condition.expected_value == {"variable": "health", "value": 100}

    def test_variable_eq_not_dict(self):
        with pytest.raises(ValidationError) as exc_info:
            UnaryCondition(
                condition_type=ConditionType.VARIABLE_EQ, expected_value="not_dict"
            )
        assert "requires dict with 'variable' and 'value' keys" in str(exc_info.value)

    def test_variable_gt_missing_variable_key(self):
        with pytest.raises(ValidationError) as exc_info:
            UnaryCondition(
                condition_type=ConditionType.VARIABLE_GT, expected_value={"value": 50}
            )
        assert "requires dict with 'variable' and 'value' keys" in str(exc_info.value)

    def test_variable_lt_missing_value_key(self):
        with pytest.raises(ValidationError) as exc_info:
            UnaryCondition(
                condition_type=ConditionType.VARIABLE_LT,
                expected_value={"variable": "mana"},
            )
        assert "requires dict with 'variable' and 'value' keys" in str(exc_info.value)

    def test_variable_eq_invalid_variable_type(self):
        with pytest.raises(ValidationError) as exc_info:
            UnaryCondition(
                condition_type=ConditionType.VARIABLE_EQ,
                expected_value={"variable": 123, "value": 50},
            )
        assert "requires 'variable' to be string" in str(exc_info.value)


class TestUnaryConditionEvaluation:
    def setup_method(self):
        """Set up mock provider for each test"""
        self.provider = Mock(spec=ContainerStateProvider)

    def test_status_equals_true(self):
        condition = UnaryCondition(
            condition_type=ConditionType.STATUS_EQUALS,
            container_reference="test_container",
            expected_value=ContainerStatus.ACTIVE,
        )
        container_state = Mock(spec=ContainerState)
        container_state.status = ContainerStatus.ACTIVE
        self.provider.get_container_state.return_value = container_state

        assert condition.evaluate(self.provider) is True
        self.provider.get_container_state.assert_called_once_with("test_container")

    def test_status_equals_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.STATUS_EQUALS,
            container_reference="test_container",
            expected_value=ContainerStatus.ACTIVE,
        )
        container_state = Mock(spec=ContainerState)
        container_state.status = ContainerStatus.DISABLED
        self.provider.get_container_state.return_value = container_state

        assert condition.evaluate(self.provider) is False

    def test_status_equals_no_container_state(self):
        condition = UnaryCondition(
            condition_type=ConditionType.STATUS_EQUALS,
            container_reference="missing_container",
            expected_value=ContainerStatus.ACTIVE,
        )
        self.provider.get_container_state.return_value = None

        assert condition.evaluate(self.provider) is False

    def test_seen_count_gt_true(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_GT,
            container_reference="test_container",
            expected_value=5,
        )
        container_state = Mock(spec=ContainerState)
        container_state.seen_count = 10
        self.provider.get_container_state.return_value = container_state

        assert condition.evaluate(self.provider) is True

    def test_seen_count_gt_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_GT,
            container_reference="test_container",
            expected_value=5,
        )
        container_state = Mock(spec=ContainerState)
        container_state.seen_count = 3
        self.provider.get_container_state.return_value = container_state

        assert condition.evaluate(self.provider) is False

    def test_seen_count_gt_no_container_state(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_GT,
            container_reference="missing_container",
            expected_value=5,
        )
        self.provider.get_container_state.return_value = None

        assert condition.evaluate(self.provider) is False

    def test_seen_count_lt_true(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_LT,
            container_reference="test_container",
            expected_value=10,
        )
        container_state = Mock(spec=ContainerState)
        container_state.seen_count = 5
        self.provider.get_container_state.return_value = container_state

        assert condition.evaluate(self.provider) is True

    def test_seen_count_lt_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_LT,
            container_reference="test_container",
            expected_value=10,
        )
        container_state = Mock(spec=ContainerState)
        container_state.seen_count = 15
        self.provider.get_container_state.return_value = container_state

        assert condition.evaluate(self.provider) is False

    def test_seen_count_lt_no_container_state(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_LT,
            container_reference="missing_container",
            expected_value=10,
        )
        self.provider.get_container_state.return_value = None

        assert condition.evaluate(self.provider) is False

    def test_seen_count_eq_true(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_EQ,
            container_reference="test_container",
            expected_value=7,
        )
        container_state = Mock(spec=ContainerState)
        container_state.seen_count = 7
        self.provider.get_container_state.return_value = container_state

        assert condition.evaluate(self.provider) is True

    def test_seen_count_eq_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_EQ,
            container_reference="test_container",
            expected_value=7,
        )
        container_state = Mock(spec=ContainerState)
        container_state.seen_count = 8
        self.provider.get_container_state.return_value = container_state

        assert condition.evaluate(self.provider) is False

    def test_seen_count_eq_no_container_state(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_EQ,
            container_reference="missing_container",
            expected_value=7,
        )
        self.provider.get_container_state.return_value = None

        assert condition.evaluate(self.provider) is False

    def test_variable_eq_true(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_EQ,
            expected_value={"variable": "health", "value": 100},
        )
        self.provider.get_game_variables.return_value = {"health": 100, "mana": 50}

        assert condition.evaluate(self.provider) is True

    def test_variable_eq_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_EQ,
            expected_value={"variable": "health", "value": 100},
        )
        self.provider.get_game_variables.return_value = {"health": 75, "mana": 50}

        assert condition.evaluate(self.provider) is False

    def test_variable_eq_missing_variable(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_EQ,
            expected_value={"variable": "nonexistent", "value": 100},
        )
        self.provider.get_game_variables.return_value = {"health": 75}

        assert condition.evaluate(self.provider) is False

    def test_variable_gt_true(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_GT,
            expected_value={"variable": "score", "value": 50},
        )
        self.provider.get_game_variables.return_value = {"score": 75}

        assert condition.evaluate(self.provider) is True

    def test_variable_gt_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_GT,
            expected_value={"variable": "score", "value": 50},
        )
        self.provider.get_game_variables.return_value = {"score": 25}

        assert condition.evaluate(self.provider) is False

    def test_variable_gt_missing_variable_defaults_to_zero(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_GT,
            expected_value={"variable": "nonexistent", "value": 5},
        )
        self.provider.get_game_variables.return_value = {"other": 10}

        assert condition.evaluate(self.provider) is False

    def test_variable_lt_true(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_LT,
            expected_value={"variable": "lives", "value": 5},
        )
        self.provider.get_game_variables.return_value = {"lives": 2}

        assert condition.evaluate(self.provider) is True

    def test_variable_lt_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_LT,
            expected_value={"variable": "lives", "value": 5},
        )
        self.provider.get_game_variables.return_value = {"lives": 8}

        assert condition.evaluate(self.provider) is False

    def test_variable_lt_missing_variable_defaults_to_zero(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_LT,
            expected_value={"variable": "nonexistent", "value": 5},
        )
        self.provider.get_game_variables.return_value = {"other": 10}

        assert condition.evaluate(self.provider) is True

    def test_turn_gt_true(self):
        condition = UnaryCondition(
            condition_type=ConditionType.TURN_GT, expected_value=10
        )
        self.provider.get_current_turn.return_value = 15

        assert condition.evaluate(self.provider) is True

    def test_turn_gt_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.TURN_GT, expected_value=10
        )
        self.provider.get_current_turn.return_value = 5

        assert condition.evaluate(self.provider) is False

    def test_turn_gt_equal_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.TURN_GT, expected_value=10
        )
        self.provider.get_current_turn.return_value = 10

        assert condition.evaluate(self.provider) is False

    def test_unknown_condition_type_returns_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.STATUS_EQUALS,
            container_reference="test_container",
            expected_value=ContainerStatus.ACTIVE,
        )
        condition.condition_type = "unknown_type"

        assert condition.evaluate(self.provider) is False


class TestBinaryCondition:
    def setup_method(self):
        """Set up mock provider for each test"""
        self.provider = Mock(spec=ContainerStateProvider)

    def test_and_both_true(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=5)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=3)
        condition = BinaryCondition(left=left, operator="AND", right=right)
        self.provider.get_current_turn.return_value = 10

        assert condition.evaluate(self.provider) is True

    def test_and_left_false(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=15)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=3)
        condition = BinaryCondition(left=left, operator="AND", right=right)
        self.provider.get_current_turn.return_value = 10

        assert condition.evaluate(self.provider) is False

    def test_and_right_false(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=5)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=15)
        condition = BinaryCondition(left=left, operator="AND", right=right)
        self.provider.get_current_turn.return_value = 10

        assert condition.evaluate(self.provider) is False

    def test_and_both_false(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=15)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=20)
        condition = BinaryCondition(left=left, operator="AND", right=right)
        self.provider.get_current_turn.return_value = 10

        assert condition.evaluate(self.provider) is False

    def test_or_both_true(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=5)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=3)
        condition = BinaryCondition(left=left, operator="OR", right=right)
        self.provider.get_current_turn.return_value = 10

        assert condition.evaluate(self.provider) is True

    def test_or_left_true(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=5)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=15)
        condition = BinaryCondition(left=left, operator="OR", right=right)
        self.provider.get_current_turn.return_value = 10

        assert condition.evaluate(self.provider) is True

    def test_or_right_true(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=15)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=5)
        condition = BinaryCondition(left=left, operator="OR", right=right)
        self.provider.get_current_turn.return_value = 10

        assert condition.evaluate(self.provider) is True

    def test_or_both_false(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=15)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=20)
        condition = BinaryCondition(left=left, operator="OR", right=right)
        self.provider.get_current_turn.return_value = 10

        assert condition.evaluate(self.provider) is False

    def test_invalid_operator(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=5)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=3)
        condition = BinaryCondition(left=left, operator="XOR", right=right)
        self.provider.get_current_turn.return_value = 10

        assert condition.evaluate(self.provider) is False

    def test_nested_binary_conditions(self):
        inner_left = UnaryCondition(
            condition_type=ConditionType.TURN_GT, expected_value=5
        )
        inner_right = UnaryCondition(
            condition_type=ConditionType.TURN_GT, expected_value=3
        )
        inner_condition = BinaryCondition(
            left=inner_left, operator="AND", right=inner_right
        )

        outer_right = UnaryCondition(
            condition_type=ConditionType.TURN_GT, expected_value=20
        )
        outer_condition = BinaryCondition(
            left=inner_condition, operator="OR", right=outer_right
        )

        # Test with turn=10 (inner should be True, outer_right False, so OR = True)
        self.provider.get_current_turn.return_value = 10
        assert outer_condition.evaluate(self.provider) is True

        # Test with turn=2 (inner should be False, outer_right False, so OR = False)
        self.provider.get_current_turn.return_value = 2
        assert outer_condition.evaluate(self.provider) is False

    def test_complex_evaluation_with_mixed_conditions(self):
        container_state = Mock(spec=ContainerState)
        container_state.status = ContainerStatus.ACTIVE
        container_state.seen_count = 8

        self.provider.get_container_state.return_value = container_state
        self.provider.get_game_variables.return_value = {"health": 75, "mana": 30}
        self.provider.get_current_turn.return_value = 15

        left = UnaryCondition(
            condition_type=ConditionType.STATUS_EQUALS,
            container_reference="test_container",
            expected_value=ContainerStatus.ACTIVE,
        )
        right = UnaryCondition(
            condition_type=ConditionType.VARIABLE_GT,
            expected_value={"variable": "health", "value": 50},
        )
        condition = BinaryCondition(left=left, operator="AND", right=right)

        result = condition.evaluate(self.provider)
        assert result is True


class TestConditionUnionType:
    def test_condition_union_accepts_unary(self):
        condition: Condition = UnaryCondition(
            condition_type=ConditionType.TURN_GT, expected_value=5
        )
        assert isinstance(condition, UnaryCondition)

    def test_condition_union_accepts_binary(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=5)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=3)
        condition: Condition = BinaryCondition(left=left, operator="AND", right=right)
        assert isinstance(condition, BinaryCondition)
