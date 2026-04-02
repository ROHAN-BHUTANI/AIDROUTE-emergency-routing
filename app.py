"""Flask backend for the AI Emergency Response Optimizer.

This service provides:
- nearest hospital detection from CSV
- Dijkstra-based route optimization
- route-level risk prediction
"""

from __future__ import annotations

import json
import math
import os
from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import URLError
from urllib.request import Request, urlopen

import networkx as nx
import pandas as pd
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from risk_model import (
    build_route_risk_insights,
    compute_edge_risk_score,
    compute_route_risk_score,
    compare_routes,
    evaluate_emergency_risk,
    estimate_traffic_score,
    risk_band,
)
from routing import dijkstra, generate_demo_route_options


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

ROADS_PATH = DATA_DIR / "roads.csv"
LOCATIONS_PATH = DATA_DIR / "locations.csv"
HOSPITALS_PATH = DATA_DIR / "hospitals.csv"
POIS_PATH = DATA_DIR / "pois.csv"
OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"


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
    request = Request(url, headers={"User-Agent": "AIDROUTE/1.0"})

    try:
        with urlopen(request, timeout=15) as response:
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
    """Fetch nearby hospitals from OpenStreetMap via Overpass and rank them by distance."""
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

    request = Request(
        OVERPASS_API_URL,
        data=query.encode("utf-8"),
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "AIDROUTE/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
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


class EmergencyRoutingService:
    """Core service that loads data once and serves routing queries."""

    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self.node_coords: Dict[int, Tuple[float, float]] = {}
        self.hospitals: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self) -> None:
        self.node_coords = self._load_locations()
        self.graph = self._load_graph()
        self.hospitals = self._load_hospitals()

    def _load_locations(self) -> Dict[int, Tuple[float, float]]:
        locations_df = pd.read_csv(LOCATIONS_PATH, usecols=["osmid", "y", "x"])
        return {
            int(row.osmid): (float(row.y), float(row.x))
            for row in locations_df.itertuples(index=False)
        }

    def _load_graph(self) -> nx.DiGraph:
        roads_df = pd.read_csv(ROADS_PATH)

        u_col = "u" if "u" in roads_df.columns else roads_df.columns[0]
        v_col = "v" if "v" in roads_df.columns else roads_df.columns[1]
        length_col = "length" if "length" in roads_df.columns else roads_df.columns[2]

        graph = nx.DiGraph()
        for row in roads_df[[u_col, v_col, length_col]].itertuples(index=False):
            u, v, length = int(row[0]), int(row[1]), float(row[2])
            graph.add_edge(u, v, length=length, risk_score=0.0)
        return graph

    def _load_hospitals(self) -> List[Dict[str, Any]]:
        # Primary source: explicit hospital dataset.
        if HOSPITALS_PATH.exists():
            hospitals_df = pd.read_csv(HOSPITALS_PATH)
            return [
                {
                    "id": idx,
                    "name": str(getattr(row, "name", f"Hospital {idx}")),
                    "latitude": float(getattr(row, "latitude")),
                    "longitude": float(getattr(row, "longitude")),
                }
                for idx, row in enumerate(hospitals_df.itertuples(index=False), start=1)
            ]

        # Fallback source: POI dataset if dedicated hospital file is not present.
        if not POIS_PATH.exists():
            return []

        pois_df = pd.read_csv(POIS_PATH)
        if "amenity" not in pois_df.columns or "geometry" not in pois_df.columns:
            return []

        hospitals: List[Dict[str, Any]] = []
        hospitals_df = pois_df[pois_df["amenity"].astype(str).str.lower() == "hospital"].copy()
        for idx, row in enumerate(hospitals_df.itertuples(index=False), start=1):
            geometry = str(getattr(row, "geometry", "")).strip()
            if not geometry.startswith("POINT (") or not geometry.endswith(")"):
                continue
            lon_lat = geometry[7:-1].split()
            if len(lon_lat) != 2:
                continue
            lon, lat = float(lon_lat[0]), float(lon_lat[1])
            hospitals.append(
                {
                    "id": idx,
                    "name": "Hospital",
                    "latitude": lat,
                    "longitude": lon,
                }
            )
        return hospitals

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
        if nearby_hospitals := self.nearby_hospitals(latitude, longitude, radius_km=5.0, limit=3):
            return {"id": 1, **nearby_hospitals[0]}

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
        with suppress(ValueError):
            if hospitals := fetch_overpass_hospitals(latitude, longitude, radius_km=radius_km, limit=limit):
                return hospitals

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

    def route_options_to_hospital(self, latitude: float, longitude: float, emergency_type: str) -> Dict[str, Any]:
        """Compute fastest and safest route options with a comparison summary."""
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

        fastest_cost, fastest_path = dijkstra(graph, source_node, target_node, risk_factor=0.0)
        safest_cost, safest_path = dijkstra(graph, source_node, target_node, risk_factor=2.2)

        # Fallback to simulated graph demo when real-world graph routing is disconnected
        # or collapses into a zero-distance same-node route.
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
                "hospital_id": hospital["id"],
                "hospital_name": hospital["name"],
                "latitude": hospital["latitude"],
                "longitude": hospital["longitude"],
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
            # Backward-compatible fields used by existing frontend.
            "path_nodes": selected_route["path_nodes"],
            "route_coordinates": selected_route["route_coordinates"],
            "edge_risks": selected_route["edge_risks"],
            "segment_with_max_risk": selected_route["segment_with_max_risk"],
            "total_distance_km": selected_route["total_distance_km"],
            "total_cost": round(float(fastest_cost if comparison["recommended_route"] == "fastest" else safest_cost), 3),
            "risk_score": selected_route["risk_score"],
            "risk_band": selected_route["risk_band"],
            "nearest_hospital_distance_km": hospital["distance_km"],
            "recommended_route": comparison["recommended_route"],
        }

    def _build_simulated_route_bundle(
        self,
        latitude: float,
        longitude: float,
        hospital: Dict[str, Any],
        emergency_type: str,
    ) -> Dict[str, Any]:
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
                "hospital_id": hospital["id"],
                "hospital_name": hospital["name"],
                "latitude": hospital["latitude"],
                "longitude": hospital["longitude"],
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
            "nearest_hospital_distance_km": hospital["distance_km"],
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
        return fetch_osrm_route(
            source_latitude,
            source_longitude,
            destination_latitude,
            destination_longitude,
        )


