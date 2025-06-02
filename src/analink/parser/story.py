# from typing import Any, Optional

# from pydantic import BaseModel, Field

# from analink.parser.condition import Condition
# from analink.parser.container import Container
# from analink.parser.status import ContainerState, ContainerStatus


# class Story(BaseModel):
#     """Main story container with state management"""

#     root: Container
#     global_state: dict[int, ContainerState] = Field(default_factory=dict)
#     game_state: dict[str, Any] = Field(default_factory=dict)
#     # TODO: Any for game state is bad, variable have given type , maybe create a variable class??
#     current_turn: int = 0

#     def get_container_state(self, container_id: int) -> ContainerState:
#         """Get or create container state"""
#         if container_id not in self.global_state:
#             self.global_state[container_id] = ContainerState()
#         return self.global_state[container_id]

#     def get_available_content(
#         self, current_container: Optional[Container] = None
#     ) -> list[Container]:
#         """Get all currently available content based on conditions"""
#         if current_container is None:
#             current_container = self.root

#         available = []

#         # Add current container if it has content
#         if current_container.content:
#             available.append(current_container)
#             # Mark as seen
#             state = self.get_container_state(current_container.item_id)
#             state.seen_count += 1
#             state.last_seen_turn = self.current_turn
#             # TODO : probably not a unique status but more like a set of flag should be in ContainerState
#             if state.status == ContainerStatus.NOT_SEEN:
#                 state.status = ContainerStatus.SEEN

#         # Check children based on conditions
#         for condition, child in current_container.children:
#             if self._evaluate_condition(condition, child.item_id):
#                 available.extend(self.get_available_content(child))

#         return available

#     def _evaluate_condition(self, condition: Condition, container_id: int) -> bool:
#         """Evaluate any condition with optional container context"""
#         container_state = self.get_container_state(container_id)
#         return condition.evaluate(container_state, self.game_state, self.current_turn)

#     def click_choice(self, choice_id: int) -> None:
#         """Mark a choice as clicked"""
#         state = self.get_container_state(choice_id)
#         # TODO : probably not a unique status but more like a set of flag should be in ContainerState
#         state.status = ContainerStatus.CLICKED
#         self.current_turn += 1

#     def set_container_status(self, container_id: int, status: ContainerStatus) -> None:
#         """Manually set a container's status"""
#         state = self.get_container_state(container_id)
#         state.status = status

#     def set_variable(self, variable_name: str, value: Any) -> None:
#         """Set a game variable"""
#         self.game_state[variable_name] = value

#     def get_variable(self, variable_name: str, default: Any = None) -> Any:
#         """Get a game variable"""
#         return self.game_state.get(variable_name, default)
