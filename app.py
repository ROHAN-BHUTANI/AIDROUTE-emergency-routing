"""Flask backend for the AI Emergency Response Optimizer.

This service provides:
- Nearest hospital detection from CSV data
- Dijkstra-based route optimization with risk awareness
- Route-level risk prediction and emergency evaluation
- Traffic estimation and decision engine
- Real-time alert generation

All responses follow a standardized schema: {"status": "success"|"error", "data": {...}, "message": ...}
"""

from __future__ import annotations

import json
import math
import os
import random
import time
from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.error import URLError
from urllib.request import Request, urlopen

import networkx as nx
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

from ai_engine import analyze_disaster, explain_route, recommend_action
from models.risk_model import (
    compute_edge_risk_score,
    compute_route_risk_score,
    compare_routes,
    evaluate_emergency_risk,
    estimate_traffic_score,
    risk_band,
)
from routing import build_demo_city_graph, dijkstra, generate_demo_route_options


# ============================================================================
# Constants & Configuration
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

ROADS_PATH = DATA_DIR / "roads.csv"
LOCATIONS_PATH = DATA_DIR / "locations.csv"
HOSPITALS_PATH = DATA_DIR / "hospitals.csv"
POIS_PATH = DATA_DIR / "pois.csv"

OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

ALLOWED_EMERGENCIES = {"medical", "accident", "fire", "flood", "earthquake", "landslide"}


