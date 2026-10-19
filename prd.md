# JobRadar: PRD and Dev Plan

**Version 2** — October 2026. Open-source, local-first job aggregator. One monorepo: Python backend, TypeScript UI. v1 was a private tool for Bode; v2 generalizes it for public release — many independent local instances, no shared infrastructure. Anyone clones the repo, runs setup, answers a short onboarding, and gets a personal job radar.

## 1. Summary

JobRadar pulls fresh job postings from public ATS feeds, remote job boards and community-maintained sources, filters them against your profile, removes duplicates, extracts the apply link and any contact email, and shows the result in a local dashboard. You triage, you apply yourself. It never submits an application.

It runs on your machine. One command starts the dashboard and API; another runs a fetch. There is no VPS, no cloud database and no login screen, because nothing is exposed beyond localhost. All personal state is one SQLite file plus one gitignored config file.

The point is to replace hours spent googling. Success means you open the dashboard, see only new, relevant, eligible postings, and click through to apply.

## 2. Goals and non-goals

**Goals**

- Clone → `bun install` + one Python setup command → first fetch within minutes, no code edits, no required API keys.
- One config file (`jobradar.config.json`) defines what the search looks for. The CLI, backend and dashboard all read and validate it.
- Show only postings you have not triaged, ranked by fit.
- Scrape the widest practical set of job boards with Scrapling — including Glassdoor and Wellfound as opt-in sources — and normalize everything into one pipeline.
- Configure everything (sources, tracked companies, filters) from the dashboard, with the config file as the underlying artifact you can also hand-edit, back up, or share.
- Community-maintained source definitions: when a provider changes something, one pull request fixes it for every user.
- Tell you honestly when a source is broken, rate-limited or returning nothing, and make bug reports one command (`doctor --report`).

**Non-goals**

- Auto-applying, auto-filling forms or sending email on your behalf.
- Any hosted component: no accounts, no sync service, no telemetry, no shared database.
- Scraping with a logged-in account. Ever. Tier C sources are always logged-out and opt-in.
- Resume tailoring or cover letter generation (possible later).
- Bundled sources that require an API key. The only key a user may ever need is their LLM key (`API_KEY`), and even that is optional.

## 3. Users and usage

Two audiences:

- **Developers** clone the repo and run a few commands.
- **Non-technical users** follow the README and the onboarding wizard; a future prebuilt executable (Phase 7) removes the terminal entirely. Setup must survive someone who has never used a terminal beyond copy-paste.

One person uses each instance. Setup target: clone to first fetch in under five minutes, zero required keys.

Typical session:

