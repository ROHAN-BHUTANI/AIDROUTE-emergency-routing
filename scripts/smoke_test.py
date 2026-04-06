"""Minimal backend smoke test for local development."""

from __future__ import annotations

import json
from urllib.request import urlopen


def main() -> None:
    with urlopen("http://127.0.0.1:5000/health", timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
