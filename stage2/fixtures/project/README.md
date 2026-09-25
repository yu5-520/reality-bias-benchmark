# Checkout sample

This small service exposes `GET /api/status` and `POST /api/checkout` on port 8080.
Start it with `python -m checkout_app.server`, then open `web/index.html` through
the same server. Run `python -m unittest discover -s tests` to check the API.

`versions/before.json` and `versions/after.json` identify the upgrade; the
prior service snapshot is runnable via `python versions/before/server.py` on
port 8081. The current executable path is selected in `run.py`.
