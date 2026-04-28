import heapq
import math
from typing import Any, Dict, Hashable, Iterable, List, Optional, Tuple

import networkx as nx


def build_sample_graph() -> nx.DiGraph:
    """Build a small sample road graph with length and risk per edge."""
    graph = nx.DiGraph()

    sample_nodes = ["A", "B", "C", "D", "E", "F"]
    graph.add_nodes_from(sample_nodes)

    sample_edges = [
        ("A", "B", {"length": 4.0, "risk_score": 0.2}),
        ("A", "C", {"length": 2.0, "risk_score": 0.6}),
        ("B", "C", {"length": 1.0, "risk_score": 0.3}),
        ("B", "D", {"length": 5.0, "risk_score": 0.8}),
        ("C", "D", {"length": 8.0, "risk_score": 0.4}),
        ("C", "E", {"length": 10.0, "risk_score": 0.2}),
        ("D", "E", {"length": 2.0, "risk_score": 0.5}),
        ("D", "F", {"length": 6.0, "risk_score": 0.9}),
        ("E", "F", {"length": 2.0, "risk_score": 0.2}),
    ]

    graph.add_edges_from(sample_edges)
    return graph


def add_combined_cost(G: nx.DiGraph, alpha: float = 0.7, beta: float = 0.3) -> nx.DiGraph:
    for _, _, data in G.edges(data=True):
        length = float(data.get("length", 1.0))
        risk = float(data.get("risk_score", 0.0))
        data["combined_cost"] = alpha * length + beta * length * risk
    return G


def district_to_node(district_name, node_to_district, G):
    # Pick the first node in the district for routing simplicity
    return next((node for node, district in node_to_district.items() if district == district_name), None)


def _effective_edge_cost(edge_data: Dict[str, float], risk_factor: float = 1.0) -> float:
    """Higher risk increases travel cost and discourages unsafe roads."""
    length = float(edge_data.get("length", 1.0))
    risk = float(edge_data.get("risk_score", 0.0))
    return max(length * (1.0 + risk_factor * risk), 0.0)


def _iter_neighbors(graph: nx.DiGraph, node: Hashable) -> Iterable[Tuple[Hashable, Dict[str, float]]]:
    yield from graph[node].items()


def dijkstra(
    graph: nx.DiGraph,
    start: Hashable,
    end: Hashable,
    risk_factor: float = 1.0,
    blocked_edges: Optional[Iterable[Tuple[Hashable, Hashable]]] = None,
) -> Tuple[float, List[Hashable]]:
    """Return shortest risk-adjusted path and distance using a binary heap."""
    if start not in graph or end not in graph:
        return math.inf, []

    # Map blocked edges for O(1) lookup
    blocked = set()
    if blocked_edges:
        for u, v in blocked_edges:
            blocked.add((u, v))
            blocked.add((v, u)) # Assume symmetry for simulation

    distances: Dict[Hashable, float] = {start: 0.0}
    previous: Dict[Hashable, Optional[Hashable]] = {start: None}
    min_heap: List[Tuple[float, Hashable]] = [(0.0, start)]

    while min_heap:
        current_distance, current_node = heapq.heappop(min_heap)

        if current_distance > distances.get(current_node, math.inf):
            continue

        if current_node == end:
            break

        for neighbor, edge_data in _iter_neighbors(graph, current_node):
            if (current_node, neighbor) in blocked:
                continue

            edge_cost = _effective_edge_cost(edge_data, risk_factor=risk_factor)
            candidate_distance = current_distance + edge_cost

            if candidate_distance < distances.get(neighbor, math.inf):
                distances[neighbor] = candidate_distance
                previous[neighbor] = current_node
                heapq.heappush(min_heap, (candidate_distance, neighbor))

    if end not in distances:
        return math.inf, []

    path: List[Hashable] = []
    cursor: Optional[Hashable] = end
    while cursor is not None:
        path.append(cursor)
        cursor = previous.get(cursor)
    path.reverse()

    return distances[end], path


def shortest_safest_route(G, source_node, target_node):
    distance, path = dijkstra(G, source_node, target_node, risk_factor=1.0)
    return (distance, path) if path else (None, [])


