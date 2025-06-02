from typing import ClassVar, Optional

from pydantic import BaseModel, Field, PrivateAttr, computed_field

from analink.parser.condition import Condition


class Container(BaseModel):
    # Instance fields
    _id: int = PrivateAttr(default_factory=lambda: Container._get_next_id())
    content: Optional[str] = None
    children: list[tuple[Condition, "Container"]] = Field(
        default_factory=list
    )  # Added container_id for condition evaluation
    is_choice: bool = False
    choice_text: Optional[str] = None
    sticky: bool = False

    _next_id: ClassVar[int] = 1

    @computed_field  # type: ignore[prop-decorator]
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

    def _is_descendant_of(self, ancestor: "Container") -> bool:
        """
        Check if this container is a descendant of the given ancestor container.
        Uses iterative approach to avoid recursion depth issues.
        """
        # Use a stack to traverse the ancestor's tree
        stack = [ancestor]
        visited = set()

        while stack:
            current = stack.pop()

            # Avoid infinite loops in case of existing circular references
            if id(current) in visited:
                continue
            visited.add(id(current))

            # Check if we found ourselves in the ancestor's tree
            if current is self:
                return True

            # Add all children to the stack for further exploration
            for _, child_container in current.children:
                stack.append(child_container)

        return False

    def append_to_leaves(self, item: tuple[Condition, "Container"]) -> None:
        """
        Append an item to all leaf containers (containers with no children).
        If this container has no children, append to this container.
        Otherwise, recursively append to all leaf containers in the tree.
        Avoids circular references by not adding a container to itself or its descendants.
        """
        condition, container_to_add = item

        # Avoid circular reference - don't add a container to itself or its descendants
        if self is container_to_add or self._is_descendant_of(container_to_add):
            return

        if not self.children:
            # This is a leaf container, append here
            self.children.append(item)
        else:
            # This container has children, recursively append to their leaves
            for _, child_container in self.children:
                child_container.append_to_leaves(item)

    def print_tree(self, depth=0, is_last=True, prefix="", final_return=[]):
        # Create the tree connector
        if depth == 0:
            connector = ""
            next_prefix = ""
        else:
            connector = "└── " if is_last else "├── "
            next_prefix = prefix + ("    " if is_last else "│   ")

        final_return.append(f"{prefix}{connector}=== CONTAINER ID : {self.item_id} ===")
        final_return.append(
            f"{prefix}{'    ' if depth == 0 else ('    ' if is_last else '│   ')}{self.content}"
        )

        # Print children
        children = list(self.children)
        for i, (condition, child_container) in enumerate(children):
            is_last_child = i == len(children) - 1
            child_container.print_tree(
                depth + 1, is_last_child, next_prefix, final_return=final_return
            )
        return "\n".join(final_return)

    def container_to_mermaid(self):
        """Convert container tree to Mermaid flowchart"""
        lines = ["```mermaid", "flowchart TD"]

        visited_nodes = set()
        added_edges = set()

        def traverse(container):
            # Skip if we've already processed this node
            if container.item_id in visited_nodes:
                return

            visited_nodes.add(container.item_id)

            # Add this node
            content = container.content.replace('"', "'").replace("\n", " ")
            if len(content) > 50:
                content = content[:47] + "..."
            lines.append(f'    {container.item_id}["{content}"]')

            # Add edges to children (only if not already added)
            for condition, child in container.children:
                edge = (container.item_id, child.item_id)
                if edge not in added_edges:
                    lines.append(f"    {container.item_id} --> {child.item_id}")
                    added_edges.add(edge)

                # Continue traversing even if edge was already added
                traverse(child)

        traverse(self)
        lines.append("```")
        return "\n".join(lines)