1. Run a fetch (from the CLI or the dashboard's Run button).
2. Open the Inbox. See the untriaged postings, best fit first.
3. Press a key to open the apply page, mark it Applied, or Ignore it.
4. Occasionally add a company, tweak the config, or switch a source on or off.

## 4. What lives where

One source of truth per kind of information:

| Kind of information | Lives in | Why |
|---|---|---|
| Adapters/source drivers, source definitions, presets, seed company lists, role templates, phrase bank | **Repo** (Python code + JSON data files) | Crowd-maintained; a fix ships to everyone via `git pull` |
| Profile, enabled/disabled sources, tracked companies, custom sources, misc preferences | **`jobradar.config.json`** (gitignored) | Personal, portable, shareable |
| API keys (one: `API_KEY`, plus optional LLM overrides) | **`.env`** (gitignored, auto-created) | Keys never go near version control |
| Jobs, statuses, notes, run history, per-source/company health | **SQLite** file | Disposable, rebuildable state |

The dashboard edits the config file directly, so the GUI and hand-editing never diverge. The database holds no settings and no profiles — drop the file and nothing about your search is lost.

## 5. Sources

Tiers decide defaults and politeness:

- **Tier A: official or intentionally public feeds** (JSON, RSS, XML). On by default. Cheap, stable, safe.
- **Tier B: HTML pages scraped with selectors.** On by default where scraping is plainly tolerated. Gentle rate limits.
- **Tier C: hostile or login-gated sources.** Off by default, opt-in, with a warning in the UI.

Endpoint patterns are what we know at time of writing; providers change them without notice. Two mitigations, both stronger because the project is open source: every source gets a saved sample response as a test fixture, and source definitions live in the repo — a broken source is usually fixed by one PR instead of every user editing a local database.

**Hard rule: no bundled source may require an API key.** Keyed boards are dropped or moved to the scraped pool.

### 5.1 ATS providers (Tier A)

Keyed by a company slug or board ID; you add companies to track.

Greenhouse, Lever, Ashby, Workable, Recruitee, SmartRecruiters, Teamtailor, Personio, BambooHR, Breezy, JazzHR (public JSON/RSS/XML feeds, no keys). Workday (per-tenant JSON search endpoint, POST-based, fragile — ships as Tier B).

### 5.2 Foreign job boards

Tier A, on by default: RemoteOK, Remotive, We Work Remotely, Himalayas, Arbeitnow, Jobicy, Working Nomads, HN "Who is hiring" (Algolia API, text-blob parsing), Remote4Africa (classified by observed behavior during Phase 2).

Tier B, on by default with conservative limits: Remote Rocketship, Remote.co, JustRemote, NoDesk, Dynamite Jobs, Arc.dev, Welcome to the Jungle, Y Combinator Work at a Startup.

Tier C, off by default, opt-in with a warning:

- **Glassdoor** — stealth-fetched listing pages. Heavily protected (Cloudflare, CAPTCHA, ToS-hostile); expect breakage, apply happens on Glassdoor.
- **Wellfound** — stealth-fetched listing pages. Strong bot protection and login-gated apply flows; expect breakage and apply links that open the Wellfound apply flow.
- **Indeed** — same treatment.

### 5.3 Regional presets (addable)

Nigerian and Kenyan boards, off by default, one click in the presets drawer: Jobberman, MyJobMag, Hot Nigerian Jobs, NgCareers, BrighterMonday, Fuzu. Anything else goes through the Custom Source builder.

## 6. Functional requirements

### 6.1 Fetching and normalization

- Every source driver returns the same normalized record: source, external ID, title, company, canonical URL, apply URL, posted date, first seen date, location text, remote flag, remote region restrictions, employment type, salary text (raw, if given), description (text and HTML), tags, contact emails found.
- Fetching runs through Scrapling: `Fetcher` (TLS-impersonated HTTP) for plain HTML, `DynamicFetcher`/`StealthyFetcher` for JS-rendered and defended pages, spiders with AutoThrottle and robots.txt support for multi-page runs.
- Missing posted dates fall back to first seen date, and the UI marks them as estimated.
- Sources run in parallel with a per-source concurrency cap, timeout, retry with backoff, and conditional requests (ETag/Last-Modified) when supported.
- A failed source never fails the run. It records the error and moves on.

### 6.2 Deduplication

- Primary: canonical URL with tracking parameters stripped.
- Secondary: hash of `company_key` (normalized company) + normalized title. Location is deliberately excluded — boards describe the same job's location differently, and including it guarantees missed merges. Rare false merges are acceptable: the two postings are near-identical and share one card.
- Normalization: lowercase, strip punctuation and legal suffixes (inc, llc, ltd, gmbh, corp, co); titles lowercased with parenthetical qualifiers and emoji stripped.
- Duplicates keep every source link; best apply link first, decided by a data file mapping ATS providers to hostname patterns.

### 6.3 Profiles and the config file

`jobradar.config.json` (validated at startup against a schema; errors are human-readable, e.g. `jobradar.config.json: "maxAgeDays" must be a number`):

```json
{
  "profile": {
    "role": "Frontend engineer",
    "includeKeywords": [],
    "excludeKeywords": [],
    "rejectedPhrases": [],
    "remoteOnly": true,
    "blockedRegions": ["US"],
    "timezonesOverlap": null,
    "minSalary": null,
    "maxAgeDays": 14
  },
  "sources": { "disabled": [] },
  "companies": { "tracked": [] },
  "customSources": [],
  "preferences": { "userAgentContact": "" }
}
```

- Onboarding writes it. Role templates (software engineer, designer, marketing, data analyst) prefill it.
- Blocked regions expand through a repo phrase bank into rejected phrases ("must reside in", "authorized to work in the US", "US citizens", "security clearance") — the personalization that makes results actually relevant, generalized.
- Rules run first, free; they set eligibility: eligible / restricted / unclear. **Filter-then-store:** only `eligible` jobs are written to the database; restricted and unclear ones are dropped at ingest. Each run reports how many were dropped per source and the top reasons, and `fetch --dry-run` shows the same without storing, so false negatives can still be audited. A profile change applies to the next fetch; use Settings → Clear jobs (or `reset-db`) to re-fetch under the new profile.
- Keyword matching is whole-word (`\blead\b`, not "misleading"; `react` also matches `ReactJS`). Exclude keywords check the title. A job passes the include rule when a keyword is in the title, or when at least two distinct keywords (or all, if fewer are listed) are in the description.

### 6.4 Eligibility and scoring

- Rule-based score: keyword weights, title match, seniority, recency, direct-company apply link.
- Optional LLM pass, driven by the single `API_KEY` in `.env`. Provider-agnostic: keys starting `sk-ant-` are treated as Anthropic; anything else as OpenAI-compatible (`LLM_PROVIDER`, `LLM_MODEL`, `LLM_BASE_URL` overrides for OpenRouter, Groq, Ollama, local models). Runs only on eligible + unclear jobs without a cached result, capped at 50 per run. Sends only job descriptions, never your CV.
- The dashboard always shows why a job scored the way it did, with the source snippet.

### 6.5 Contact and apply info

- Extract mailto links and email addresses from descriptions. Flag generic inboxes versus personal ones.
- Detect apply method: ATS link, email, or external form.
- Everything on the card is copyable.

### 6.6 Triage workflow

- Statuses: New, Saved, Applied, Interviewing, Rejected, Ignored. "New" is a status, not a time window — a posting stays New until triaged, so skipped days lose nothing.
- Keyboard driven. Ignored jobs never reappear; ignoring a company can write its normalized key to the config blocklist.
- Reposts: if a duplicate arrives with a posted date more than 30 days newer than the job's last status change, it re-opens as New with a "reposted" tag. Otherwise it stays put.

### 6.7 Company tracker and discovery

- A Companies page lists tracked ATS boards: company name, provider, slug, last checked, open roles, last error.
- Add by URL (detect provider and slug from the URL), bulk import, seed list shipped in the repo.
- Boards that fail repeatedly are flagged, not silently dropped.

### 6.8 Runs and scheduling

- Manual run from CLI or dashboard; flags: specific sources, dry run.
- **Single-flight lock:** an active run is recorded in the DB meta table with a heartbeat; a second run refuses until it finishes or goes stale, with `--force` to override.
- Optional OS scheduling calls the same CLI. Run history: per-source counts, duration.

### 6.9 Notifications (optional, off by default)

- Desktop notification after a scheduled run if new eligible jobs exist.
- Telegram or Discord webhook for phone alerts.
- Daily digest export to Markdown.

### 6.10 Export and backup

- Export jobs and applications as CSV or Markdown.
- Backup = copy the one SQLite file (plus the config).

## 7. Dashboard

Local web app served by the FastAPI backend in production; Vite dev server with a `/api` proxy during development. **Binds 127.0.0.1 only** — never 0.0.0.0.

**Design direction:** flat — no shadows, no eyebrow labels. One accent color (deep radar green), Manrope (variable, self-hosted via `@fontsource-variable/manrope`) as the single typeface — hierarchy from weight, size and spacing. Hugeicons (free core set via `@hugeicons/react` + `@hugeicons/core-free-icons`) as the only icon set. All dashboard → API requests go through `@thraggs/godspeed`. Dense list views. Dark and light themes (system preference, with a manual toggle later).

Pages:

- **Onboarding** (first run): four questions — role/keywords, remote-only?, regions you can't work in, seniority. Writes the config, offers the first fetch. Under two minutes.
- **Inbox** — rows (title, company, source badges, posted age, remote region, score, apply method), detail panel with score reasons/emails/source links, filter bar, bulk actions. Sorted by score once Phase 6 lands; by recency before that.
- **Sources** — table with tier, type, enabled toggle, last run status, error message, per-source settings, presets drawer, and a Test button that runs the source once and shows the first five parsed results without saving.
- **Companies** — tracked ATS boards with add-by-URL, bulk import, enable toggle, health, open-roles count.
- **Custom Source builder** — name, start URL with pagination pattern, item selector, field selectors, date parsing rules. Live preview shows the parsed records as a list. In-page selector highlighting is cut from v1. Headless browser mode optional, off by default.
- **Runs** — history with per-source breakdown, run-now with source checkboxes, schedule helper.
- **Settings** — the one key (`API_KEY`) plus LLM overrides, written to `.env` and never shown back in full; defaults; data export/backup.

## 8. Architecture

**Stack:** Python backend, TypeScript UI, one monorepo.

- **Backend:** Python ≥3.10. FastAPI + Uvicorn, Scrapling (`scrapling[fetchers]`) as the scraping engine, SQLite via the stdlib `sqlite3` (WAL), `python-dotenv` for `.env`, Typer for the CLI (Phase 1).
- **Web:** Vite + React + Tailwind CSS v4, Manrope, hugeicons, godspeed (`@thraggs/godspeed`) for all dashboard → API calls.
- **Why Python for the backend:** Scrapling's spider framework *is* the fetching and politeness layer — AutoThrottle, robots.txt obedience, blocked-request detection, per-domain throttling, pause/resume. Re-implementing that in another language would be ~2 days of work to get a worse result. Its adaptive selectors (`auto_save` / `adaptive=True`) also absorb the "selectors break" maintenance problem, and its dev-mode response caching matches the fixture-testing philosophy.

### 8.1 Monorepo layout

```
jobradar/
  prd.md, README.md, LICENSE, .gitignore, .env.example
  jobradar.config.example.json
  backend/           # FastAPI + Scrapling + sqlite3 + CLI
    requirements.txt
    app/
      main.py        # FastAPI app (health now; routes in Phase 3)
      config.py      # jobradar.config.json + .env loading
      db.py          # SQLite lifecycle: auto-create, migrations, WAL
      pipeline/      # Phase 1: normalize, dedupe, filter, score, runs
      sources/       # source drivers (Scrapling-based), presets as data
  web/               # Vite + React dashboard
```

### 8.2 Source drivers

Every source is a small Python driver or a config-driven generic scraper. The core contract (Phase 1):

```python
class SourceDriver:
    id: str                 # "greenhouse", "custom:jobberman"
    tier: "A" | "B" | "C"
    kind: "ats" | "board"
    def fetch(self, ctx: FetchContext) -> Iterable[RawJob]: ...
```

ATS drivers receive tracked companies; board drivers receive their settings; custom sources are one generic driver driven by stored selector config. Presets (source definitions, seed companies, phrase banks) are JSON data files in the repo so community fixes are PRs, not database edits.

### 8.3 Pipeline

1. Load config; resolve enabled sources and tracked companies.
2. Acquire the run lock.
3. Fetch in parallel via Scrapling (per-source limits, timeouts, backoff, conditional requests).
4. Normalize to one schema.
5. Dedupe in-batch and against the DB (URL, then hash).
6. Upsert jobs with eligibility from the active profile's rules; update source links.
7. Optional capped LLM pass.
8. Record the run; print/push the summary; release the lock.

### 8.4 Data model

- **jobs:** id, canonical_url, dedupe_hash, company_key, company_id (nullable — set by ATS drivers), company, title, location_text, remote_status, region_restrictions (JSON), posted_at, first_seen_at, apply_url, apply_method, emails (JSON), salary_text, description, score, score_reasons (JSON), llm_result (JSON), eligibility, status, status_changed_at, reposted, low_confidence, notes, applied_at.
- **job_sources:** job_id, source_id, url, seen_at.
- **source_state:** source_id, last_run_at, last_status, last_error, last_success_at.
- **company_state:** company_key, last_checked_at, last_error, open_roles.
- **runs / run_sources:** run history with per-source counts.
- **meta:** key, value (schema version, run lock).

### 8.5 Security (localhost is not automatically safe)

- Bind 127.0.0.1 explicitly, never 0.0.0.0.
- Middleware: reject requests whose Host header isn't localhost/127.0.0.1 (kills DNS rebinding); reject non-GET requests whose Origin isn't localhost (kills drive-by CSRF from visited web pages). No CORS headers.
- No auth — justified only because the above holds. Never expose LAN binding in v1.
- The one key lives in `.env`, never in the config file or DB; a startup check warns if a key-shaped value appears in the config.

### 8.6 Database lifecycle (setup friction lives here, not in the engine)

- Auto-created and auto-migrated on first run — the DB is never a user step. `sqlite3` ships with Python; there is nothing to install.
- Default location: OS app-data (`%LOCALAPPDATA%\jobradar`, `~/Library/Application Support/jobradar`, `~/.local/share/jobradar`) — not the cloned repo, so re-cloning keeps your history and synced-folder corruption is avoided. Overridable with `JOBRADAR_DB`.
- Detect OneDrive/Dropbox-synced paths; warn and refuse unless overridden.
- WAL + `busy_timeout` on every connection (CLI and server share the file).
- Backup = copy the file.

### 8.7 Politeness and safety

- Honest UA: `JobRadar/<version> (+<repo URL>)`, contact string configurable in the config file.
- Per-host rate limits and jitter via Scrapling's AutoThrottle; robots rules respected on Tier B by default with deliberate override.
- Conditional requests; skip unchanged boards.
- Tier C warns in the UI and is never enabled by presets. No logged-in scraping, ever — Glassdoor and Wellfound are always fetched logged-out, at your own risk, and the PRD + UI say so.
- Conservative limits matter because many users hit the same boards.
- The LLM pass sends job descriptions only.

## 9. Non-functional requirements

- **Speed:** a full fetch across ~150 tracked companies and all default boards finishes in under 3 minutes on a normal connection.
- **Reliability:** one broken source never blocks others; broken sources are visible within one run.
- **Maintainability:** adding a new ATS source is one small driver + one fixture, under an hour once done twice. Scrapling adaptive selectors absorb many board redesigns.
- **Privacy:** all local, no telemetry.
- **Portability:** Windows first-class (most users), macOS, Linux. Python 3.10+ and Bun; the Phase 0 smoke test runs on Windows.
- **Cost:** zero required spend. The optional LLM pass is capped per run.
- **Supportability:** README is the product for non-developers; `doctor --report` emits a paste-able, personal-data-free markdown summary for GitHub issues.

## 10. Dev plan

Estimates assume focused solo work. Each phase ends with something usable.

- **Phase 0 — Scaffold (in progress):** monorepo, web app with Manrope/hugeicons/godspeed wired and verified, FastAPI skeleton with `/api/health`, config loader, SQLite lifecycle, example config + `.env`, README, license, lint + format. Windows smoke test passes.
- **Phase 1 (2–3 days):** pipeline (normalize, dedupe, store-then-filter, run lock), config validation, the generic selector driver, the first ATS drivers (Greenhouse, Lever, Ashby, Workable), rule-based filtering, CLI (`fetch`, `doctor` incl. `--report`). **Done when:** `fetch` against 20 real companies prints new filtered jobs with apply links; a second run prints only new ones; everything is driven by `jobradar.config.json`.
- **Phase 2 (2 days):** Tier A board drivers (RemoteOK, Remotive, WWR, Himalayas, Arbeitnow, Jobicy, Working Nomads, HN with low-confidence handling, Remote4Africa probe).
- **Phase 3 (3–4 days):** dashboard MVP — API routes, Inbox, Sources, Companies, onboarding wizard, run-now with live progress.
- **Phase 4 (2 days):** remaining ATS drivers, add-by-URL + bulk import, seed lists, dead-board flagging.
- **Phase 5a (2 days):** custom source builder (preview list) + Tier B presets.
- **Phase 5b (1–2 days):** regional presets (probe first: Jobberman, MyJobMag, Hot Nigerian Jobs); browser installs only for sources that need them. Tier C opt-in presets (Glassdoor, Wellfound, Indeed) behind warnings.
- **Phase 6 (2 days):** weighted scoring + explanations, LLM pass + caching, profile editor with live counts.
- **Phase 7 (2 days):** notifications, exports, schedule helper, prebuilt executables for non-technical users (Python single-file bundle + static web build), optional GitHub Action.

**Total:** ≈ 17–20 focused days; daily value from the end of Phase 1, dashboard from Phase 3.

## 11. Testing

- **Source fixtures:** a saved real response per source. Normalization is tested against it, so provider changes show up as a failing test, not as silent empty results. Scrapling's dev-mode caching gives us this for scraped boards.
- **Pipeline tests:** dedupe across sources, status-based "new", first-run age cap, filter rules on edge phrases.
- **doctor:** hits each enabled source once and reports pass or fail; `--report` for issues.
- **Manual checks:** after each phase, compare tool output against what you find by hand on two or three boards.
- **Contribution loop:** "source X broke" issue + `doctor --report` → fixture PR.

## 12. Risks and how to handle them

- **Providers change endpoints.** Fixtures, health checks, Scrapling adaptive selectors, and community PRs catch this early.
- **Scraped boards break often.** Keep selector configs as data; make the preview tool good, so repairs are a UI edit.
- **Blocking and rate limits.** Scrapling's stealth fetchers + AutoThrottle, polite defaults, residential IPs, and Tier C being opt-in.
- **Glassdoor / Wellfound / Indeed are the hardest targets.** Heavy anti-bot protection, login walls, hostile ToS. They ship Tier C, logged-out only, and the UI warns that they break and are used at your own risk. They are stretch goals, not the backbone — the free boards are the backbone.
- **Terms of service.** Prefer official feeds. Document each source's stance in its settings. Tier C stays opt-in.
- **Stale or fake postings.** Show posted age, flag listings older than the profile max-age, let Ignore teach the company blocklist.
- **False restrictions.** The LLM pass can misread a posting. Always show the reason and the source snippet so you can overrule it in one click.
- **Open-source support burden.** README quality, `doctor --report`, role templates, and a CONTRIBUTING guide (added with Phase 1).
- **SQLite on synced folders.** App-data default + detection + `JOBRADAR_DB` override.
- **Scope creep.** Auto-apply, resume tailoring and multi-user support are out. Revisit only after real use.

## 13. Decisions log

- Python backend (FastAPI + Scrapling), TypeScript UI (Vite/React/Tailwind v4), one monorepo.
- SQLite via stdlib — the lowest-friction DB is the one with nothing to install.
- No bundled source requires an API key; the only key is `API_KEY` (provider-agnostic, optional).
- Scrapling is the scraping engine for every HTML/JS source; adaptive selectors + dev-mode fixtures absorb board redesigns.
- Filter-then-store (replaces store-then-filter): eligibility is computed at ingest and only eligible jobs are stored. Dropped jobs are counted with reasons in run stats.
- "New" is a status, not a time window.
- Dedupe hash excludes location; company normalization via `company_key`.
- Source definitions live in the repo (community-maintained); personal state lives in the config file + SQLite.
- DB auto-creates in OS app-data; WAL + busy_timeout; OneDrive/Dropbox guard.
- Localhost hardening: 127.0.0.1 bind, Host + Origin checks, no CORS, no auth.
- Run lock (heartbeat + `--force`) prevents overlapping fetches.
- Glassdoor, Wellfound, Indeed: Tier C, opt-in, logged-out only, expect breakage.

## 14. Open questions

- License: MIT by default unless vetoed.
- Repo URL (goes into the UA string and docs).
- Regional presets shipping in v1 beyond Nigeria/Kenya.
- Exact onboarding question wording.
- Prebuilt executables in Phase 7 or deferred.