from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from analink.parser.condition import (
    BinaryCondition,
    Condition,
    ConditionType,
    UnaryCondition,
)
from analink.parser.status import ContainerState, ContainerStatus


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
            expected_value=ContainerStatus.ACTIVE,
        )
        assert condition.condition_type == ConditionType.STATUS_EQUALS
        assert condition.expected_value == ContainerStatus.ACTIVE

    def test_status_equals_invalid_type(self):
        with pytest.raises(ValidationError) as exc_info:
            UnaryCondition(
                condition_type=ConditionType.STATUS_EQUALS, expected_value="invalid"
            )
        assert "STATUS_EQUALS requires ContainerStatus" in str(exc_info.value)

    def test_seen_count_gt_valid(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_GT, expected_value=5
        )
        assert condition.expected_value == 5

    def test_seen_count_gt_negative_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            UnaryCondition(
                condition_type=ConditionType.SEEN_COUNT_GT, expected_value=-1
            )
        assert "requires non-negative integer" in str(exc_info.value)

    def test_seen_count_lt_non_integer_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            UnaryCondition(
                condition_type=ConditionType.SEEN_COUNT_LT, expected_value="not_int"
            )
        assert "requires non-negative integer" in str(exc_info.value)

    def test_seen_count_eq_valid(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_EQ, expected_value=0
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

    def test_variable_gt_invalid_value_type(self):
        with pytest.raises(ValidationError) as exc_info:
            UnaryCondition(
                condition_type=ConditionType.VARIABLE_GT,
                expected_value={"variable": "score", "value": "not_int"},
            )
        assert "requires 'value' to be int" in str(exc_info.value)


class TestUnaryConditionEvaluation:
    def test_status_equals_true(self):
        condition = UnaryCondition(
            condition_type=ConditionType.STATUS_EQUALS,
            expected_value=ContainerStatus.ACTIVE,
        )
        container_state = Mock(spec=ContainerState)
        container_state.status = ContainerStatus.ACTIVE

        assert condition.evaluate(container_state=container_state) is True

    def test_status_equals_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.STATUS_EQUALS,
            expected_value=ContainerStatus.ACTIVE,
        )
        container_state = Mock(spec=ContainerState)
        container_state.status = ContainerStatus.DISABLED

        assert condition.evaluate(container_state=container_state) is False

    def test_status_equals_no_container_state(self):
        condition = UnaryCondition(
            condition_type=ConditionType.STATUS_EQUALS,
            expected_value=ContainerStatus.ACTIVE,
        )
        assert condition.evaluate() is False

    def test_seen_count_gt_true(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_GT, expected_value=5
        )
        container_state = Mock(spec=ContainerState)
        container_state.seen_count = 10

        assert condition.evaluate(container_state=container_state) is True

    def test_seen_count_gt_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_GT, expected_value=5
        )
        container_state = Mock(spec=ContainerState)
        container_state.seen_count = 3

        assert condition.evaluate(container_state=container_state) is False

    def test_seen_count_gt_no_container_state(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_GT, expected_value=5
        )
        assert condition.evaluate() is False

    def test_seen_count_lt_true(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_LT, expected_value=10
        )
        container_state = Mock(spec=ContainerState)
        container_state.seen_count = 5

        assert condition.evaluate(container_state=container_state) is True

    def test_seen_count_lt_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_LT, expected_value=10
        )
        container_state = Mock(spec=ContainerState)
        container_state.seen_count = 15

        assert condition.evaluate(container_state=container_state) is False

    def test_seen_count_lt_no_container_state(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_LT, expected_value=10
        )
        assert condition.evaluate() is False

    def test_seen_count_eq_true(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_EQ, expected_value=7
        )
        container_state = Mock(spec=ContainerState)
        container_state.seen_count = 7

        assert condition.evaluate(container_state=container_state) is True

    def test_seen_count_eq_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_EQ, expected_value=7
        )
        container_state = Mock(spec=ContainerState)
        container_state.seen_count = 8

        assert condition.evaluate(container_state=container_state) is False

    def test_seen_count_eq_no_container_state(self):
        condition = UnaryCondition(
            condition_type=ConditionType.SEEN_COUNT_EQ, expected_value=7
        )
        assert condition.evaluate() is False

    def test_variable_eq_true(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_EQ,
            expected_value={"variable": "health", "value": 100},
        )
        game_state = {"health": 100, "mana": 50}

        assert condition.evaluate(game_state=game_state) is True

    def test_variable_eq_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_EQ,
            expected_value={"variable": "health", "value": 100},
        )
        game_state = {"health": 75, "mana": 50}

        assert condition.evaluate(game_state=game_state) is False

    def test_variable_eq_missing_variable(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_EQ,
            expected_value={"variable": "nonexistent", "value": 100},
        )
        game_state = {"health": 75}

        assert condition.evaluate(game_state=game_state) is False

    def test_variable_eq_no_game_state(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_EQ,
            expected_value={"variable": "health", "value": 100},
        )
        assert condition.evaluate() is False

    def test_variable_gt_true(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_GT,
            expected_value={"variable": "score", "value": 50},
        )
        game_state = {"score": 75}

        assert condition.evaluate(game_state=game_state) is True

    def test_variable_gt_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_GT,
            expected_value={"variable": "score", "value": 50},
        )
        game_state = {"score": 25}

        assert condition.evaluate(game_state=game_state) is False

    def test_variable_gt_missing_variable_defaults_to_zero(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_GT,
            expected_value={"variable": "nonexistent", "value": 5},
        )
        game_state = {"other": 10}

        assert condition.evaluate(game_state=game_state) is False

    def test_variable_gt_no_game_state(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_GT,
            expected_value={"variable": "score", "value": 50},
        )
        assert condition.evaluate() is False

    def test_variable_lt_true(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_LT,
            expected_value={"variable": "lives", "value": 5},
        )
        game_state = {"lives": 2}

        assert condition.evaluate(game_state=game_state) is True

    def test_variable_lt_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_LT,
            expected_value={"variable": "lives", "value": 5},
        )
        game_state = {"lives": 8}

        assert condition.evaluate(game_state=game_state) is False

    def test_variable_lt_missing_variable_defaults_to_zero(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_LT,
            expected_value={"variable": "nonexistent", "value": 5},
        )
        game_state = {"other": 10}

        assert condition.evaluate(game_state=game_state) is True

    def test_variable_lt_no_game_state(self):
        condition = UnaryCondition(
            condition_type=ConditionType.VARIABLE_LT,
            expected_value={"variable": "lives", "value": 5},
        )
        assert condition.evaluate() is False

    def test_turn_gt_true(self):
        condition = UnaryCondition(
            condition_type=ConditionType.TURN_GT, expected_value=10
        )
        assert condition.evaluate(current_turn=15) is True

    def test_turn_gt_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.TURN_GT, expected_value=10
        )
        assert condition.evaluate(current_turn=5) is False

    def test_turn_gt_equal_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.TURN_GT, expected_value=10
        )
        assert condition.evaluate(current_turn=10) is False

    def test_unknown_condition_type_returns_false(self):
        condition = UnaryCondition(
            condition_type=ConditionType.STATUS_EQUALS,
            expected_value=ContainerStatus.ACTIVE,
        )
        condition.condition_type = "unknown_type"

        assert condition.evaluate() is False


