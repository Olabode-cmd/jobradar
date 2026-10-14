# Contributing

Thanks for helping. The most useful contribution is fixing a broken source: providers change their feeds without notice, and one pull request fixes it for everyone.

## Layout

```
backend/app/
  api/         HTTP only: routes, request schemas, error mapping, security middleware
  services/    use-cases the routes call; they raise AppErrors, never HTTP errors
  pipeline/    fetch -> normalize -> dedupe -> judge -> store, run lock, progress, AI pass
  sources/     the only code that fetches job data: registry, dispatcher, one driver per kind
  llm/         provider-agnostic client contract, adapters, assessment prompt
  domain/      pure functions (normalizing, eligibility, scoring, contact, salary, export)
  db/          connection, schema, one repository module per concern
  config/      jobradar.config.json and .env handling
  net/         the one HTTP client (Scrapling)
  data/        JSON anyone can edit: presets, phrase bank, ATS hosts, seed companies
web/src/
  api/         one module per resource, all calls go through godspeed
  lib/         pure helpers and runtime parsers for API data
  hooks/       shared hooks
  components/  ui primitives and layout
  features/    one folder per page
```

Dependencies point one way: `api -> services -> pipeline / sources / llm / db / config -> domain`. `domain` imports nothing from the rest of the app, so it stays easy to test.

## Running the tests

```bash
cd backend
python -m unittest discover -s tests -t .
```

Tests mirror the package layout. They never touch the network or your real config: HTTP is faked, the database is a temp file, and config paths are patched.

## Adding a source

1. **A JSON board.** Add an entry to `backend/app/data/presets.json` with `"type": "api"` and a `startUrl`. If its field names are new, add the spelling to the lists in `sources/drivers/json_board.py`. Set `"allRemote": true` for remote-only boards.
2. **A company ATS.** Add a parser to `sources/drivers/ats/parsers.py` and register it in `providers.py` with its feed URL. Add its hostname to `ats/detect.py` so "add by URL" recognises it.
3. **Add a test with a fixture** shaped like a real response (see `tests/sources/test_ats_parsers.py`). A provider change should show up as a failing test, not as silently empty results.
4. Check it against the live feed: `python -m app.cli doctor`.

Sources that need an API key are out of scope. Anything that needs a login is out of scope. Sources that fight bots are Tier C: off by default, logged-out only.

## Style

- Python: type hints, small functions, early returns, no comments that restate the code.
- TypeScript: strict mode, kebab-case file names, no `any`. Data from the API is parsed at the boundary in `web/src/lib/parse-*.ts`.
- Treat anything from a feed, a posting or a request as untrusted text.
- Run `bun run format` before committing.

## Reporting a broken source

Open an issue with the output of `python -m app.cli doctor --report`. It contains no personal data.
