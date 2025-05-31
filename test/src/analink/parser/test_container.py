from unittest.mock import Mock

import pytest

from analink.parser.condition import (
    BinaryCondition,
    Condition,
    ConditionType,
    UnaryCondition,
)
from analink.parser.container import Container


class TestContainerInitialization:
    def setup_method(self):
        Container.reset_id_counter()

    def test_default_initialization(self):
        container = Container()

        assert container.item_id == 1
        assert container.content is None
        assert container.children == []
        assert container.is_choice is False
        assert container.choice_text is None
        assert container.sticky is False

    def test_initialization_with_content(self):
        container = Container(content="Hello World")

        assert container.content == "Hello World"
        assert container.item_id == 1

    def test_initialization_with_all_fields(self):
        mock_condition = Mock(spec=BinaryCondition)
        child_container = Container(content="Child")
        children = [(mock_condition, child_container)]

        container = Container(
            content="Parent content",
            children=children,
            is_choice=True,
            choice_text="Choose this",
            sticky=True,
        )

        assert container.content == "Parent content"
        assert len(container.children) == 1
        assert container.children[0][0] == mock_condition
        assert container.children[0][1] == child_container
        assert container.is_choice is True
        assert container.choice_text == "Choose this"
        assert container.sticky is True

    def test_empty_children_list_by_default(self):
        container = Container()

        assert isinstance(container.children, list)
        assert len(container.children) == 0

    def test_multiple_children(self):
        condition1 = Mock(spec=BinaryCondition)
        condition2 = Mock(spec=BinaryCondition)
        child1 = Container(content="Child 1")
        child2 = Container(content="Child 2")

        children = [(condition1, child1), (condition2, child2)]

        container = Container(children=children)

        assert len(container.children) == 2
        assert container.children[0] == (condition1, child1)
        assert container.children[1] == (condition2, child2)


class TestContainerIdGeneration:
    def setup_method(self):
        Container.reset_id_counter()

    def test_sequential_id_generation(self):
        container1 = Container()
        container2 = Container()
        container3 = Container()

        assert container1.item_id == 1
        assert container2.item_id == 2
        assert container3.item_id == 3

    def test_id_persists_across_modifications(self):
        container = Container()
        original_id = container.item_id

        container.content = "Modified content"
        container.is_choice = True

        assert container.item_id == original_id

    def test_private_id_attribute_access(self):
        container = Container()

        assert hasattr(container, "_id")
        assert container._id == 1

    def test_computed_field_matches_private_attr(self):
        container = Container()

        assert container.item_id == container._id

    def test_id_generation_independent_of_other_fields(self):
        Container.reset_id_counter()

        container1 = Container(content="First")
        container2 = Container(is_choice=True, choice_text="Second")
        container3 = Container(sticky=True)

        assert container1.item_id == 1
        assert container2.item_id == 2
        assert container3.item_id == 3


class TestContainerIdCounter:
    def test_initial_counter_value(self):
        Container.reset_id_counter()
        assert Container._next_id == 1

    def test_counter_increments_after_creation(self):
        Container.reset_id_counter()
        initial_counter = Container._next_id

        Container()

        assert Container._next_id == initial_counter + 1

    def test_get_next_id_increments_counter(self):
        Container.reset_id_counter()

        id1 = Container._get_next_id()
        id2 = Container._get_next_id()
        id3 = Container._get_next_id()

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3
        assert Container._next_id == 4

    def test_reset_id_counter_functionality(self):
        Container.reset_id_counter()
        Container()
        Container()
        Container()

        assert Container._next_id == 4

        Container.reset_id_counter()

        assert Container._next_id == 1

    def test_reset_affects_new_instances(self):
        Container()
        Container()
        Container.reset_id_counter()

        new_container = Container()
        assert new_container.item_id == 1


class TestContainerFields:
    def setup_method(self):
        Container.reset_id_counter()

    def test_content_field_optional(self):
        container = Container()
        assert container.content is None

        container.content = "New content"
        assert container.content == "New content"

        container.content = None
        assert container.content is None

    def test_content_field_string_type(self):
        container = Container(content="String content")
        assert isinstance(container.content, str)
        assert container.content == "String content"

    def test_is_choice_boolean_field(self):
        container = Container()
        assert container.is_choice is False
        assert isinstance(container.is_choice, bool)

        container.is_choice = True
        assert container.is_choice is True

    def test_choice_text_optional_field(self):
        container = Container()
        assert container.choice_text is None

        container.choice_text = "Choose me"
        assert container.choice_text == "Choose me"

        container.choice_text = None
        assert container.choice_text is None

    def test_sticky_boolean_field(self):
        container = Container()
        assert container.sticky is False
        assert isinstance(container.sticky, bool)

        container.sticky = True
        assert container.sticky is True

    def test_children_list_type(self):
        container = Container()
        assert isinstance(container.children, list)

        mock_condition = Mock(spec=Condition)
        child = Container()
        container.children.append((mock_condition, child, 1))

        assert len(container.children) == 1
        assert isinstance(container.children[0], tuple)
        assert len(container.children[0]) == 3

    def test_children_tuple_structure(self):
        mock_condition = Mock(spec=Condition)
        child_container = Container()
        container_id = 123

        container = Container()
        container.children.append((mock_condition, child_container, container_id))

        condition, child, cid = container.children[0]
        assert condition == mock_condition
        assert child == child_container
        assert cid == container_id

    def test_children_with_different_container_id_types(self):
        mock_condition = Mock(spec=Condition)
        child_container = Container()

        container = Container()

        container.children.append((mock_condition, child_container, 42))
        container.children.append((mock_condition, child_container, None))

        assert container.children[0][2] == 42
        assert container.children[1][2] is None