class TestBinaryCondition:
    def test_and_both_true(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=5)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=3)
        condition = BinaryCondition(left=left, operator="AND", right=right)

        assert condition.evaluate(current_turn=10) is True

    def test_and_left_false(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=15)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=3)
        condition = BinaryCondition(left=left, operator="AND", right=right)

        assert condition.evaluate(current_turn=10) is False

    def test_and_right_false(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=5)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=15)
        condition = BinaryCondition(left=left, operator="AND", right=right)

        assert condition.evaluate(current_turn=10) is False

    def test_and_both_false(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=15)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=20)
        condition = BinaryCondition(left=left, operator="AND", right=right)

        assert condition.evaluate(current_turn=10) is False

    def test_or_both_true(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=5)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=3)
        condition = BinaryCondition(left=left, operator="OR", right=right)

        assert condition.evaluate(current_turn=10) is True

    def test_or_left_true(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=5)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=15)
        condition = BinaryCondition(left=left, operator="OR", right=right)

        assert condition.evaluate(current_turn=10) is True

    def test_or_right_true(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=15)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=5)
        condition = BinaryCondition(left=left, operator="OR", right=right)

        assert condition.evaluate(current_turn=10) is True

    def test_or_both_false(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=15)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=20)
        condition = BinaryCondition(left=left, operator="OR", right=right)

        assert condition.evaluate(current_turn=10) is False

    def test_invalid_operator(self):
        left = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=5)
        right = UnaryCondition(condition_type=ConditionType.TURN_GT, expected_value=3)
        condition = BinaryCondition(left=left, operator="XOR", right=right)

        assert condition.evaluate(current_turn=10) is False

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

        assert outer_condition.evaluate(current_turn=10) is True
        assert outer_condition.evaluate(current_turn=2) is False

    def test_complex_evaluation_with_all_parameters(self):
        container_state = Mock(spec=ContainerState)
        container_state.status = ContainerStatus.ACTIVE
        container_state.seen_count = 8

        game_state = {"health": 75, "mana": 30}

        left = UnaryCondition(
            condition_type=ConditionType.STATUS_EQUALS,
            expected_value=ContainerStatus.ACTIVE,
        )
        right = UnaryCondition(
            condition_type=ConditionType.VARIABLE_GT,
            expected_value={"variable": "health", "value": 50},
        )
        condition = BinaryCondition(left=left, operator="AND", right=right)

        result = condition.evaluate(
            container_state=container_state, game_state=game_state, current_turn=15
        )
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
