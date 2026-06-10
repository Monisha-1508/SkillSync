from __future__ import annotations

from functools import lru_cache

import networkx as nx

from backend.data.skill_chains import ALL_CHAINS, ROLE_TRACKS, ROLE_DISPLAY_DESCRIPTIONS

SKILL_LABEL_TO_NODE: dict[str, str] = {
    "Python": "sde.python_core",
    "SQL": "sde.dbms_sql",
    "Data Structures & Algorithms": "sde.arrays_strings",
    "Java": "cap.java_core",
    "Aptitude": "apt.quant_arithmetic",
    "Communication": "fnd.communication_basics",
    "Excel": "da.excel_analysis",
    "Statistics": "da.descriptive_stats",
    "Object-Oriented Programming": "sde.oop",
    "JavaScript": "fs.javascript_core",
    "System Design": "sde.hld_system_design",
    "Data Visualization": "da.visualization_principles",
}

RATING_LABELS = {1: "unknown", 2: "weak", 3: "developing", 4: "known", 5: "strong"}


@lru_cache(maxsize=1)
def get_graph() -> nx.DiGraph:
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
                tags=node.tags,
            )
    for chain in ALL_CHAINS.values():
        for index, node in enumerate(chain):
            prereqs: set[str] = set()
            if node.root:
                prereqs.add(node.root)
            elif index > 0:
                prereqs.add(chain[index - 1].key)
            prereqs.update(node.extra)
            for prereq in prereqs:
                graph.add_edge(prereq, node.key)
    return graph


def node(skill_id: str) -> dict:
    graph = get_graph()
    if skill_id not in graph:
        raise KeyError(f"unknown skill id '{skill_id}'")
    attrs = graph.nodes[skill_id]
    return {"id": skill_id, **attrs}


def prerequisites(skill_id: str) -> list[str]:
    return sorted(get_graph().predecessors(skill_id))


def unlocks(skill_id: str) -> list[str]:
    return sorted(get_graph().successors(skill_id))


def all_prerequisites(skill_id: str) -> set[str]:
    return nx.ancestors(get_graph(), skill_id)


def all_dependents(skill_id: str) -> set[str]:
    return nx.descendants(get_graph(), skill_id)


def role_track_chain_names(role: str) -> list[str]:
    return ROLE_TRACKS.get(role, ROLE_TRACKS["Software Development Engineer"])


def role_subgraph(role: str) -> nx.DiGraph:
    graph = get_graph()
    chain_names = role_track_chain_names(role)
    node_ids = {n.key for name in chain_names for n in ALL_CHAINS[name]}
    return graph.subgraph(node_ids)


def role_node_ids(role: str) -> list[str]:
    sub = role_subgraph(role)
    return list(nx.topological_sort(sub))


def role_description(role: str) -> str:
    return ROLE_DISPLAY_DESCRIPTIONS.get(role, "")


def known_roles() -> list[str]:
    return list(ROLE_TRACKS.keys())


def infer_known_nodes(current_skills: dict[str, int]) -> dict[str, dict]:
    graph = get_graph()
    statuses: dict[str, dict] = {}

    def upsert(skill_id: str, status: str, source: str, rating: int | None = None) -> None:
        existing = statuses.get(skill_id)
        rank = {"inferred-weak": 0, "inferred-known": 1, "direct": 2}
        if existing is None or rank[status] > rank[existing["status"]]:
            statuses[skill_id] = {"status": status, "source": source, "rating": rating}

    for label, rating in current_skills.items():
        canonical = SKILL_LABEL_TO_NODE.get(label)
        if canonical is None or canonical not in graph:
            continue
        upsert(canonical, "direct", label, rating)

        if rating >= 4:
            for ancestor in all_prerequisites(canonical):
                upsert(ancestor, "inferred-known", f"implied by {label}", rating)
        elif rating <= 2:
            for child in unlocks(canonical):
                upsert(child, "inferred-weak", f"shaky base in {label}", rating)

    return statuses


def critical_path(role: str) -> list[str]:
    sub = role_subgraph(role)
    longest: list[str] = []
    for source in (n for n in sub if sub.in_degree(n) == 0):
        for target in (n for n in sub if sub.out_degree(n) == 0):
            for path in nx.all_simple_paths(sub, source, target):
                if len(path) > len(longest):
                    longest = path
    return longest


def topo_rank(node_ids: list[str]) -> list[str]:
    graph = get_graph()
    order = {n: i for i, n in enumerate(nx.topological_sort(graph))}
    return sorted(node_ids, key=lambda n: order.get(n, len(order)))


def priority_topo_rank(node_ids: list[str], priority_ids: set[str]) -> list[str]:
    subset = set(node_ids)
    sub = get_graph().subgraph(subset)
    indegree = {n: sub.in_degree(n) for n in sub}
    original_rank = {n: i for i, n in enumerate(node_ids)}

    ready = [n for n in node_ids if indegree[n] == 0]
    ordered: list[str] = []
    while ready:
        ready.sort(key=lambda n: (n not in priority_ids, original_rank[n]))
        chosen = ready.pop(0)
        ordered.append(chosen)
        for successor in sub.successors(chosen):
            indegree[successor] -= 1
            if indegree[successor] == 0:
                ready.append(successor)
    return ordered
