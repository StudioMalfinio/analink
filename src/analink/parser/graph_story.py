from typing import Optional

import networkx as nx

from analink.parser.node import Node, NodeType


def find_leaves_from_node(
    start_node_id: int, edges: list[tuple[int, int]]
) -> list[int]:
    """Find all leaf nodes (nodes with no outgoing edges) reachable from start_node_id"""
    # Create directed graph from edges
    G = nx.DiGraph(edges)

    # Get all descendants of start_node_id
    if start_node_id not in G:
        return [start_node_id]  # If node has no edges, it's a leaf itself

    descendants = nx.descendants(G, start_node_id)
    descendants.add(start_node_id)  # Include the start node itself

    # Find leaves: nodes with out_degree 0
    leaves = [node for node in descendants if G.out_degree(node) == 0]

    return leaves


def parse_story(
    nodes: dict[int, Node],
    verbose=False,
) -> list[tuple[int, int]]:
    """
    return the edges
    """
    edges = []
    node_at_level: dict[int, list[int]] = {}
    max_level_seen = 0

    for item_id, node in nodes.items():
        max_level_seen = max(node.level, max_level_seen)
        if node.level not in node_at_level:
            node_at_level[node.level] = []

        if node.node_type is NodeType.BASE:
            # strange since it should have been merged
            node_at_level[node.level].append(item_id)
            if (
                node.level > 0
                and node.level - 1 in node_at_level
                and len(node_at_level[node.level - 1]) > 0
            ):
                edges.append((node_at_level[node.level - 1][-1], item_id))

        elif node.node_type is NodeType.CHOICE:
            node_at_level[node.level].append(item_id)
            if (
                node.level > 0
                and node.level - 1 in node_at_level
                and len(node_at_level[node.level - 1]) > 0
            ):
                edges.append((node_at_level[node.level - 1][-1], item_id))

        elif node.node_type is NodeType.GATHER:
            # for every leaves of node in node_at_level[node.level] -> add the edge node.item_id->item_id
            if node.level in node_at_level:

                for level_node_item_id in node_at_level[node.level]:
                    # Find all leaves (descendants with no outgoing edges) from this node
                    leaves = find_leaves_from_node(level_node_item_id, edges)
                    for leaf_id in leaves:
                        edges.append((leaf_id, item_id))

            node_at_level[node.level] = []
            if node.level - 1 not in node_at_level:
                node_at_level[node.level - 1] = [item_id]
            else:
                node_at_level[node.level - 1][-1] = item_id

    return edges


def escape_mermaid_text(text: Optional[str]) -> str:
    """Escape text for use in Mermaid diagrams"""
    if not text:
        return ""

    # Replace quotes with escaped versions or alternatives
    text = text.replace('"', "&quot;")  # HTML entity for double quotes
    text = text.replace("'", "&#39;")  # HTML entity for single quotes
    text = text.replace("\n", " ")  # Replace newlines with spaces
    text = text.replace("|", "&#124;")  # Escape pipe characters (special in Mermaid)

    return text


def graph_to_mermaid(nodes: dict[int, Node], edges: list[tuple[int, int]]) -> str:
    """Convert nodes and edges to Mermaid flowchart"""
    lines = ["```mermaid", "flowchart TD"]

    added_edges = set()

    # Add all nodes
    for node_id, node in nodes.items():
        content = (
            node.content.replace('"', "'").replace("\n", " ") if node.content else ""
        )
        if len(content) > 50:
            content = content[:47] + "..."
        if node.node_type is NodeType.CHOICE:
            lines.append(f'    {node_id}{{"{content}"}}')
        else:
            lines.append(f'    {node_id}["{content}"]')

    # Add all edges (avoid duplicates)
    for source, target in edges:
        edge = (source, target)
        if edge not in added_edges:
            if nodes[target].node_type is NodeType.CHOICE:
                choice_text = escape_mermaid_text(nodes[target].choice_text)
                lines.append(f"    {source} -->|{choice_text}| {target}")
            else:
                lines.append(f"    {source} --> {target}")
            added_edges.add(edge)

    lines.append("```")
    return "\n".join(lines)