app = Flask(__name__)
CORS(app)
service = EmergencyRoutingService()


def parse_payload(payload: Optional[Dict[str, Any]]) -> Tuple[float, float, str]:
    if payload is None:
        raise ValueError("Request body must be valid JSON.")

    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    emergency_type = payload.get("emergency_type")
    if emergency_type is None:
        emergency_type = payload.get("emergency type")
    if emergency_type is None:
        emergency_type = payload.get("emergencyType")
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

    allowed_emergencies = {"medical", "accident", "fire", "flood", "earthquake", "landslide"}
    if emergency_type not in allowed_emergencies:
        raise ValueError(
            "Unsupported emergency_type. Allowed values: medical, accident, fire, flood, earthquake, landslide."
        )

    return lat, lon, emergency_type


def parse_traffic_payload(payload: Optional[Dict[str, Any]]) -> Tuple[str, str, Optional[float]]:
    if payload is None:
        raise ValueError("Request body must be valid JSON.")

    time_of_day = str(payload.get("time_of_day", payload.get("timeOfDay", ""))).strip()
    location_type = str(payload.get("location_type", payload.get("locationType", ""))).strip().lower()
    random_variability = payload.get("random_variability", payload.get("randomVariability"))

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


def success_response(data: Dict[str, Any], status_code: int = 200):
    return jsonify({"status": "success", "data": data}), status_code


def error_response(message: str, status_code: int = 400):
    return jsonify({"status": "error", "message": message}), status_code


def _to_title_risk_level(band: str) -> str:
    normalized = str(band or "").strip().lower()
    mapping = {
        "high": "High",
        "moderate": "Medium",
        "medium": "Medium",
        "low": "Low",
    }
    return mapping.get(normalized, "Low")


def _format_route_for_optimize(route_type: str, route_data: Dict[str, Any], emergency_type: str) -> Dict[str, Any]:
    route_coordinates = route_data.get("route_coordinates", [])
    evaluation = evaluate_emergency_risk(
        route_coordinates=route_coordinates,
        emergency_type=emergency_type,
    )
    recommendation = evaluation.get(
        "recommendation", "Proceed with caution based on current road conditions."
    )

    route_risk_score = float(evaluation.get("risk_score", 0.0))
    route_risk_level = str(evaluation.get("risk_level", "Low"))

    return {
        "type": route_type,
        "path": route_coordinates,
        "distance": float(route_data.get("total_distance_km", 0.0)),
        "eta": int(route_data.get("estimated_time_min", 0)),
        "risk_score": route_risk_score,
        "risk_level": route_risk_level,
        "recommendation": recommendation,
    }


def _build_decision_payload(routes: List[Dict[str, Any]]) -> Dict[str, Any]:
    decision = compare_routes(routes)
    best_route = decision["best_route"]
    return {
        "best_route": best_route,
        "explanation": decision["explanation"],
        "recommendation": decision["recommendation"],
        "ranked_routes": decision["ranked_routes"],
        "criteria": decision["criteria"],
    }


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return success_response({"service": "ai-emergency-response-optimizer", "ok": True})


