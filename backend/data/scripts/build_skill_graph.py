"""
Expands backend/data/skill_chains.py into a validated NetworkX DAG and writes
a snapshot to backend/data/skill_graph.json.

Run it once after editing skill_chains.py:
    python -m backend.data.scripts.build_skill_graph

Why export a JSON snapshot at all, if the graph is cheap to rebuild at import
time? Two reasons that matter for a hackathon demo specifically: (1) it is the
artifact you can open and eyeball - or hand to a judge - without spinning up
the app, and (2) the frontend's dependency-graph view and the `/roadmap/dag`
endpoint serve straight from it, so a graph edit doesn't require touching API
code. The runtime graph (backend/utils/skill_graph.py) is built from the same
source chains, so the two never drift apart.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from backend.data.skill_chains import ALL_CHAINS, ROLE_TRACKS  # noqa: E402


def build_graph() -> nx.DiGraph:
    graph = nx.DiGraph()

    for chain in ALL_CHAINS.values():
        for node in chain:
            graph.add_node(
                node.key,
                name=node.name,
                bloom_level=node.bloom,
                estimated_hours=node.hours,
                difficulty=node.difficulty,
                family=node.family,
                tags=list(node.tags),
            )

    # Wire edges in a second pass so a chain may reference a node defined in
    # another chain (e.g. the Capgemini Tech track roots in "fnd.prog_logic").
    for chain in ALL_CHAINS.values():
        for index, node in enumerate(chain):
            prereqs: set[str] = set()
            if node.root:
                prereqs.add(node.root)
            elif index > 0:
                prereqs.add(chain[index - 1].key)
            prereqs.update(node.extra)
            for prereq in prereqs:
                if prereq not in graph:
                    raise ValueError(f"{node.key} references unknown prerequisite '{prereq}'")
                graph.add_edge(prereq, node.key)

    if not nx.is_directed_acyclic_graph(graph):
        cycle = nx.find_cycle(graph)
        raise ValueError(f"Skill graph has a cycle, fix skill_chains.py: {cycle}")

    return graph


def export_snapshot(graph: nx.DiGraph, out_path: Path) -> dict:
    nodes = []
    for key, attrs in graph.nodes(data=True):
        nodes.append({
            "id": key,
            "name": attrs["name"],
            "bloom_level": attrs["bloom_level"],
            "estimated_hours": attrs["estimated_hours"],
            "difficulty": attrs["difficulty"],
            "family": attrs["family"],
            "tags": attrs["tags"],
            "prerequisites": sorted(graph.predecessors(key)),
            "unlocks": sorted(graph.successors(key)),
        })
    edges = [{"from": u, "to": v} for u, v in graph.edges()]

    snapshot = {
        "generated_from": "backend/data/skill_chains.py",
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "is_dag": nx.is_directed_acyclic_graph(graph),
        "role_tracks": ROLE_TRACKS,
        "nodes": nodes,
        "edges": edges,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return snapshot


def main() -> None:
    graph = build_graph()
    out_path = Path(__file__).resolve().parents[1] / "skill_graph.json"
    snapshot = export_snapshot(graph, out_path)
    print(f"Skill graph built: {snapshot['node_count']} nodes, {snapshot['edge_count']} edges")
    print(f"DAG valid: {snapshot['is_dag']}")
    print(f"Snapshot written to {out_path}")

    for role, tracks in ROLE_TRACKS.items():
        subgraph_nodes = {
            node.key
            for chain_name in tracks
            for node in ALL_CHAINS[chain_name]
        }
        sub = graph.subgraph(subgraph_nodes)
        total_hours = sum(attrs["estimated_hours"] for _, attrs in sub.nodes(data=True))
        print(f"  {role}: {sub.number_of_nodes()} nodes, ~{total_hours}h total")


if __name__ == "__main__":
    main()
