# Development Notes

## Windows backend run
Use the Python launcher that is already configured on this machine:

```bat
py -m venv .venv
call .venv\Scripts\activate.bat
py -m pip install -r requirements.txt
py app.py
```

## Runtime behavior
- If `data/roads.csv` is unavailable, the backend automatically falls back to the built-in demo graph.
- The `/health` endpoint should return a success response when the server is running.
- The repo keeps the root focused on the runtime entry points: `app.py`, `routing.py`, `data/`, `models/`, `requirements.txt`, and `README.md`.
