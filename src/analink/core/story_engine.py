"""
Core story engine for managing interactive fiction state and flow.
"""

from pathlib import Path
from typing import Any, Callable, List, Optional

import networkx as nx

from analink.core.condition import Condition
from analink.core.parser import Node, NodeType, clean_lines
from analink.core.status import ContainerState, ContainerStateProvider, ContainerStatus
from analink.parser.graph_story import graph_to_mermaid, parse_story


class StoryEngine(ContainerStateProvider):
    """
    Core engine for managing interactive fiction story state, flow, and logic.

    This class handles:
    - Story parsing and graph construction
    - Current position tracking
    - Choice processing and path following
    - Content history management
    - Event callbacks for UI updates
    """

    def __init__(
        self,
        story_text: str,
        let_people_choose_one_choice: bool = True,
        typing_speed: float = 0.05,
        cwd: Optional[Path] = None,
    ):
        """
        Initialize the story engine.

        Args:
            story_text: The ink story content as a string
            typing_speed: Delay between characters for typing effect (0 = instant)
        """
        Node.reset_id_counter()
        self.typing_speed = typing_speed
        self.let_people_choose_one_choice = let_people_choose_one_choice

        # Parse the story
        self.raw_story = clean_lines(story_text, cwd=cwd)
        self.nodes, self.edges = parse_story(self.raw_story)

        # Story state
        self.story_history: List[str] = []
        self.current_node_id = self._find_start_node()
        self._fill_auto_end_node()
        self.is_story_complete = False
        self.graph: nx.DiGraph = nx.DiGraph(self.edges)

        # Event callbacks
        self.on_content_added: Optional[Callable[[str], None]] = None
        self.on_choices_updated: Optional[Callable[[List[Node]], None]] = None
        self.on_story_complete: Optional[Callable[[], None]] = None

        self.node_visited: dict[int, int] = dict()
        self.node_can_be_visited_again: dict[int, bool] = dict()

        # State tracking
        self.container_states: dict[str, ContainerState] = {}
        self.game_variables: dict[str, Any] = {}
        self.current_turn: int = 0

        # Initialize container states for all knots and stitches
        self._initialize_container_states()

    def get_container_state(
        self, container_reference: Optional[str]
    ) -> Optional[ContainerState]:
        """Get container state by reference"""
        if container_reference is None:
            raise AttributeError("Need to give a container reference when querying it")
        return self.container_states.get(container_reference)

    def get_game_variables(self) -> dict[str, Any]:
        """Get current game variables"""
        return self.game_variables

    def get_current_turn(self) -> int:
        """Get current turn number"""
        return self.current_turn

    def _evaluate_condition(self, condition: Optional[Condition]) -> bool:
        """Evaluate a condition using the provider pattern"""
        if not condition:
            return True

        return condition.evaluate(self)  # Pass self as the provider

    def _initialize_container_states(self) -> None:
        """Initialize container states for all knots and stitches"""
        # Initialize states for all knots
        for node_id, node in self.nodes.items():
            if hasattr(node, "knot_name") and node.knot_name != "HEADER":
                knot_key = node.knot_name
                if knot_key not in self.container_states:
                    self.container_states[knot_key] = ContainerState()

                # Initialize states for stitches
                if hasattr(node, "stitch_name") and node.stitch_name != "HEADER":
                    stitch_key = f"{node.knot_name}.{node.stitch_name}"
                    if stitch_key not in self.container_states:
                        self.container_states[stitch_key] = ContainerState()

    def to_mermaid(self):
        return graph_to_mermaid(self.nodes, self.edges)

    @classmethod
    def from_file(cls, filepath: str, **kwargs) -> "StoryEngine":
        """Create a story engine from an ink file."""
        with open(filepath, "r", encoding="utf-8") as f:
            story_text = f.read()
        return cls(story_text, cwd=Path(filepath).parent.resolve(), **kwargs)

    def _fill_auto_end_node(self) -> None:
        # for all the node without children not being END then AUTO_END
        all_nodes = set(self.nodes.keys())
        all_nodes = all_nodes - set([-1, -2, -3])
        source_nodes = set([source for source, _ in self.edges])
        remaining_nodes = all_nodes - source_nodes
        all_nodes_in_edges = set(
            [target for _, target in self.edges] + [source for source, _ in self.edges]
        )
        orphan_nodes = all_nodes - all_nodes_in_edges
        remaining_nodes = remaining_nodes - orphan_nodes
        for node_id in remaining_nodes:
            self.edges.append((node_id, -3))

    def _find_start_node(self) -> int:
        """Find the starting node of the story."""
        if not self.edges:
            if self.nodes:
                candidate_start = list(self.nodes.keys())[0]
            else:
                candidate_start = 1
            self.edges.append((-2, candidate_start))
            return -2

        nodes_with_incoming = {target for source, target in self.edges}
        if -1 not in nodes_with_incoming:
            nodes_with_incoming.add(-1)
        all_nodes = set(self.nodes.keys()) - set([-3])
        all_nodes_in_edges = set(
            [target for _, target in self.edges] + [source for source, _ in self.edges]
        )
        if -2 not in all_nodes_in_edges:
            nodes_with_incoming.add(-2)
        start_candidates = all_nodes - nodes_with_incoming
        if start_candidates:
            candidate_start = min(start_candidates)
        else:
            candidate_start = list(self.nodes.keys())[0]
        if candidate_start == -2:
            return candidate_start
        else:
            self.edges.append((-2, candidate_start))
            return -2

    def start_story(self):
        """Start the story by adding initial content and finding first choices."""
        # Add initial node content to history
        current_node = self.nodes.get(self.current_node_id)
        if current_node and current_node.content:
            self._add_content(current_node.content)

        # Follow the path to find initial choices
        self._follow_story_path()

        # Notify UI of initial state
        self._notify_choices_updated()

    def make_choice(self, choice_node: Node) -> bool:
        """
        Make a choice and advance the story.

        Args:
            choice_node: The chosen node

        Returns:
            True if the choice was valid and processed, False otherwise
        """
        if self.is_story_complete:
            return False

        if choice_node.item_id not in [
            node.item_id for node in self.get_available_choices()
        ]:
            return False  # Invalid choice

        # Update current position
        self.current_node_id = choice_node.item_id

        # Add choice to history
        if choice_node.choice_text:
            self._add_content(f"• {choice_node.choice_text}")

        # Add choice content if different from choice text
        if (
            choice_node.content
            and choice_node.content != choice_node.choice_text
            and choice_node.content.strip()
        ):
            self._add_content(choice_node.content)
        if not choice_node.is_sticky:
            self.node_can_be_visited_again[choice_node.item_id] = False
        # Follow the story path until we find new choices or reach the end
        self._follow_story_path()

        # Notify UI of updated state
        self._notify_choices_updated()

        return True

    def _update_container_states_for_node(self, node_id: int) -> None:
        """Update container states when visiting a node"""
        node = self.nodes.get(node_id)
        if not node:
            return

        # Update knot state
        if hasattr(node, "knot_name") and node.knot_name != "HEADER":
            knot_key = node.knot_name
            if knot_key in self.container_states:
                state = self.container_states[knot_key]
                state.seen_count += 1
                state.last_seen_turn = self.current_turn
                state.status = ContainerStatus.SEEN

        # Update stitch state
        if (
            hasattr(node, "stitch_name")
            and node.stitch_name != "HEADER"
            and hasattr(node, "knot_name")
        ):
            stitch_key = f"{node.knot_name}.{node.stitch_name}"
            if stitch_key in self.container_states:
                state = self.container_states[stitch_key]
                state.seen_count += 1
                state.last_seen_turn = self.current_turn
                state.status = ContainerStatus.SEEN

    def _follow_story_path(self):
        """Follow the story path, processing gather nodes and base content until we find choices or reach the end."""
        visited = set()  # Prevent infinite loops

        while self.current_node_id not in visited:
            if self.current_node_id not in self.node_visited:
                self.node_visited[self.current_node_id] = 0
            self.node_visited[self.current_node_id] += 1
            self._update_container_states_for_node(self.current_node_id)
            # Get next nodes
            next_node_ids = self._get_next_nodes(self.current_node_id)

            if not next_node_ids:
                # End of story
                if self.nodes.get(self.current_node_id).node_type is NodeType.END:
                    self._add_content("END OF STORY")
                elif (
                    self.nodes.get(self.current_node_id).node_type is NodeType.AUTO_END
                ):
                    self._add_content("AUTO END OF STORY generated by the software")
                else:
                    raise NotImplementedError("THE STORY GRAPH HAS STRANGE PATHS")
                self.is_story_complete = True
                if self.on_story_complete:
                    self.on_story_complete()
                break

            # Check if any next nodes are choices
            choice_nodes = self._get_choice_nodes(next_node_ids)

            if (choice_nodes and self.let_people_choose_one_choice) or (
                len(choice_nodes) > 1 and not self.let_people_choose_one_choice
            ):
                # Found choices, stop here so user can choose
                break

            # No choices found, continue following the path
            # Move to the first next node if we can see it multiple times
            if not self.let_people_choose_one_choice:
                next_node_id = (
                    choice_nodes[0].item_id if choice_nodes else next_node_ids[0]
                )
            else:
                next_node_id = next_node_ids[0]
            next_node = self.nodes.get(next_node_id)

            if next_node:
                self.current_node_id = next_node_id
                # Add content from gather nodes and base content to history
                if next_node.node_type == NodeType.GATHER and next_node.content:
                    self._add_content(next_node.content)
                elif next_node.node_type == NodeType.BASE and next_node.content:
                    self._add_content(next_node.content)
                elif (
                    next_node.node_type == NodeType.CHOICE
                    and next_node.content
                    and not self.let_people_choose_one_choice
                ):
                    self._add_content(next_node.content)
            else:
                # Move to this node
                self.current_node_id = next_node_id

    def _get_next_nodes(self, node_id: int) -> List[int]:
        """Get the next nodes from the current node."""
        if node_id in self.graph:
            possible_nodes = list(self.graph.successors(node_id))
            return [
                node_id
                for node_id in possible_nodes
                if self.node_can_be_visited_again.get(node_id, True)
            ]
        return []

    def _get_choice_nodes(self, node_ids: List[int]) -> List[Node]:
        """Filter node IDs to return only choice nodes."""
        choice_nodes = []
        fallback_choice = []
        choice_order = 1
        for node_id in node_ids:
            if (
                node_id in self.nodes
                and self.nodes[node_id].node_type == NodeType.CHOICE
            ):
                node = self.nodes[node_id]
                if node.is_sticky or node_id not in self.node_visited:
                    if node.choice_order is None:
                        node.choice_order = choice_order
                    if node.is_fallback:
                        fallback_choice.append(node)
                    else:
                        if not self._evaluate_condition(node.condition):
                            choice_order += 1
                            continue
                        choice_nodes.append(node)
                choice_order += 1

        return choice_nodes if choice_nodes else fallback_choice

    def get_available_choices(self) -> List[Node]:
        """Get the currently available choice nodes."""
        if self.is_story_complete:
            return []

        next_node_ids = self._get_next_nodes(self.current_node_id)
        return self._get_choice_nodes(next_node_ids)

    def get_story_history(self) -> List[str]:
        """Get the complete story history."""
        return self.story_history.copy()

    def _add_content(self, content: str):
        """Add content to the story history and notify listeners."""
        self.story_history.append(content)
        if self.on_content_added:
            self.on_content_added(content)

    def _notify_choices_updated(self):
        """Notify that available choices have been updated."""
        if self.on_choices_updated:
            choices = self.get_available_choices()
            self.on_choices_updated(choices)

    def reset_story(self):
        """Reset the story to the beginning."""
        self.story_history.clear()
        self.current_node_id = self._find_start_node()
        self.is_story_complete = False

    def get_story_stats(self) -> dict:
        """Get statistics about the current story state."""
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "current_node": self.current_node_id,
            "history_length": len(self.story_history),
            "choices_available": len(self.get_available_choices()),
            "is_complete": self.is_story_complete,
        }
