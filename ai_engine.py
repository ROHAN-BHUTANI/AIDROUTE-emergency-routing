"""Gemini AI helpers for disaster analysis and route explanation.

This module reads `GEMINI_API_KEY` from the environment or from a local `.env`
file in the project root. It uses the Google Gemini REST API directly so the
backend does not need an additional SDK dependency.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent
DOTENV_PATH = BASE_DIR / ".env"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"


def _load_dotenv() -> None:
    """Load simple KEY=VALUE pairs from .env into the environment."""
    if not DOTENV_PATH.exists():
        return

    for raw_line in DOTENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        if line.startswith("export "):
            line = line[len("export ") :].strip()

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()


def _get_api_key() -> str:
    """Return the configured Gemini API key if available."""
    return (
        os.getenv("GEMINI_API_KEY", "").strip()
        or os.getenv("GOOGLE_GEMINI_API_KEY", "").strip()
    )


def _post_json(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    request_obj = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urlopen(request_obj, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def _extract_candidate_text(payload: Dict[str, Any]) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        return ""

    content = (candidates[0].get("content") or {})
    parts = content.get("parts") or []
    text_parts: List[str] = []
    for part in parts:
        text = part.get("text")
        if text:
            text_parts.append(str(text))
    return "".join(text_parts).strip()


def _parse_json_text(text: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    if not text:
        return fallback

    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    return fallback


def _severity_from_text(text: str) -> str:
    lowered = (text or "").lower()
    high_signals = ["earthquake", "landslide", "explosion", "mass casualty", "collapse", "wildfire", "chemical"]
    medium_signals = ["flood", "accident", "collision", "fire", "blocked", "injury", "smoke"]

    if any(signal in lowered for signal in high_signals):
        return "high"
    if any(signal in lowered for signal in medium_signals):
        return "medium"
    return "low"


def _action_plan_from_severity(severity: str) -> List[Dict[str, Any]]:
    if severity == "high":
        return [
            {"resource": "ambulances", "units": 3},
            {"resource": "rescue_teams", "units": 2},
            {"resource": "medical_staff", "units": 6},
            {"resource": "traffic_control", "units": 2},
        ]
    if severity == "medium":
        return [
            {"resource": "ambulances", "units": 2},
            {"resource": "medical_staff", "units": 4},
            {"resource": "traffic_control", "units": 1},
        ]
    return [
        {"resource": "ambulances", "units": 1},
        {"resource": "medical_staff", "units": 2},
    ]


def _route_level_from_risk(risk_score: Any) -> str:
    try:
        score = float(risk_score)
    except (TypeError, ValueError):
        score = 0.0
    if score >= 7:
        return "high"
    if score >= 4:
        return "medium"
    return "low"


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = api_key or _get_api_key()
        self.model = model or os.getenv("GEMINI_MODEL", GEMINI_MODEL)

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _generate_json(self, prompt: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return fallback

        payload = {
            "systemInstruction": {
                "parts": [
                    {
                        "text": (
                            "You are an emergency response assistant. "
                            "Return only valid JSON. Do not wrap output in markdown."
                        )
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.9,
                "maxOutputTokens": 256,
                "responseMimeType": "application/json",
            },
        }

        url = GEMINI_API_BASE.format(model=self.model, api_key=self.api_key)
        try:
            response_payload = _post_json(url, payload)
        except (URLError, json.JSONDecodeError, OSError, ValueError):
            return fallback

        text = _extract_candidate_text(response_payload)
        parsed = _parse_json_text(text, fallback)
        parsed.setdefault("provider", "gemini")
        return parsed

    def analyze_disaster(self, text_input: str) -> Dict[str, Any]:
        severity_hint = _severity_from_text(text_input)
        fallback = {
            "severity": severity_hint,
            "summary": text_input.strip()[:180] or "No incident details provided.",
            "indicators": [],
            "confidence": 0.55 if text_input.strip() else 0.25,
            "provider": "fallback",
        }

        prompt = (
            "Analyze the incident description and return JSON with keys: "
            "severity (low, medium, or high), summary (one sentence), indicators (array of strings), "
            "confidence (0 to 1). Incident text: "
            f"{text_input}"
        )
        result = self._generate_json(prompt, fallback)
        severity = str(result.get("severity", severity_hint)).strip().lower()
        if severity not in {"low", "medium", "high"}:
            severity = severity_hint
        result["severity"] = severity
        result.setdefault("summary", fallback["summary"])
        result.setdefault("indicators", [])
        result.setdefault("confidence", fallback["confidence"])
        return result

    def recommend_action(self, disaster_data: Dict[str, Any]) -> Dict[str, Any]:
        severity = str(disaster_data.get("severity", "low")).strip().lower()
        if severity not in {"low", "medium", "high"}:
            severity = "low"

        fallback = {
            "severity": severity,
            "priority": "monitor" if severity == "low" else "deploy" if severity == "medium" else "escalate",
            "resource_allocation": _action_plan_from_severity(severity),
            "summary": (
                "Monitor conditions and keep standard medical support ready."
                if severity == "low"
                else "Deploy additional medical support and traffic control."
                if severity == "medium"
                else "Escalate with full rescue, ambulances, and field medical support."
            ),
            "provider": "fallback",
        }

        prompt = (
            "Given this disaster JSON, return strict JSON with keys: severity, priority, resource_allocation, summary. "
            "resource_allocation must be an array of objects with resource and units. Disaster JSON: "
            f"{json.dumps(disaster_data, ensure_ascii=False)}"
        )
        result = self._generate_json(prompt, fallback)
        result["severity"] = severity
        result.setdefault("resource_allocation", _action_plan_from_severity(severity))
        result.setdefault("priority", fallback["priority"])
        result.setdefault("summary", fallback["summary"])
        return result

    def explain_route(self, route: Dict[str, Any], risk: Dict[str, Any]) -> Dict[str, Any]:
        route_name = str(route.get("name") or route.get("route_name") or "selected_route").strip()
        risk_level = _route_level_from_risk(risk.get("risk_score", route.get("risk_score", 0.0)))
        fallback = {
            "route_name": route_name,
            "risk_level": risk_level,
            "explanation": (
                f"{route_name.title()} is selected because it balances travel time and risk for the current incident."
            ),
            "reasons": [
                "Lower combined decision cost",
                "Acceptable risk profile",
                "Better fit for the incident response context",
            ],
            "provider": "fallback",
        }

        prompt = (
            "Explain why this emergency route was chosen. Return strict JSON with keys: route_name, risk_level, "
            "explanation, reasons (array of strings). Route JSON: "
            f"{json.dumps(route, ensure_ascii=False)}. Risk JSON: {json.dumps(risk, ensure_ascii=False)}"
        )
        result = self._generate_json(prompt, fallback)
        result["route_name"] = route_name
        result["risk_level"] = risk_level
        result.setdefault("explanation", fallback["explanation"])
        result.setdefault("reasons", fallback["reasons"])
        return result


_CLIENT = GeminiClient()


def analyze_disaster(text_input: str) -> Dict[str, Any]:
    """Analyze incident text and return a structured severity summary."""
    return _CLIENT.analyze_disaster(text_input)


def recommend_action(disaster_data: Dict[str, Any]) -> Dict[str, Any]:
    """Return structured resource allocation guidance from disaster analysis data."""
    return _CLIENT.recommend_action(disaster_data)


def explain_route(route: Dict[str, Any], risk: Dict[str, Any]) -> Dict[str, Any]:
    """Explain why a particular route is selected given route and risk context."""
    return _CLIENT.explain_route(route, risk)
