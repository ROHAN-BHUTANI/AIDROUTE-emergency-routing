import random
from typing import Any, Dict, Iterable, List, Optional, Tuple

EMERGENCY_WEIGHTS = {
    "medical": 1.0,
    "fire": 1.3,
    "flood": 1.5,
    "earthquake": 1.7,
    "landslide": 1.6,
    "accident": 1.2,
}

SIMULATED_LOCATION_DATA: Dict[str, Dict[str, float]] = {
    "dehradun": {"traffic_density": 7.4, "accident_probability": 5.3},
    "haridwar": {"traffic_density": 8.1, "accident_probability": 6.7},
    "nainital": {"traffic_density": 5.2, "accident_probability": 4.9},
    "almora": {"traffic_density": 3.8, "accident_probability": 3.2},
    "rishikesh": {"traffic_density": 6.5, "accident_probability": 5.8},
}


def emergency_multiplier(emergency_type: str) -> float:
    if not emergency_type:
        return 1.0
    return EMERGENCY_WEIGHTS.get(emergency_type.strip().lower(), 1.0)


def compute_edge_risk_score(length_m: float, emergency_type: str) -> float:
    # Base risk increases with edge length; emergency type scales risk upward.
    base_risk = min(max(length_m, 0.0) / 5000.0, 1.0)
    return min(base_risk * emergency_multiplier(emergency_type), 1.0)


def compute_route_risk_score(edge_risk_scores: Iterable[float]) -> float:
    scores = [min(max(score, 0.0), 1.0) for score in edge_risk_scores]
    return round((sum(scores) / len(scores)) * 100.0, 2) if scores else 0.0


def risk_band(risk_score: float) -> str:
    if risk_score >= 75:
        return "high"
    return "moderate" if risk_score >= 40 else "low"


def _band_from_level(level: str) -> str:
    normalized = level.strip().lower()
    return {"high": "high", "medium": "moderate", "low": "low"}.get(normalized, "low")


def _zone_from_coordinates(latitude: float, longitude: float) -> str:
    if latitude >= 28.62:
        return "northern zone"
    return "eastern corridor" if longitude >= 77.22 else "central zone"


def _simulate_route_signals(route_coordinates: List[List[float]]) -> Tuple[float, float, str]:
    """Simulate traffic and accident signals (0-10) for a route."""
    if not route_coordinates:
        return 0.0, 0.0, "central zone"

    seed = "|".join(f"{point[0]:.4f},{point[1]:.4f}" for point in route_coordinates)
    seeded_random = random.Random(seed)

    centroid_lat = sum(point[0] for point in route_coordinates) / len(route_coordinates)
    centroid_lon = sum(point[1] for point in route_coordinates) / len(route_coordinates)
    zone = _zone_from_coordinates(centroid_lat, centroid_lon)

    traffic = seeded_random.uniform(4.0, 8.8)
    accident = seeded_random.uniform(2.5, 7.9)

    # Slightly increase pressure with longer routes.
    route_factor = min(max(len(route_coordinates) - 2, 0), 6) * 0.18
    traffic = min(round(traffic + route_factor, 2), 10.0)
    accident = min(round(accident + (route_factor * 0.6), 2), 10.0)

    return traffic, accident, zone


def _normalize_time_of_day(time_of_day: str) -> Tuple[int, str]:
    normalized = (time_of_day or "").strip().lower()
    if not normalized:
        return 12, "midday"

    keyword_map = {
        "morning": (8, "morning peak"),
        "rush morning": (8, "morning peak"),
        "peak morning": (8, "morning peak"),
        "noon": (12, "midday"),
        "midday": (12, "midday"),
        "afternoon": (15, "afternoon flow"),
        "evening": (18, "evening peak"),
        "rush evening": (18, "evening peak"),
        "peak evening": (18, "evening peak"),
        "night": (22, "night off-peak"),
        "late night": (23, "night off-peak"),
        "dawn": (5, "early morning"),
    }
    if normalized in keyword_map:
        return keyword_map[normalized]

    if ":" in normalized:
        hour_part = normalized.split(":", 1)[0]
        try:
            hour = int(hour_part)
        except ValueError:
            return 12, "midday"
        hour = max(0, min(hour, 23))
        return hour, _time_label_from_hour(hour)

    if normalized.endswith("am") or normalized.endswith("pm"):
        try:
            hour_value = int(normalized[:-2].strip())
        except ValueError:
            return 12, "midday"
        hour_value = hour_value % 12
        if normalized.endswith("pm"):
            hour_value += 12
        return hour_value, _time_label_from_hour(hour_value)

    try:
        hour = int(normalized)
    except ValueError:
        return 12, "midday"

    hour = max(0, min(hour, 23))
    return hour, _time_label_from_hour(hour)


