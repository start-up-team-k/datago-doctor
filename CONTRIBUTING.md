# Contributing

- Issues are welcome, especially: a failing response body (remove your service key first) that datago-doctor could not explain or explained wrongly.
- Result-code meanings live in one place: `datago_doctor/codes.py`. If you can cite an official document or a captured response for a code, change its `confidence` to `confirmed` and set `source`.
- Add a fixture under `tests/fixtures/`, list it in `tests/fixtures/manifest.json` and `SOURCES.md` (public issue URL, official doc URL, or live-call date + masked URL; otherwise name it `synthetic_*`).
- Keep it dependency-free (standard library only). Run `python -m pytest` before opening a PR.
- Never put a real service key in a fixture, issue or PR.