@app.route("/nearest-hospital", methods=["POST"])
def nearest_hospital_api():
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
    """Return a single OSRM driving route between source and destination coordinates."""
    try:
        payload = request.get_json(silent=True)
        if payload is None:
            raise ValueError("Request body must be valid JSON.")

        source_latitude = payload.get("source_latitude", payload.get("sourceLatitude", payload.get("latitude")))
        source_longitude = payload.get(
            "source_longitude",
            payload.get("sourceLongitude", payload.get("longitude")),
        )
        destination_latitude = payload.get(
            "destination_latitude",
            payload.get("destinationLatitude"),
        )
        destination_longitude = payload.get(
            "destination_longitude",
            payload.get("destinationLongitude"),
        )

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

        risk_level = str(evaluation.get("risk_level", "Low")).strip().lower()
        risk_band_value = "high" if risk_level == "high" else "moderate" if risk_level == "medium" else "low"

        return success_response(
            {
                "emergency_type": emergency_type,
                "route_distance_km": route_data["total_distance_km"],
                "traffic_density": evaluation["traffic_density"],
                "accident_probability": evaluation["accident_probability"],
                "risk_score": evaluation["risk_score"],
                "risk_level": evaluation["risk_level"],
                "explanation": evaluation["explanation"],
                "recommendation": evaluation["recommendation"],
                "risk_band": risk_band_value,
            }
        )
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(f"Unexpected server error: {exc}", 500)


@app.route("/estimate-traffic", methods=["POST"])
def estimate_traffic_api():
    """Estimate traffic score from time of day, location type, and variability."""
    try:
        time_of_day, location_type, random_variability = parse_traffic_payload(request.get_json(silent=True))
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
    """Compare multiple routes and return the best route with an explanation."""
    try:
        payload = request.get_json(silent=True)
        if payload is None:
            raise ValueError("Request body must be valid JSON.")

        routes = payload.get("routes")
        if not isinstance(routes, list) or len(routes) < 2:
            raise ValueError("routes must contain at least two route objects.")

        decision = _build_decision_payload(routes)
        return success_response(decision)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(f"Unexpected server error: {exc}", 500)


@app.route("/optimize-route", methods=["POST"])
def optimize_route_api():
    """Return nearest hospital and fastest/safest route options in a clean JSON schema."""
    try:
        latitude, longitude, emergency_type = parse_payload(request.get_json(silent=True))
        route_bundle = service.route_options_to_hospital(latitude, longitude, emergency_type)

        destination = route_bundle.get("destination", {})
        hospital = {
            "name": str(destination.get("hospital_name", "")),
            "lat": float(destination.get("latitude", 0.0)),
            "lon": float(destination.get("longitude", 0.0)),
        }

        osrm_route: Optional[Dict[str, Any]] = None
        try:
            osrm_route = service.osrm_route(
                latitude,
                longitude,
                float(destination.get("latitude", latitude)),
                float(destination.get("longitude", longitude)),
            )
        except ValueError:
            osrm_route = None

        fastest_route = route_bundle.get("fastest_route", {})
        safest_route = route_bundle.get("safest_route", {})

        if osrm_route:
            fastest_route = {
                "route_coordinates": osrm_route["route_coordinates"],
                "total_distance_km": osrm_route["distance_km"],
                "estimated_time_min": int(round(osrm_route["duration_min"])),
            }

        decision = _build_decision_payload(
            [
                {
                    "name": "fastest",
                    "distance": fastest_route.get("total_distance_km", 0.0),
                    "eta": fastest_route.get("estimated_time_min", 0),
                    "traffic_score": fastest_route.get("traffic_score"),
                    "risk_score": fastest_route.get("risk_score", 0.0),
                    "path": fastest_route.get("route_coordinates", []),
                    "recommendation": fastest_route.get("recommendation", ""),
                },
                {
                    "name": "safest",
                    "distance": safest_route.get("total_distance_km", 0.0),
                    "eta": safest_route.get("estimated_time_min", 0),
                    "traffic_score": safest_route.get("traffic_score"),
                    "risk_score": safest_route.get("risk_score", 0.0),
                    "path": safest_route.get("route_coordinates", []),
                    "recommendation": safest_route.get("recommendation", ""),
                },
            ]
        )

        response = {
            "hospital": hospital,
            "routes": [
                _format_route_for_optimize("fastest", fastest_route, emergency_type),
                _format_route_for_optimize("safest", safest_route, emergency_type),
            ],
            "decision": decision,
        }
        return jsonify(response), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Unexpected server error while optimizing route."}), 500


if __name__ == "__main__":
    # debug=False is safer for production-like runs.
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").strip().lower() in {"1", "true", "yes", "on"},
    )