def _time_label_from_hour(hour: int) -> str:
    if 7 <= hour <= 10:
        return "morning peak"
    if 11 <= hour <= 15:
        return "midday"
    if 16 <= hour <= 19:
        return "evening peak"
    if 20 <= hour <= 23:
        return "night off-peak"
    return "early morning"


def estimate_traffic_score(
    time_of_day: str,
    location_type: str,
    random_variability: Optional[float] = None,
) -> Dict[str, Any]:
    """Estimate traffic intensity on a 0-10 scale from time, urbanicity, and variability."""
    hour, time_label = _normalize_time_of_day(time_of_day)
    location_normalized = (location_type or "").strip().lower()
    is_urban = location_normalized in {"urban", "city", "metro", "metropolitan", "true", "yes", "1"}

    if random_variability is None:
        seed = f"{hour}|{location_normalized}|{time_of_day.strip().lower()}"
        variability = random.Random(seed).uniform(0.0, 1.0)
    else:
        variability = max(0.0, min(float(random_variability), 1.0))

    if 7 <= hour <= 10 or 17 <= hour <= 20:
        time_component = 7.6
    elif 11 <= hour <= 15:
        time_component = 5.2
    elif 0 <= hour <= 5:
        time_component = 2.4
    else:
        time_component = 3.8

    location_component = 2.4 if is_urban else 0.8
    variability_component = (variability * 2.4) - 1.2

    traffic_score = round(min(max(time_component + location_component + variability_component, 0.0), 10.0), 2)

    if traffic_score >= 7.5:
        explanation = f"Peak hour traffic detected in {'urban' if is_urban else 'non-urban'} zone during {time_label}."
    elif traffic_score >= 4.5:
        explanation = f"Moderate traffic expected in {'urban' if is_urban else 'non-urban'} zone during {time_label}."
    else:
        explanation = f"Low traffic conditions expected in {'urban' if is_urban else 'non-urban'} zone during {time_label}."

    return {
        "traffic_score": traffic_score,
        "explanation": explanation,
        "time_of_day": time_of_day,
        "normalized_time": time_label,
        "location_type": "urban" if is_urban else "non-urban",
        "random_variability": round(variability, 2),
    }


def _clamp(value: float, minimum: float = 0.0, maximum: float = 10.0) -> float:
    return max(minimum, min(value, maximum))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def _estimate_route_traffic_score(route: Dict[str, Any]) -> float:
    explicit_traffic = route.get("traffic_score", route.get("traffic_density", route.get("estimated_traffic")))
    if explicit_traffic is not None:
        return round(_clamp(_safe_float(explicit_traffic)), 2)

    distance_km = _safe_float(route.get("distance", route.get("total_distance_km", 0.0)))
    eta_min = _safe_float(route.get("eta", route.get("estimated_time_min", 0.0)))

    if distance_km <= 0.0 or eta_min <= 0.0:
        return 0.0

    minutes_per_km = eta_min / max(distance_km, 0.1)
    return round(_clamp(minutes_per_km * 2.5), 2)


def _route_display_name(route: Dict[str, Any], index: int) -> str:
    value = route.get("type") or route.get("route_name") or route.get("name") or route.get("label")
    if value:
        return str(value)
    return f"route_{index + 1}"


def _route_decision_reason(best: Dict[str, Any], runner_up: Dict[str, Any]) -> str:
    best_name = best["name"].replace("_", " ").title()
    runner_up_name = runner_up["name"].replace("_", " ").title()

    risk_delta = round(runner_up["risk_score"] - best["risk_score"], 2)
    traffic_delta = round(runner_up["traffic_score"] - best["traffic_score"], 2)
    distance_delta = round(runner_up["distance_km"] - best["distance_km"], 2)
    eta_delta = round(runner_up["eta_min"] - best["eta_min"], 1)

    if best["risk_score"] < runner_up["risk_score"] and eta_delta < 0:
        return (
            f"{best_name} is safer despite being {abs(eta_delta):.1f} minutes longer than {runner_up_name} "
            f"because it has {abs(traffic_delta):.1f}/10 lower congestion and a {abs(risk_delta):.1f}/10 lower risk score."
        )

    if best["distance_km"] < runner_up["distance_km"] and best["risk_score"] <= runner_up["risk_score"]:
        return (
            f"{best_name} is the best overall choice because it is {abs(distance_delta):.2f} km shorter "
            f"while keeping traffic and risk under control."
        )

    if best["traffic_score"] < runner_up["traffic_score"]:
        return (
            f"{best_name} is preferred because it keeps congestion lower than {runner_up_name} "
            f"even though other route metrics are similar."
        )

    return (
        f"{best_name} has the strongest combined balance of distance, estimated traffic, and risk compared with {runner_up_name}."
    )