def build_demo_city_graph() -> Tuple[nx.DiGraph, Dict[int, Tuple[float, float]]]:
    """Create a small connected road graph with simulated coordinates, length, and risk."""
    node_coords: Dict[int, Tuple[float, float]] = {
        1: (28.6100, 77.2000),
        2: (28.6145, 77.2065),
        3: (28.6180, 77.2140),
        4: (28.6210, 77.2210),
        5: (28.6150, 77.2280),
        6: (28.6070, 77.2220),
        7: (28.6035, 77.2125),
        8: (28.6075, 77.2045),
    }

    # length is in km, risk_score is normalized 0-1 for demo.
    edge_specs = [
        (1, 2, 1.2, 0.20),
        (2, 3, 1.0, 0.95),
        (3, 4, 1.1, 0.70),
        (4, 5, 1.0, 0.25),
        (5, 6, 1.4, 0.30),
        (6, 7, 1.0, 0.15),
        (7, 8, 1.2, 0.40),
        (8, 1, 1.1, 0.20),
        (2, 8, 0.9, 0.55),
        (3, 5, 1.3, 0.60),
        (2, 6, 1.6, 0.22),
        (1, 7, 1.5, 0.18),
        (2, 4, 0.9, 0.10),
        (4, 3, 0.9, 0.10),
    ]

    graph = nx.DiGraph()
    for node_id in node_coords:
        graph.add_node(node_id)

    for u, v, length_km, risk in edge_specs:
        graph.add_edge(u, v, length=length_km, risk_score=risk)
        graph.add_edge(v, u, length=length_km, risk_score=risk)

    return graph, node_coords


def _nearest_node(node_coords: Dict[int, Tuple[float, float]], latitude: float, longitude: float) -> int:
    return min(
        node_coords,
        key=lambda node_id: (node_coords[node_id][0] - latitude) ** 2
        + (node_coords[node_id][1] - longitude) ** 2,
    )


def _sorted_nodes_by_distance(
    node_coords: Dict[int, Tuple[float, float]], latitude: float, longitude: float
) -> List[int]:
    return sorted(
        node_coords,
        key=lambda node_id: (node_coords[node_id][0] - latitude) ** 2
        + (node_coords[node_id][1] - longitude) ** 2,
    )


def _route_distance_and_risks(graph: nx.DiGraph, path: List[int]) -> Tuple[float, List[float]]:
    total_distance_km = 0.0
    edge_risks: List[float] = []
    for u, v in zip(path[:-1], path[1:]):
        edge_data = graph.get_edge_data(u, v) or {}
        total_distance_km += float(edge_data.get("length", 0.0))
        edge_risks.append(float(edge_data.get("risk_score", 0.0)))
    return round(total_distance_km, 3), edge_risks


def _estimate_eta_minutes(distance_km: float, speed_kmh: float) -> int:
    if distance_km <= 0:
        return 0
    return max(int(round((distance_km / max(speed_kmh, 1.0)) * 60.0)), 1)


def generate_demo_route_options(
    source_lat: float,
    source_lon: float,
    hospital_lat: float,
    hospital_lon: float,
    emergency_type: str,
) -> Dict[str, Any]:
    """Generate fastest and safest routes on a simulated city graph using Dijkstra."""
    graph, node_coords = build_demo_city_graph()

    source_node = _nearest_node(node_coords, source_lat, source_lon)
    target_candidates = _sorted_nodes_by_distance(node_coords, hospital_lat, hospital_lon)
    target_node = target_candidates[0]
    if target_node == source_node and len(target_candidates) > 1:
        target_node = target_candidates[1]

    fastest_cost, fastest_path = dijkstra(graph, source_node, target_node, risk_factor=0.0)
    safest_cost, safest_path = dijkstra(graph, source_node, target_node, risk_factor=2.2)

    if not fastest_path and safest_path:
        fastest_path = safest_path
        fastest_cost = safest_cost
    if not safest_path and fastest_path:
        safest_path = fastest_path
        safest_cost = fastest_cost

    def summarize(path: List[int], route_name: str, speed_kmh: float, total_cost: float) -> Dict[str, Any]:
        distance_km, edge_risks = _route_distance_and_risks(graph, path)
        avg_risk = round((sum(edge_risks) / len(edge_risks)) * 100.0, 2) if edge_risks else 0.0
        if avg_risk >= 75.0:
            band = "high"
        elif avg_risk >= 40.0:
            band = "moderate"
        else:
            band = "low"

        return {
            "route_name": route_name,
            "path_nodes": path,
            "route_coordinates": [[node_coords[node][0], node_coords[node][1]] for node in path],
            "edge_risks": edge_risks,
            "segment_with_max_risk": edge_risks.index(max(edge_risks)) + 1 if edge_risks else None,
            "total_distance_km": distance_km,
            "risk_score": avg_risk,
            "risk_band": band,
            "estimated_time_min": _estimate_eta_minutes(distance_km, speed_kmh),
            "emergency_type": emergency_type,
            "total_cost": round(float(total_cost), 3),
            "source_node": source_node,
            "target_node": target_node,
            "is_simulated": True,
        }

    return {
        "fastest_route": summarize(fastest_path, "fastest", 40.0, fastest_cost),
        "safest_route": summarize(safest_path, "safest", 30.0, safest_cost),
        "source_node": source_node,
        "target_node": target_node,
        "is_simulated": True,
    }