class TestContainerComputedField:
    def setup_method(self):
        Container.reset_id_counter()

    def test_item_id_is_computed_field(self):
        _ = Container()

        assert hasattr(Container, "item_id")
        assert callable(getattr(Container, "item_id").fget)

    def test_item_id_read_only(self):
        container = Container()
        original_id = container.item_id

        with pytest.raises(AttributeError):
            container.item_id = 999

        assert container.item_id == original_id

    def test_item_id_consistency(self):
        container = Container()

        id1 = container.item_id
        id2 = container.item_id
        id3 = container.item_id

        assert id1 == id2 == id3

    def test_item_id_reflects_private_attr(self):
        container = Container()

        assert container.item_id == container._id

        container2 = Container()
        assert container2.item_id == container2._id
        assert container2.item_id != container.item_id


class TestContainerEdgeCases:
    def setup_method(self):
        Container.reset_id_counter()

    def test_nested_containers_in_children(self):
        grandchild = Container(content="Grandchild")
        child = Container(content="Child")
        parent = Container(content="Parent")

        mock_condition = Mock(spec=Condition)
        child.children.append((mock_condition, grandchild, None))
        parent.children.append((mock_condition, child, 1))

        assert len(parent.children) == 1
        assert len(child.children) == 1
        assert parent.children[0][1] == child
        assert child.children[0][1] == grandchild

    def test_same_child_in_multiple_parents(self):
        shared_child = Container(content="Shared")
        parent1 = Container(content="Parent 1")
        parent2 = Container(content="Parent 2")

        mock_condition = Mock(spec=Condition)
        parent1.children.append((mock_condition, shared_child, 1))
        parent2.children.append((mock_condition, shared_child, 2))

        assert parent1.children[0][1] == shared_child
        assert parent2.children[0][1] == shared_child
        assert parent1.children[0][1].item_id == parent2.children[0][1].item_id

    def test_empty_string_content(self):
        container = Container(content="")
        assert container.content == ""
        assert container.content is not None

    def test_boolean_fields_explicit_false(self):
        container = Container(is_choice=False, sticky=False)
        assert container.is_choice is False
        assert container.sticky is False

    def test_modifying_children_list_after_creation(self):
        container = Container()
        original_children = container.children

        mock_condition = Mock(spec=Condition)
        child = Container()
        container.children.append((mock_condition, child, 1))

        assert container.children is original_children
        assert len(container.children) == 1

    def test_choice_text_without_is_choice(self):
        container = Container(choice_text="Some text", is_choice=False)
        assert container.choice_text == "Some text"
        assert container.is_choice is False


class TestContainerIntegration:
    def setup_method(self):
        Container.reset_id_counter()

    def test_complete_container_tree(self):
        mock_condition1 = Mock(spec=UnaryCondition)
        mock_condition1.condition_type = ConditionType.SEEN_COUNT_EQ
        mock_condition1.expected_value = 0
        mock_condition2 = Mock(spec=UnaryCondition)
        mock_condition2.condition_type = ConditionType.SEEN_COUNT_EQ
        mock_condition2.expected_value = 0

        leaf1 = Container(content="Leaf 1", is_choice=True, choice_text="Choice 1")
        leaf2 = Container(content="Leaf 2", sticky=True)

        branch = Container(
            content="Branch",
            children=[(mock_condition1, leaf1), (mock_condition2, leaf2)],
        )

        root = Container(content="Root", children=[(mock_condition1, branch)])

        assert root.item_id == 4
        assert branch.item_id == 3
        assert leaf1.item_id == 1
        assert leaf2.item_id == 2

        assert root.children[0][1] == branch
        assert branch.children[0][1] == leaf1
        assert branch.children[1][1] == leaf2

        assert leaf1.is_choice is True
        assert leaf1.choice_text == "Choice 1"
        assert leaf2.sticky is True

    def test_container_equality_based_on_id(self):
        container1 = Container(content="Same content")
        container2 = Container(content="Same content")

        assert container1.item_id != container2.item_id
        assert container1 != container2

    def test_model_validation_passes(self):
        mock_condition = Mock(spec=UnaryCondition)
        mock_condition.condition_type = ConditionType.SEEN_COUNT_EQ
        mock_condition.expected_value = 0
        child = Container()

        container = Container(
            content="Valid content",
            children=[(mock_condition, child)],
            is_choice=True,
            choice_text="Valid choice",
            sticky=False,
        )

        assert isinstance(container, Container)
        dumped_data = container.model_dump()
        validated_container = Container.model_validate(dumped_data)

        assert validated_container.content == container.content
        assert validated_container.is_choice == container.is_choice
        assert validated_container.choice_text == container.choice_text
        assert validated_container.sticky == container.sticky
        assert len(validated_container.children) == len(container.children)
        assert validated_container.item_id != container.item_id