def compare_routes(routes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Rank multiple routes using distance, estimated traffic, and risk score."""
    if len(routes) < 2:
        raise ValueError("Provide at least two routes to compare.")

    normalized_routes: List[Dict[str, Any]] = []
    for index, route in enumerate(routes):
        name = _route_display_name(route, index)
        distance_km = _safe_float(route.get("distance", route.get("total_distance_km", route.get("distance_km", 0.0))))
        eta_min = _safe_float(route.get("eta", route.get("estimated_time_min", route.get("duration_min", 0.0))))
        risk_score = _safe_float(route.get("risk_score", 0.0))
        traffic_score = _estimate_route_traffic_score(route)

        normalized_routes.append(
            {
                "name": name,
                "distance_km": round(distance_km, 3),
                "eta_min": round(eta_min, 1),
                "traffic_score": traffic_score,
                "risk_score": round(_clamp(risk_score), 2),
                "recommendation": str(route.get("recommendation", "")),
                "path": route.get("path") or route.get("route_coordinates") or [],
            }
        )

    max_distance = max((route["distance_km"] for route in normalized_routes), default=1.0) or 1.0
    max_eta = max((route["eta_min"] for route in normalized_routes), default=1.0) or 1.0

    for route in normalized_routes:
        distance_component = route["distance_km"] / max_distance
        eta_component = route["eta_min"] / max_eta
        traffic_component = route["traffic_score"] / 10.0
        risk_component = route["risk_score"] / 10.0
        route["decision_score"] = round(
            100.0 * (
                0.30 * distance_component
                + 0.25 * eta_component
                + 0.25 * traffic_component
                + 0.20 * risk_component
            ),
            2,
        )

    ranked_routes = sorted(
        normalized_routes,
        key=lambda route: (
            route["decision_score"],
            route["risk_score"],
            route["traffic_score"],
            route["eta_min"],
            route["distance_km"],
        ),
    )

    best_route = ranked_routes[0]
    runner_up = ranked_routes[1]

    explanation = _route_decision_reason(best_route, runner_up)

    if best_route["risk_score"] <= runner_up["risk_score"] and best_route["traffic_score"] <= runner_up["traffic_score"]:
        recommendation = f"Choose {best_route['name'].replace('_', ' ').title()} for the best balance of safety and congestion."
    elif best_route["risk_score"] < runner_up["risk_score"]:
        recommendation = f"Choose {best_route['name'].replace('_', ' ').title()} if safety is the main priority."
    else:
        recommendation = f"Choose {best_route['name'].replace('_', ' ').title()} to minimize total travel cost."

    return {
        "best_route": best_route,
        "ranked_routes": ranked_routes,
        "explanation": explanation,
        "recommendation": recommendation,
        "criteria": {
            "distance": 0.30,
            "eta": 0.25,
            "traffic": 0.25,
            "risk": 0.20,
        },
    }


def _build_explanation(risk_level: str, zone: str, traffic: float, accident: float) -> str:
    if risk_level == "High":
        return (
            f"High traffic detected in {zone}, with elevated accident probability "
            f"({accident:.1f}/10)."
        )
    if risk_level == "Medium":
        return (
            f"Moderate congestion in {zone}; traffic density is {traffic:.1f}/10 "
            f"with manageable accident probability."
        )
    return (
        f"Low congestion in {zone}; traffic and accident indicators are currently stable."
    )


def _build_recommendation(risk_level: str, emergency_type: str) -> str:
    emergency = (emergency_type or "medical").strip().lower()

    if risk_level == "High":
        if emergency in {"fire", "earthquake", "landslide", "flood"}:
            return "High traffic detected in central zone, alternate route recommended with emergency corridor priority."
        return "High traffic detected in central zone, alternate route recommended."
    if risk_level == "Medium":
        return "Use current route with caution and monitor live traffic updates for safer diversions."
    return "Route conditions are favorable; continue with standard emergency dispatch protocol."


def evaluate_emergency_risk(
    *,
    location: Optional[str] = None,
    route_coordinates: Optional[List[List[float]]] = None,
    emergency_type: str = "medical",
) -> Dict[str, Any]:
    """Advanced risk model for either a location or a route.

    Formula:
    risk_score = 0.6 * traffic_density + 0.4 * accident_probability
    """
    has_location = bool(location and location.strip())
    has_route = bool(route_coordinates)

    if not has_location and not has_route:
        raise ValueError("Provide either location or route_coordinates for risk evaluation.")

    if has_route:
        traffic, accident_rate, zone = _simulate_route_signals(route_coordinates or [])
        context = "route"
    else:
        traffic, accident_rate = _simulate_signals(str(location))
        zone = _zone_from_coordinates(28.61, 77.21)
        context = "location"

    risk_score = round((0.6 * traffic) + (0.4 * accident_rate), 2)
    risk_level = _risk_category(risk_score)

    return {
        "input_type": context,
        "location": location if has_location else None,
        "traffic_density": round(traffic, 2),
        "accident_probability": round(accident_rate, 2),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "explanation": _build_explanation(risk_level, zone, traffic, accident_rate),
        "recommendation": _build_recommendation(risk_level, emergency_type),
        "zone": zone,
    }


def build_route_risk_insights(edge_risk_scores: Iterable[float], emergency_type: str) -> Dict[str, str]:
    """Create a human-readable explanation and recommendation for a route."""
    scores = [min(max(score, 0.0), 1.0) for score in edge_risk_scores]
    if not scores:
        return {
            "risk_score": "0.0",
            "explanation": "No route segments available for analysis.",
            "recommendation": "Retry route calculation with valid coordinates.",
            "risk_band": "low",
        }

    # Convert normalized segment risk into 0-10 traffic/accident-like signals.
    traffic_density = min(max((sum(scores) / len(scores)) * 10.0, 0.0), 10.0)
    accident_probability = min(max(max(scores) * 10.0, 0.0), 10.0)
    route_risk_score = round((0.6 * traffic_density) + (0.4 * accident_probability), 2)
    band = _band_from_level(_risk_category(route_risk_score))

    highest_risk = max(scores)
    segment_index = scores.index(highest_risk) + 1

    level = _risk_category(route_risk_score)
    explanation = _build_explanation(level, f"route segment {segment_index}", traffic_density, accident_probability)
    recommendation = _build_recommendation(level, emergency_type)

    if emergency_type.strip().lower() in {"fire", "earthquake", "landslide"} and band != "low":
        recommendation = "Use the safest available route and prioritize emergency clearance."

    return {
        "risk_score": str(route_risk_score),
        "explanation": explanation,
        "recommendation": recommendation,
        "risk_band": band,
    }


def _simulate_signals(location: str) -> Tuple[float, float]:
    """Return traffic and accident signals on a 0-10 scale."""
    key = location.strip().lower()
    if key in SIMULATED_LOCATION_DATA:
        data = SIMULATED_LOCATION_DATA[key]
        return data["traffic_density"], data["accident_probability"]

    # Deterministic random fallback for unknown locations.
    seeded_random = random.Random(key)
    traffic = round(seeded_random.uniform(2.0, 9.5), 2)
    accident_rate = round(seeded_random.uniform(1.0, 8.5), 2)
    return traffic, accident_rate


def _risk_category(score: float) -> str:
    if score < 4.0:
        return "Low"
    return "Medium" if score < 7.0 else "High"


def get_risk_score(location: str) -> Dict[str, float]:
    """
    Calculate location risk using weighted traffic and accident signals.

    Formula:
    risk_score = (0.6 * traffic_density) + (0.4 * accident_probability)
    """
    if not location or not location.strip():
        raise ValueError("location must be a non-empty string")

    evaluation = evaluate_emergency_risk(location=location)

    return {
        "location": location,
        "traffic_density": evaluation["traffic_density"],
        "accident_probability": evaluation["accident_probability"],
        "risk_score": evaluation["risk_score"],
        "category": evaluation["risk_level"],
        "explanation": evaluation["explanation"],
        "recommendation": evaluation["recommendation"],
    }