# ============================================================================
# Utility Functions
# ============================================================================


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute distance between coordinates using the haversine formula."""
    radius = 6371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2.0) ** 2
    )
    return radius * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float with default fallback."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_risk_level(level: str) -> str:
    """Normalize risk level string to standard format."""
    normalized = str(level or "").strip().lower()
    if normalized in {"high", "medium", "low"}:
        return normalized
    if normalized == "moderate":
        return "medium"
    return "low"


def _to_title_case_risk(band: str) -> str:
    """Convert risk band to title case for display."""
    normalized = str(band or "").strip().lower()
    mapping = {"high": "High", "moderate": "Medium", "medium": "Medium", "low": "Low"}
    return mapping.get(normalized, "Low")


def _risk_level_from_score(score: Any) -> str:
    """Convert a 0-10 route risk score into a low/medium/high severity label."""
    value = _safe_float(score, 0.0)
    if value >= 7.0:
        return "high"
    if value >= 4.0:
        return "medium"
    return "low"


# ============================================================================
# API Response Utilities
# ============================================================================


def success_response(data: Dict[str, Any], status_code: int = 200):
    """Return standardized success response."""
    return jsonify({"status": "success", "data": data}), status_code


def error_response(message: str, status_code: int = 400):
    """Return standardized error response."""
    return jsonify({"status": "error", "message": message}), status_code


# ============================================================================
# External API Functions
# ============================================================================


def fetch_osrm_route(
    source_latitude: float,
    source_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
) -> Dict[str, Any]:
    """Fetch a real driving route from OSRM and normalize the response."""
    url = OSRM_ROUTE_URL.format(
        lon1=source_longitude,
        lat1=source_latitude,
        lon2=destination_longitude,
        lat2=destination_latitude,
    )
    request_obj = Request(url, headers={"User-Agent": "AIDROUTE/1.0"})

    try:
        with urlopen(request_obj, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        raise ValueError(f"Unable to reach the OSRM routing service: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("OSRM returned an invalid JSON response.") from exc

    if payload.get("code") != "Ok":
        message = payload.get("message") or "OSRM did not return a usable route."
        raise ValueError(str(message))

    routes = payload.get("routes") or []
    if not routes:
        raise ValueError("OSRM did not return any routes.")

    route = routes[0]
    geometry = route.get("geometry") or {}
    coordinates = geometry.get("coordinates") or []
    route_coordinates = [
        [float(latitude), float(longitude)]
        for longitude, latitude in coordinates
        if longitude is not None and latitude is not None
    ]

    distance_meters = float(route.get("distance", 0.0))
    duration_seconds = float(route.get("duration", 0.0))

    return {
        "route_coordinates": route_coordinates,
        "distance_km": round(distance_meters / 1000.0, 3),
        "duration_min": round(duration_seconds / 60.0, 1),
        "distance_m": round(distance_meters, 1),
        "duration_sec": round(duration_seconds, 1),
    }


def fetch_overpass_hospitals(
    latitude: float,
    longitude: float,
    radius_km: float = 5.0,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """Fetch nearby hospitals from OpenStreetMap via Overpass API."""
    radius_meters = int(max(radius_km, 0.1) * 1000)
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="hospital"](around:{radius_meters},{latitude},{longitude});
      way["amenity"="hospital"](around:{radius_meters},{latitude},{longitude});
      relation["amenity"="hospital"](around:{radius_meters},{latitude},{longitude});
    );
    out center tags;
    """.strip()

    request_obj = Request(
        OVERPASS_API_URL,
        data=query.encode("utf-8"),
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "AIDROUTE/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request_obj, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        raise ValueError(f"Unable to reach the Overpass service: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("Overpass returned an invalid JSON response.") from exc

    elements = payload.get("elements") or []
    hospitals: List[Dict[str, Any]] = []

    for element in elements:
        tags = element.get("tags") or {}
        hospital_latitude = element.get("lat")
        hospital_longitude = element.get("lon")

        if hospital_latitude is None or hospital_longitude is None:
            center = element.get("center") or {}
            hospital_latitude = center.get("lat")
            hospital_longitude = center.get("lon")

        if hospital_latitude is None or hospital_longitude is None:
            continue

        name = str(tags.get("name") or tags.get("operator") or "Hospital").strip()
        distance_km = haversine_km(latitude, longitude, float(hospital_latitude), float(hospital_longitude))

        if distance_km > radius_km:
            continue

        hospitals.append(
            {
                "name": name,
                "latitude": round(float(hospital_latitude), 6),
                "longitude": round(float(hospital_longitude), 6),
                "distance_km": round(distance_km, 3),
            }
        )

    hospitals.sort(key=lambda item: item["distance_km"])
    return hospitals[: max(limit, 1)]


def _openrouter_completion(prompt: str) -> Optional[str]:
    """Fetch AI completion from OpenRouter API."""
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return None

    body = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "You generate concise disaster-routing intelligence text."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.35,
        "max_tokens": 90,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("OPENROUTER_APP_URL", "http://localhost:3000"),
        "X-Title": "AIDRoute",
    }

    request_obj = Request(
        OPENROUTER_API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urlopen(request_obj, timeout=18) as response:
            payload = json.loads(response.read().decode("utf-8"))
        choices = payload.get("choices") or []
        if not choices:
            return None
        content = ((choices[0].get("message") or {}).get("content") or "").strip()
        return content or None
    except Exception:
        return None


# ============================================================================
# Risk & Explanation Functions
# ============================================================================


def _risk_explanation(
    risk_score: float,
    risk_level: str,
    emergency_type: str,
    scenario_title: str,
) -> str:
    """Generate risk explanation text."""
    prompt = (
        "Write one concise sentence (max 20 words) explaining this emergency route risk. "
        f"Risk score: {risk_score:.2f}/10. Risk level: {risk_level}. "
        f"Emergency: {emergency_type}. Scenario: {scenario_title}."
    )
    ai_text = _openrouter_completion(prompt)
    if ai_text:
        return ai_text

    if risk_level == "high":
        return "High risk due to severe incident intensity, dense traffic, and constrained emergency access."
    if risk_level == "medium":
        return "Moderate risk from mixed traffic pressure and localized disruption near emergency zone."
    return "Low risk with stable mobility and clear emergency corridor access."


def _simulate_emergency_scenario(emergency_type: str, latitude: float, longitude: float) -> Dict[str, Any]:
    """Simulate emergency scenario details for risk evaluation."""
    minute_bucket = int(time.time() // 60)
    seed = f"{emergency_type}|{round(latitude, 3)}|{round(longitude, 3)}|{minute_bucket}"
    rng = random.Random(seed)

    traffic_state = rng.choice(["light", "moderate", "heavy"])
    weather_state = rng.choice(["clear", "rainfall", "storm cells", "low visibility"])
    impact_state = rng.choice(["localized", "district-wide", "corridor-wide"])

    templates = {
        "fire": ["Industrial fire near mixed-use block", "Warehouse blaze with smoke spread"],
        "flood": ["Urban flooding around arterial roads", "Flash flood crossing major corridor"],
        "earthquake": ["Post-seismic response with debris", "Aftershock-triggered structural hazards"],
        "landslide": ["Hillside landslide blocking route", "Slope failure near emergency corridor"],
        "accident": ["Multi-vehicle collision at junction", "High-impact crash with lane blockage"],
        "medical": ["Mass-casualty medical dispatch", "Critical patient transfer under pressure"],
    }
    title = rng.choice(templates.get(emergency_type, templates["medical"]))
    summary = f"{title} with {traffic_state} traffic, {weather_state}, and {impact_state} operational impact."

    return {
        "title": title,
        "summary": summary,
        "traffic_state": traffic_state,
        "weather_state": weather_state,
        "impact_scope": impact_state,
        "updated_at": int(time.time()),
    }


def _build_dynamic_alerts(risk_score: float, scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build dynamic alert list based on risk score and scenario."""
    severity = "critical" if risk_score >= 7 else "warning" if risk_score >= 4 else "info"
    return [
        {
            "type": "flood_warning",
            "title": "Flood Warning",
            "severity": "critical" if scenario.get("weather_state") in {"rainfall", "storm cells"} else "info",
            "message": "Waterlogging risk rising on low-lying routes."
            if scenario.get("weather_state") in {"rainfall", "storm cells"}
            else "No active flood stress indicators.",
        },
        {
            "type": "traffic_congestion",
            "title": "Traffic Congestion",
            "severity": "warning" if scenario.get("traffic_state") in {"moderate", "heavy"} else "info",
            "message": "Congestion clusters detected near response corridor."
            if scenario.get("traffic_state") in {"moderate", "heavy"}
            else "Traffic flow currently stable.",
        },
        {
            "type": "fire_risk",
            "title": "Fire Risk",
            "severity": severity,
            "message": "Elevated fire propagation risk due to ongoing hazardous conditions."
            if risk_score >= 7
            else "Fire risk monitored; maintain standby suppression support.",
        },
    ]


# ============================================================================
# Input Parsing & Validation
# ============================================================================


def parse_payload(payload: Optional[Dict[str, Any]]) -> Tuple[float, float, str]:
    """Parse and validate request payload for route endpoints.
    
    Returns: (latitude, longitude, emergency_type)
    """
    if payload is None:
        raise ValueError("Request body must be valid JSON.")

    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    emergency_type = payload.get("emergency_type") or payload.get("emergency type") or payload.get("emergencyType")
    emergency_type = str(emergency_type or "medical").strip().lower()

    if latitude is None or longitude is None:
        raise ValueError("Both latitude and longitude are required.")

    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError) as exc:
        raise ValueError("Latitude and longitude must be numeric values.") from exc

    if not (-90.0 <= lat <= 90.0):
        raise ValueError("Latitude must be between -90 and 90.")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError("Longitude must be between -180 and 180.")

    if emergency_type not in ALLOWED_EMERGENCIES:
        raise ValueError(
            f"Unsupported emergency_type. Allowed values: {', '.join(sorted(ALLOWED_EMERGENCIES))}."
        )

    return lat, lon, emergency_type


def parse_traffic_payload(payload: Optional[Dict[str, Any]]) -> Tuple[str, str, Optional[float]]:
    """Parse and validate traffic estimation request payload."""
    if payload is None:
        raise ValueError("Request body must be valid JSON.")

    time_of_day = str(payload.get("time_of_day") or payload.get("timeOfDay", "")).strip()
    location_type = str(payload.get("location_type") or payload.get("locationType", "")).strip().lower()
    random_variability = payload.get("random_variability") or payload.get("randomVariability")

    if not time_of_day:
        raise ValueError("time_of_day is required.")
    if not location_type:
        raise ValueError("location_type is required.")

    if random_variability is None or random_variability == "":
        variability_value = None
    else:
        try:
            variability_value = float(random_variability)
        except (TypeError, ValueError) as exc:
            raise ValueError("random_variability must be numeric.") from exc

    if variability_value is not None and not (0.0 <= variability_value <= 1.0):
        raise ValueError("random_variability must be between 0 and 1.")

    return time_of_day, location_type, variability_value


# ============================================================================
# Emergency Routing Service
# ============================================================================
# Emergency Routing Service
# ============================================================================


class EmergencyRoutingService:
    """Core service that loads data once and serves routing queries."""

    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self.node_coords: Dict[int, Tuple[float, float]] = {}
        self.hospitals: List[Dict[str, Any]] = []
        self.blocked_edges: Set[Tuple[int, int]] = set()
        self.using_demo_data = False
        self._load_data()

    def _load_data(self) -> None:
        """Load graph, node coordinates, and hospital data."""
        self.node_coords = self._load_locations()
        self.graph = self._load_graph()
        self.hospitals = self._load_hospitals()

    def _load_locations(self) -> Dict[int, Tuple[float, float]]:
        """Load node coordinates from locations.csv."""
        if not LOCATIONS_PATH.exists():
            self.using_demo_data = True
            return {}

        try:
            locations_df = pd.read_csv(LOCATIONS_PATH, usecols=["osmid", "y", "x"])
            return {
                int(row.osmid): (float(row.y), float(row.x))
                for row in locations_df.itertuples(index=False)
            }
        except Exception:
            self.using_demo_data = True
            return {}

    def _load_graph(self) -> nx.DiGraph:
        """Load road network from roads.csv or use demo graph."""
        if not ROADS_PATH.exists():
            self.using_demo_data = True
            demo_graph, demo_node_coords = build_demo_city_graph()
            self.node_coords = demo_node_coords
            return demo_graph

        try:
            roads_df = pd.read_csv(ROADS_PATH)

            u_col = "u" if "u" in roads_df.columns else roads_df.columns[0]
            v_col = "v" if "v" in roads_df.columns else roads_df.columns[1]
            length_col = "length" if "length" in roads_df.columns else roads_df.columns[2]

            graph = nx.DiGraph()
            for row in roads_df[[u_col, v_col, length_col]].itertuples(index=False):
                u, v, length = int(row[0]), int(row[1]), float(row[2])
                graph.add_edge(u, v, length=length, risk_score=0.0)
            return graph
        except Exception:
            self.using_demo_data = True
            demo_graph, demo_node_coords = build_demo_city_graph()
            self.node_coords = demo_node_coords
            return demo_graph

    def _load_hospitals(self) -> List[Dict[str, Any]]:
        """Load hospital data from CSV files."""
        # Primary source: explicit hospital dataset
        if HOSPITALS_PATH.exists():
            try:
                hospitals_df = pd.read_csv(HOSPITALS_PATH)
                hospitals = []
                for idx, row in enumerate(hospitals_df.itertuples(index=False), start=1):
                    name = str(getattr(row, "name", f"Hospital {idx}")).strip()
                    try:
                        lat = float(getattr(row, "latitude", 0.0))
                        lon = float(getattr(row, "longitude", 0.0))
                        hospitals.append(
                            {"id": idx, "name": name, "latitude": lat, "longitude": lon}
                        )
                    except (TypeError, ValueError):
                        continue
                if hospitals:
                    return hospitals
            except Exception:
                pass

        # Fallback source: POI dataset
        if not POIS_PATH.exists():
            return []

        try:
            pois_df = pd.read_csv(POIS_PATH)
            if "amenity" not in pois_df.columns or "geometry" not in pois_df.columns:
                return []

            hospitals: List[Dict[str, Any]] = []
            hospitals_df = pois_df[pois_df["amenity"].astype(str).str.lower() == "hospital"].copy()
            for idx, row in enumerate(hospitals_df.itertuples(index=False), start=1):
                geometry = str(getattr(row, "geometry", "")).strip()
                if not geometry.startswith("POINT (") or not geometry.endswith(")"):
                    continue
                try:
                    lon_lat = geometry[7:-1].split()
                    if len(lon_lat) != 2:
                        continue
                    lon, lat = float(lon_lat[0]), float(lon_lat[1])
                    hospitals.append(
                        {"id": idx, "name": "Hospital", "latitude": lat, "longitude": lon}
                    )
                except (ValueError, IndexError):
                    continue
            return hospitals
        except Exception:
            return []

    def nearest_node(self, latitude: float, longitude: float) -> Optional[int]:
        """Return nearest graph node to the input coordinate."""
        if not self.node_coords:
            return None

        return min(
            self.node_coords,
            key=lambda node_id: (self.node_coords[node_id][0] - latitude) ** 2
            + (self.node_coords[node_id][1] - longitude) ** 2,
        )

    def nearest_hospital(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """Return nearest hospital with distance calculated."""
        # Try real-time Overpass API first
        with suppress(ValueError):
            if hospitals := fetch_overpass_hospitals(latitude, longitude, radius_km=5.0, limit=1):
                return {"id": 1, **hospitals[0]}

        # Fall back to loaded hospitals
        if not self.hospitals:
            return None

        best_hospital = min(
            self.hospitals,
            key=lambda h: haversine_km(latitude, longitude, h["latitude"], h["longitude"]),
        )

        distance_km = haversine_km(
            latitude,
            longitude,
            best_hospital["latitude"],
            best_hospital["longitude"],
        )
        return {**best_hospital, "distance_km": round(distance_km, 3)}

    def nearby_hospitals(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """Return nearby hospitals within radius."""
        # Try real-time Overpass API first
        with suppress(ValueError):
            if hospitals := fetch_overpass_hospitals(latitude, longitude, radius_km=radius_km, limit=limit):
                return hospitals

        # Fall back to loaded hospitals
        if not self.hospitals:
            return []

        fallback = [
            {
                "name": hospital["name"],
                "latitude": hospital["latitude"],
                "longitude": hospital["longitude"],
                "distance_km": round(
                    haversine_km(latitude, longitude, hospital["latitude"], hospital["longitude"]),
                    3,
                ),
            }
            for hospital in self.hospitals
            if haversine_km(latitude, longitude, hospital["latitude"], hospital["longitude"]) <= radius_km
        ]
        fallback.sort(key=lambda item: item["distance_km"])
        return fallback[: max(limit, 1)]

    def _route_summary(
        self,
        graph: nx.DiGraph,
        path: List[int],
        route_name: str,
        emergency_type: str,
        base_speed_kmh: float,
    ) -> Dict[str, Any]:
        """Generate route summary with all metrics."""
        if not path:
            return {
                "route_name": route_name,
                "path_nodes": [],
                "route_coordinates": [],
                "edge_risks": [],
                "segment_with_max_risk": None,
                "total_distance_km": 0.0,
                "risk_score": 0.0,
                "risk_band": "low",
                "estimated_time_min": 0,
                "emergency_type": emergency_type,
            }

        total_distance_m = 0.0
        edge_risks: List[float] = []
        for u, v in zip(path[:-1], path[1:]):
            edge_data = graph.get_edge_data(u, v) or {}
            total_distance_m += float(edge_data.get("length", 0.0))
            edge_risks.append(float(edge_data.get("risk_score", 0.0)))

        total_distance_km = round(total_distance_m / 1000.0, 3)
        risk_score = compute_route_risk_score(edge_risks)
        time_minutes = int(round((total_distance_km / max(base_speed_kmh, 1.0)) * 60.0))
        route_coordinates = [
            [self.node_coords[node][0], self.node_coords[node][1]]
            for node in path
            if node in self.node_coords
        ]

        return {
            "route_name": route_name,
            "path_nodes": path,
            "route_coordinates": route_coordinates,
            "edge_risks": edge_risks,
            "segment_with_max_risk": edge_risks.index(max(edge_risks)) + 1 if edge_risks else None,
            "total_distance_km": total_distance_km,
            "risk_score": risk_score,
            "risk_band": risk_band(risk_score),
            "estimated_time_min": time_minutes,
            "emergency_type": emergency_type,
        }

    def route_options_to_hospital(
        self, latitude: float, longitude: float, emergency_type: str
    ) -> Dict[str, Any]:
        """Compute fastest and safest route options with comparison."""
        hospital = self.nearest_hospital(latitude, longitude)
        if hospital is None:
            raise ValueError("No hospitals available in dataset.")

        source_node = self.nearest_node(latitude, longitude)
        target_node = self.nearest_node(hospital["latitude"], hospital["longitude"])

        if source_node is None or target_node is None:
            raise ValueError("Unable to map coordinates to road graph nodes.")

        graph = self.graph.copy()
        for _, _, edge_data in graph.edges(data=True):
            edge_data["risk_score"] = compute_edge_risk_score(
                float(edge_data.get("length", 0.0)), emergency_type
            )

        fastest_cost, fastest_path = dijkstra(
            graph, 
            source_node, 
            target_node, 
            risk_factor=0.0, 
            blocked_edges=self.blocked_edges
        )
        safest_cost, safest_path = dijkstra(
            graph, 
            source_node, 
            target_node, 
            risk_factor=2.2, 
            blocked_edges=self.blocked_edges
        )

        # Fallback to simulated graph if real graph routing fails
        has_real_fastest = len(fastest_path) > 1
        has_real_safest = len(safest_path) > 1

        if not has_real_fastest and not has_real_safest:
            return self._build_simulated_route_bundle(latitude, longitude, hospital, emergency_type)

        if not fastest_path:
            fastest_path = safest_path
            fastest_cost = safest_cost
        if not safest_path:
            safest_path = fastest_path
            safest_cost = fastest_cost

        fastest_route = self._route_summary(
            graph,
            fastest_path,
            route_name="fastest",
            emergency_type=emergency_type,
            base_speed_kmh=38.0,
        )
        safest_route = self._route_summary(
            graph,
            safest_path,
            route_name="safest",
            emergency_type=emergency_type,
            base_speed_kmh=32.0,
        )

        comparison = {
            "time_difference_min": safest_route["estimated_time_min"] - fastest_route["estimated_time_min"],
            "risk_difference": round(fastest_route["risk_score"] - safest_route["risk_score"], 2),
            "recommended_route": (
                "safest"
                if safest_route["risk_score"] + 8 < fastest_route["risk_score"]
                else "fastest"
            ),
        }

        selected_route = fastest_route if comparison["recommended_route"] == "fastest" else safest_route

        return {
            "start": {"latitude": latitude, "longitude": longitude, "node": source_node},
            "destination": {
                "hospital_id": hospital.get("id", 1),
                "hospital_name": hospital.get("name", "Hospital"),
                "latitude": hospital["latitude"],
                "longitude": hospital["longitude"],
                "distance_km": hospital.get("distance_km", 0.0),
                "node": target_node,
            },
            "emergency_type": emergency_type,
            "fastest_route": {
                **fastest_route,
                "total_cost": round(float(fastest_cost), 3),
            },
            "safest_route": {
                **safest_route,
                "total_cost": round(float(safest_cost), 3),
            },
            "comparison": comparison,
            # Backward-compatible fields
            "path_nodes": selected_route["path_nodes"],
            "route_coordinates": selected_route["route_coordinates"],
            "edge_risks": selected_route["edge_risks"],
            "segment_with_max_risk": selected_route["segment_with_max_risk"],
            "total_distance_km": selected_route["total_distance_km"],
            "total_cost": round(
                float(fastest_cost if comparison["recommended_route"] == "fastest" else safest_cost), 3
            ),
            "risk_score": selected_route["risk_score"],
            "risk_band": selected_route["risk_band"],
            "nearest_hospital_distance_km": hospital.get("distance_km", 0.0),
            "recommended_route": comparison["recommended_route"],
        }

    def _build_simulated_route_bundle(
        self,
        latitude: float,
        longitude: float,
        hospital: Dict[str, Any],
        emergency_type: str,
    ) -> Dict[str, Any]:
        """Build route bundle using demo graph when real routing fails."""
        demo = generate_demo_route_options(
            latitude,
            longitude,
            hospital["latitude"],
            hospital["longitude"],
            emergency_type,
        )
        fastest_route = demo["fastest_route"]
        safest_route = demo["safest_route"]

        comparison = {
            "time_difference_min": safest_route["estimated_time_min"] - fastest_route["estimated_time_min"],
            "risk_difference": round(fastest_route["risk_score"] - safest_route["risk_score"], 2),
            "recommended_route": (
                "safest" if safest_route["risk_score"] + 8 < fastest_route["risk_score"] else "fastest"
            ),
        }

        selected_route = fastest_route if comparison["recommended_route"] == "fastest" else safest_route

        return {
            "start": {
                "latitude": latitude,
                "longitude": longitude,
                "node": demo["source_node"],
                "simulated": True,
            },
            "destination": {
                "hospital_id": hospital.get("id", 1),
                "hospital_name": hospital.get("name", "Hospital"),
                "latitude": hospital["latitude"],
                "longitude": hospital["longitude"],
                "distance_km": hospital.get("distance_km", 0.0),
                "node": demo["target_node"],
                "simulated": True,
            },
            "emergency_type": emergency_type,
            "is_simulated": True,
            "fastest_route": fastest_route,
            "safest_route": safest_route,
            "comparison": comparison,
            "path_nodes": selected_route["path_nodes"],
            "route_coordinates": selected_route["route_coordinates"],
            "edge_risks": selected_route["edge_risks"],
            "segment_with_max_risk": selected_route["segment_with_max_risk"],
            "total_distance_km": selected_route["total_distance_km"],
            "total_cost": selected_route["total_cost"],
            "risk_score": selected_route["risk_score"],
            "risk_band": selected_route["risk_band"],
            "nearest_hospital_distance_km": hospital.get("distance_km", 0.0),
            "recommended_route": comparison["recommended_route"],
        }

    def route_to_hospital(self, latitude: float, longitude: float, emergency_type: str) -> Dict[str, Any]:
        """Compatibility wrapper: return selected route from multi-route options."""
        return self.route_options_to_hospital(latitude, longitude, emergency_type)

    def osrm_route(
        self,
        source_latitude: float,
        source_longitude: float,
        destination_latitude: float,
        destination_longitude: float,
    ) -> Dict[str, Any]:
        """Fetch real-world route from OSRM service."""
        return fetch_osrm_route(
            source_latitude,
            source_longitude,
            destination_latitude,
            destination_longitude,
        )


# ============================================================================
# Flask App & Routes
# ============================================================================

app = Flask(__name__)
CORS(app)
service = EmergencyRoutingService()


@app.route("/", methods=["GET"])
def home():
    """Health check and API information endpoint."""
    return success_response(
        {
            "service": "aidroute-backend",
            "frontend": "nextjs",
            "message": "Backend API is running. Use the Next.js frontend for the UI.",
            "version": "2.0",
        }
    )


@app.route("/simulate-disaster", methods=["POST"])
def simulate_disaster_api():
    """Simulate a disaster by randomly blocking roads and triggering rerouting.
    
    Request: {"type": "flood" | "accident" | "congestion", "latitude": float, "longitude": float}
    Response: {"blocked_roads": [...], "affected_area": "...", "rerouting_triggered": true}
    """
    try:
        payload = request.get_json(silent=True) or {}
        disaster_type = str(payload.get("type", "flood")).lower()
        lat = _safe_float(payload.get("latitude"), 28.61)
        lon = _safe_float(payload.get("longitude"), 77.20)

        # Clear previous blocks
        service.blocked_edges.clear()

        # Randomly block 2-5 edges from the current graph
        edges = list(service.graph.edges())
        if not edges:
            # Fallback for demo mode
            demo_graph, _ = build_demo_city_graph()
            edges = list(demo_graph.edges())

        num_blocks = random.randint(2, 5)
        blocked_list = random.sample(edges, min(num_blocks, len(edges)))
        
        for u, v in blocked_list:
            service.blocked_edges.add((u, v))
            service.blocked_edges.add((v, u)) # Bi-directional block

        blocked_details = []
        for u, v in blocked_list:
            u_coords = service.node_coords.get(u, (0,0))
            v_coords = service.node_coords.get(v, (0,0))
            blocked_details.append({
                "from_node": u,
                "to_node": v,
                "coordinates": [u_coords, v_coords]
            })

        return jsonify({
            "status": "success",
            "data": {
                "disaster_type": disaster_type,
                "severity": "high",
                "blocked_roads": blocked_details,
                "message": f"Simulated {disaster_type} at {lat}, {lon}. {len(blocked_list)} roads blocked.",
                "rerouting_triggered": True
            }
        })
    except Exception as exc:
        app.logger.error(f"FATAL: Simulation failed - {exc}")
        return error_response(f"Disaster Simulation Engine Error: {exc}", 500)


@app.route("/health", methods=["GET"])
def health():
    """Simple health check endpoint."""
    return success_response({"service": "ai-emergency-response-optimizer", "ok": True})


@app.route("/nearest-hospital", methods=["POST"])
def nearest_hospital_api():
    """Find nearest hospital to incident location.
    
    Request: {"latitude": float, "longitude": float, "emergency_type": str}
    Response: {"status": "success", "data": {"hospital": {...}, ...}}
    """
    try:
        latitude, longitude, emergency_type = parse_payload(request.get_json(silent=True))
        hospital = service.nearest_hospital(latitude, longitude)
        if hospital is None:
            return error_response("No hospitals available in dataset.", 404)

        return success_response(
            {
                "latitude": latitude,
                "longitude": longitude,
                "emergency_type": emergency_type,
                "hospital": hospital,
            }
        )
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(f"Unexpected server error: {exc}", 500)


@app.route("/nearby-hospitals", methods=["POST"])
def nearby_hospitals_api():
    """Find nearby hospitals within 5km radius.
    
    Request: {"latitude": float, "longitude": float, "emergency_type": str}
    Response: {"status": "success", "data": {"hospitals": [...]}}
    """
    try:
        latitude, longitude, emergency_type = parse_payload(request.get_json(silent=True))
        hospitals = service.nearby_hospitals(latitude, longitude, radius_km=5.0, limit=3)

        return success_response(
            {
                "latitude": latitude,
                "longitude": longitude,
                "emergency_type": emergency_type,
                "radius_km": 5.0,
                "hospitals": hospitals,
            }
        )
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(f"Unexpected server error: {exc}", 500)


@app.route("/osrm-route", methods=["POST"])
def osrm_route_api():
    """Fetch real driving route from OSRM service.
    
    Request: {"source_latitude": float, "source_longitude": float,
              "destination_latitude": float, "destination_longitude": float}
    Response: {"status": "success", "data": {"route_coordinates": [...], "distance_km": float, ...}}
    """
    try:
        payload = request.get_json(silent=True)
        if payload is None:
            raise ValueError("Request body must be valid JSON.")

        source_latitude = payload.get("source_latitude") or payload.get("sourceLatitude") or payload.get("latitude")
        source_longitude = payload.get("source_longitude") or payload.get("sourceLongitude") or payload.get("longitude")
        destination_latitude = payload.get("destination_latitude") or payload.get("destinationLatitude")
        destination_longitude = payload.get("destination_longitude") or payload.get("destinationLongitude")

        if source_latitude is None or source_longitude is None:
            raise ValueError("Source latitude and longitude are required.")
        if destination_latitude is None or destination_longitude is None:
            raise ValueError("Destination latitude and longitude are required.")

        try:
            source_latitude = float(source_latitude)
            source_longitude = float(source_longitude)
            destination_latitude = float(destination_latitude)
            destination_longitude = float(destination_longitude)
        except (TypeError, ValueError) as exc:
            raise ValueError("All coordinates must be numeric values.") from exc

        if not (-90.0 <= source_latitude <= 90.0 and -90.0 <= destination_latitude <= 90.0):
            raise ValueError("Latitude must be between -90 and 90.")
        if not (-180.0 <= source_longitude <= 180.0 and -180.0 <= destination_longitude <= 180.0):
            raise ValueError("Longitude must be between -180 and 180.")

        route = service.osrm_route(
            source_latitude,
            source_longitude,
            destination_latitude,
            destination_longitude,
        )

        return success_response(
            {
                "source": {
                    "latitude": source_latitude,
                    "longitude": source_longitude,
                },
                "destination": {
                    "latitude": destination_latitude,
                    "longitude": destination_longitude,
                },
                **route,
            }
        )
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(f"Unexpected server error: {exc}", 500)


@app.route("/get-route", methods=["POST"])
def get_route_api():
    """Get optimal route to nearest hospital.
    
    Request: {"latitude": float, "longitude": float, "emergency_type": str}
    Response: {"status": "success", "data": {"fastest_route": {...}, "safest_route": {...}, ...}}
    """
    try:
        latitude, longitude, emergency_type = parse_payload(request.get_json(silent=True))
        route_data = service.route_to_hospital(latitude, longitude, emergency_type)
        return success_response(route_data)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(f"Unexpected server error: {exc}", 500)


@app.route("/predict-risk", methods=["POST"])
def predict_risk_api():
    """Predict risk score for the route to nearest hospital.
    
    Request: {"latitude": float, "longitude": float, "emergency_type": str}
    Response: {"status": "success", "data": {"risk_score": float, "risk_level": str, ...}}
    """
    try:
        latitude, longitude, emergency_type = parse_payload(request.get_json(silent=True))
        route_data = service.route_to_hospital(latitude, longitude, emergency_type)
        route_coordinates = route_data.get("route_coordinates", [])
        
        if route_coordinates:
            evaluation = evaluate_emergency_risk(
                route_coordinates=route_coordinates,
                emergency_type=emergency_type,
            )
        else:
            evaluation = evaluate_emergency_risk(
                location=f"{latitude},{longitude}",
                emergency_type=emergency_type,
            )

        risk_level = _normalize_risk_level(str(evaluation.get("risk_level", "low")))
        risk_band_value = "high" if risk_level == "high" else "medium" if risk_level == "medium" else "low"

        return success_response(
            {
                "emergency_type": emergency_type,
                "route_distance_km": route_data.get("total_distance_km", 0.0),
                "traffic_density": evaluation.get("traffic_density", 0.0),
                "accident_probability": evaluation.get("accident_probability", 0.0),
                "risk_score": evaluation.get("risk_score", 0.0),
                "risk_level": risk_level,
                "explanation": evaluation.get("explanation", ""),
                "recommendation": evaluation.get("recommendation", ""),
                "risk_band": risk_band_value,
            }
        )
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(f"Unexpected server error: {exc}", 500)


@app.route("/estimate-traffic", methods=["POST"])
def estimate_traffic_api():
    """Estimate traffic score from time of day and location type.
    
    Request: {"time_of_day": str, "location_type": str, "random_variability": float}
    Response: {"status": "success", "data": {"traffic_score": float, ...}}
    """
    try:
        time_of_day, location_type, random_variability = parse_traffic_payload(
            request.get_json(silent=True)
        )
        result = estimate_traffic_score(
            time_of_day=time_of_day,
            location_type=location_type,
            random_variability=random_variability,
        )
        return success_response(result)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(f"Unexpected server error: {exc}", 500)


@app.route("/decision-engine", methods=["POST"])
def decision_engine_api():
    """Compare multiple routes and return the best route with explanation.
    
    Request: {"routes": [{"name": str, "distance": float, "eta": int, "risk_score": float}, ...]}
    Response: {"status": "success", "data": {"best_route": str, "explanation": str, ...}}
    """
    try:
        payload = request.get_json(silent=True)
        if payload is None:
            raise ValueError("Request body must be valid JSON.")

        routes = payload.get("routes")
        if not isinstance(routes, list) or len(routes) < 2:
            raise ValueError("routes must contain at least two route objects.")

        decision = compare_routes(routes)
        return success_response(decision)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(f"Unexpected server error: {exc}", 500)


@app.route("/live-alerts", methods=["POST"])
def live_alerts_api():
    """Generate live alerts for current emergency scenario.
    
    Request: {"latitude": float, "longitude": float, "emergency_type": str}
    Response: {"status": "success", "data": {"alerts": [...], "scenario": {...}, ...}}
    """
    try:
        latitude, longitude, emergency_type = parse_payload(request.get_json(silent=True))
        route_bundle = service.route_options_to_hospital(latitude, longitude, emergency_type)
        baseline_risk = _safe_float(route_bundle.get("risk_score"), 0.0)
        scenario = _simulate_emergency_scenario(emergency_type, latitude, longitude)
        alerts = _build_dynamic_alerts(baseline_risk, scenario)

        return success_response(
            {
                "alerts": alerts,
                "scenario": scenario,
                "risk_score": baseline_risk,
                "emergency_type": emergency_type,
                "updated_at": int(time.time()),
            }
        )
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(f"Unexpected server error: {exc}", 500)


@app.route("/optimize-route", methods=["POST"])
def optimize_route_api():
    """Return nearest hospital and fastest/safest route options with risk scoring.
    
    Request: {"latitude": float, "longitude": float, "emergency_type": str}
    Response: {"status": "success", "data": {"hospital": {...}, "routes": [...], "decision": {...}, ...}}
    """
    try:
        latitude, longitude, emergency_type = parse_payload(request.get_json(silent=True))
        route_bundle = service.route_options_to_hospital(latitude, longitude, emergency_type)

        # Extract hospital information with consistent schema
        destination = route_bundle.get("destination", {})
        hospital = {
            "id": destination.get("hospital_id", 1),
            "name": destination.get("hospital_name", "Hospital"),
            "latitude": destination.get("latitude", 0.0),
            "longitude": destination.get("longitude", 0.0),
            "distance_km": destination.get("distance_km", 0.0),
        }

        # Try to fetch OSRM route
        osrm_route: Optional[Dict[str, Any]] = None
        try:
            osrm_route = service.osrm_route(
                latitude,
                longitude,
                float(hospital["latitude"]),
                float(hospital["longitude"]),
            )
        except ValueError:
            osrm_route = None

        fastest_route = route_bundle.get("fastest_route", {})
        safest_route = route_bundle.get("safest_route", {})
        scenario = _simulate_emergency_scenario(emergency_type, latitude, longitude)

        # AI-Powered Disaster Context
        disaster_text = (
            f"{emergency_type} incident near {hospital['name']}. "
            f"Coordinates: {latitude}, {longitude}. "
            f"Scenario info: {scenario.get('summary', '')}."
        )
        disaster_analysis = analyze_disaster(disaster_text)

        # Override with OSRM route if available
        if osrm_route:
            fastest_route = {
                "route_coordinates": osrm_route.get("route_coordinates", []),
                "total_distance_km": osrm_route.get("distance_km", 0.0),
                "estimated_time_min": int(round(osrm_route.get("duration_min", 0))),
                "risk_score": _safe_float(fastest_route.get("risk_score"), 0.0),
                "risk_band": fastest_route.get("risk_band", "low"),
            }

        # Build formatted routes for response
        fastest_formatted = {
            "type": "fastest",
            "path": fastest_route.get("route_coordinates", []),
            "distance": _safe_float(fastest_route.get("total_distance_km"), 0.0),
            "eta": int(fastest_route.get("estimated_time_min", 0)),
            "risk_score": _safe_float(fastest_route.get("risk_score"), 0.0),
            "risk_level": _normalize_risk_level(fastest_route.get("risk_band", "low")),
            "risk_explanation": _risk_explanation(
                _safe_float(fastest_route.get("risk_score"), 0.0),
                _normalize_risk_level(fastest_route.get("risk_band", "low")),
                emergency_type,
                scenario.get("title", "Emergency Response"),
            ),
            "recommendation": "High-speed emergency path.",
        }

        safest_formatted = {
            "type": "safest",
            "path": safest_route.get("route_coordinates", []),
            "distance": _safe_float(safest_route.get("total_distance_km"), 0.0),
            "eta": int(safest_route.get("estimated_time_min", 0)),
            "risk_score": _safe_float(safest_route.get("risk_score"), 0.0),
            "risk_level": _normalize_risk_level(safest_route.get("risk_band", "low")),
            "risk_explanation": _risk_explanation(
                _safe_float(safest_route.get("risk_score"), 0.0),
                _normalize_risk_level(safest_route.get("risk_band", "low")),
                emergency_type,
                scenario.get("title", "Emergency Response"),
            ),
            "recommendation": "Safety-first protocol path.",
        }

        # --- Decision Engine Logic ---
        # Determine priority based on disaster severity
        severity = _normalize_risk_level(disaster_analysis.get("severity", "low"))
        if severity == "high":
            decision_priority = "safety"
        elif severity == "medium":
            decision_priority = "balanced"
        else:
            decision_priority = "speed"

        # Weights based on priority
        if decision_priority == "safety":
            weights = {"distance": 0.1, "time": 0.1, "risk": 0.5, "severity": 0.3}
        elif decision_priority == "speed":
            weights = {"distance": 0.3, "time": 0.5, "risk": 0.1, "severity": 0.1}
        else: # balanced
            weights = {"distance": 0.25, "time": 0.25, "risk": 0.25, "severity": 0.25}

        # Calculate final scores
        def calculate_score(route, severity_val):
            # Normalizing values: Lower is better (cost-based scoring)
            # Distance: 0-20km, Time: 0-60min, Risk: 0-10, Severity: 0-10
            dist_score = min(_safe_float(route["distance"]) / 20.0, 1.0)
            time_score = min(_safe_float(route["eta"]) / 60.0, 1.0)
            risk_score = min(_safe_float(route["risk_score"]) / 10.0, 1.0)
            sev_score = min(_safe_float(severity_val) / 10.0, 1.0)
            
            total = (
                weights["distance"] * dist_score +
                weights["time"] * time_score +
                weights["risk"] * risk_score +
                weights["severity"] * sev_score
            )
            # Return 0-100 score where HIGHER is better
            return round(100.0 * (1.0 - total), 2)

        sev_level_score = 10.0 if severity == "high" else 5.0 if severity == "medium" else 2.0
        fastest_decision_score = calculate_score(fastest_formatted, sev_level_score)
        safest_decision_score = calculate_score(safest_formatted, sev_level_score)

        # Final decision selection
        if safest_decision_score > fastest_decision_score:
            selected_route_name = "safest"
            final_score = safest_decision_score
            justification = (
                f"Prioritized {decision_priority} due to {severity} disaster severity. "
                "Selected safest route to minimize operational risk despite longer ETA."
            )
        else:
            selected_route_name = "fastest"
            final_score = fastest_decision_score
            justification = (
                f"Prioritized {decision_priority} due to {severity} disaster severity. "
                "Selected fastest route to ensure rapid intervention and resource delivery."
            )

        # Build complete response
        response = {
            "hospital": hospital,
            "routes": [fastest_formatted, safest_formatted],
            "final_decision": {
                "selected_route": selected_route_name,
                "decision_priority": decision_priority,
                "score": final_score,
                "justification": justification
            },
            "scenario": scenario,
            "disaster_analysis": disaster_analysis,
            "alerts": _build_dynamic_alerts(
                _safe_float(safest_formatted["risk_score"] if selected_route_name == "safest" else fastest_formatted["risk_score"]),
                scenario,
            ),
            "status_text": {
                "decision": "Intelligence engine evaluated",
                "risk": "Risk analysis complete",
                "route": "Route optimization complete",
            },
        }

        # Final Selected Route object for AI analysis
        selected_route_obj = safest_formatted if selected_route_name == "safest" else fastest_formatted

        resource_action = recommend_action(
            {
                "incident": disaster_text,
                "severity": disaster_analysis.get("severity", "low"),
                "scenario": scenario,
                "hospital": hospital,
                "best_route": response["final_decision"],
                "risk_score": response["final_decision"]["score"],
            }
        )
        route_explanation = explain_route(
            selected_route_obj,
            {
                "severity": disaster_analysis.get("severity", "low"),
                "risk_score": selected_route_obj.get("risk_score", 0.0),
                "risk_level": selected_route_obj.get("risk_level", "low"),
                "traffic_score": _safe_float(selected_route_obj.get("traffic_score", 5.0)),
                "eta_min": selected_route_obj.get("eta", 0),
                "distance_km": selected_route_obj.get("distance", 0.0),
            },
        )

        response["ai"] = {
            "disaster_analysis": disaster_analysis,
            "recommended_action": resource_action,
            "route_explanation": route_explanation,
        }

        return success_response(response)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        app.logger.error(f"FATAL: Optimize route failure: {exc}", exc_info=True)
        return error_response(f"Intelligent Routing Engine Error: {exc}", 500)


# ============================================================================
# Error Handlers
# ============================================================================


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return error_response("Endpoint not found", 404)


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return error_response("Method not allowed", 405)


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return error_response("Internal server error", 500)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").strip().lower() in {"1", "true", "yes", "on"},
    )
