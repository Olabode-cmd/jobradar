# JobRadar: PRD and Dev Plan

**Version 2** — October 2026. Open-source, local-first job aggregator. One monorepo: Python backend, TypeScript UI. v1 was a private tool for one user; v2 generalises it for public release — many independent local instances, no shared infrastructure. Anyone clones the repo, runs `./install.sh`, answers a short onboarding, and gets a personal job radar tailored to exactly what they fill in.

## 1. Summary

JobRadar pulls fresh job postings from public ATS feeds, remote job boards and community-maintained sources, filters them against your profile, removes duplicates, extracts the apply link and any contact email, and shows the result in a local dashboard. You triage; you apply yourself. It never submits an application.

It runs on your machine. One command (`./install.sh`) sets everything up; another (`./start.sh`) runs the app. There is no VPS, no cloud database and no login screen, because nothing is exposed beyond localhost. All personal state is one SQLite file plus one gitignored config file.

The point is to replace hours spent googling. Success means you open the dashboard, see only new, relevant, eligible postings, and click through to apply.

## 2. Goals and non-goals

**Goals**

- Clone → `./install.sh` → `./start.sh` → first fetch within minutes, no code edits, no required API keys.
- One config file (`jobradar.config.json`) defines what the search looks for. The CLI, backend and dashboard all read and validate it.
- Nothing is fetched until the user saves a job title. The onboarding wizard is the gate: it writes the config, offers the first fetch, and only then is the network touched.
- Show only postings you have not triaged, ranked by fit.
- Scrape the widest practical set of job boards with Scrapling — including Wellfound and Indeed as opt-in Tier C sources — and normalize everything into one pipeline.
- Relocation-aware mode: on-site jobs pass only when the employer offers to pay for the move. Country-based boards (Indeed, Wellfound, Relocate.me, Japan Dev) activate per target country set in the profile.
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

- **Developers** clone the repo, run `./install.sh` and are done.
- **Non-technical users** follow the README; a future prebuilt executable (Phase 7) removes the terminal entirely. Setup must survive someone who has never used a terminal beyond copy-paste.

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
| Source drivers, source definitions, presets, seed company lists, role templates, phrase bank, country catalog | **Repo** (Python code + JSON data files) | Crowd-maintained; a fix ships to everyone via `git pull` |
| Profile, enabled/disabled sources, tracked companies, custom sources, misc preferences | **`jobradar.config.json`** (gitignored) | Personal, portable, shareable |
| API keys (`API_KEY`, optional LLM overrides) | **`.env`** (gitignored, auto-created) | Keys never go near version control |
| Jobs, statuses, notes, run history, per-source/company health | **SQLite** file | Disposable, rebuildable state |

The dashboard edits the config file directly, so the GUI and hand-editing never diverge. The database holds no settings and no profiles — drop the file and nothing about your search is lost.

## 5. Sources

Tiers decide defaults and politeness:

- **Tier A: official or intentionally public feeds** (JSON, RSS, XML). On by default. Cheap, stable, safe.
- **Tier B: HTML pages scraped with selectors.** On by default where scraping is plainly tolerated. Gentle rate limits.
- **Tier C: hostile or bot-protected sources.** Off by default, opt-in with a warning in the UI. Need a real browser (`patchright install chromium`).

Endpoint patterns are what we know at time of writing; providers change them without notice. Two mitigations: every source gets a saved sample response as a test fixture, and source definitions live in the repo — a broken source is usually fixed by one PR.

**Hard rule: no bundled source may require an API key.**

### 5.1 ATS providers (Tier A)

Keyed by a company slug or board ID; you add companies to track.

Greenhouse, Lever, Ashby, Workable, Recruitee, SmartRecruiters, Teamtailor, Personio, BambooHR, Breezy (public JSON/RSS/XML feeds, no keys). Workday (per-tenant POST endpoint, fragile — Tier B).

### 5.2 Remote job boards (Tier A, on by default)

RemoteOK, Remotive, We Work Remotely, Himalayas, Arbeitnow (standard feed), Arbeitnow (visa-sponsorship filter), Jobicy, Working Nomads, HN "Who is hiring" (Algolia API, text-blob parsing).

### 5.3 Relocation boards

On by default. Only activated when the profile has matching target countries.

| Source | Coverage | Tier |
|---|---|---|
| **Relocate.me** | NL, JP, UK, DE, ES, PT, CY (filtered by profile) | B |
| **Japan Dev** | JP only — skipped unless JP is a target country | B |

All jobs from these boards carry an `offers_relocation` flag so the relocation rule does not have to reparse the description.

### 5.4 Country-based search sources (Tier C, off by default)

Require `openToRelocation: true` or an explicit country list in the profile. Use a stealth browser; expect occasional breakage.

- **Indeed** — one search per target country, using the profile's job title and a "relocation" suffix when the user is open to relocating. Country hosts and location strings are read from `backend/app/data/countries.json`.
- **Wellfound** — one listing page per (role-slug, country) pair. The role slug is derived from the profile title with seniority words stripped. Country-to-slug mapping comes from the same catalog.

Adding a country to both sources is one line in `countries.json`.

### 5.5 Tier B, on by default

Remote Rocketship, Remote.co, JustRemote, NoDesk, Dynamite Jobs, Arc.dev, Welcome to the Jungle, Y Combinator Work at a Startup.

### 5.6 Regional presets (addable)

Nigerian and Kenyan boards, off by default: Jobberman, MyJobMag, Hot Nigerian Jobs, NgCareers, BrighterMonday, Fuzu. Anything else goes through the Custom Source builder.

## 6. Functional requirements

### 6.1 Fetching and normalization

- Every source driver returns the same normalized record: source, external ID, title, company, canonical URL, apply URL, posted date, first seen date, location text, remote flag, remote region restrictions, employment type, salary text (raw, if given), description (text and HTML), tags, contact emails found, `offers_relocation` flag.
- Fetching runs through Scrapling: `Fetcher` (TLS-impersonated HTTP) for plain HTML and APIs, `StealthyFetcher` (real Chromium via Patchright) for Tier C pages.
- Missing posted dates fall back to first seen date.
- Sources run in parallel with a per-source concurrency cap, timeout, retry with backoff.
- A failed source never fails the run. It records the error and moves on.

### 6.2 Deduplication

- Primary: canonical URL with tracking parameters stripped.
- Secondary: hash of `company_key` (normalized company) + normalized title. Location is deliberately excluded.
- Duplicates keep every source link; best apply link first, decided by a data file mapping ATS providers to hostname patterns.

### 6.3 Profile and the config file

Nothing is fetched until the profile has a non-empty `role`. This is enforced at every entry point: CLI `fetch`, CLI `doctor`, the dashboard Run button, and the source Test button all refuse with a human-readable message if `role` is blank.

`jobradar.config.json` (validated at startup; errors are human-readable):

```json
{
  "profile": {
    "role": "",
    "includeKeywords": [],
    "excludeKeywords": [],
    "rejectedPhrases": [],
    "remoteOnly": true,
    "openToRelocation": false,
    "targetCountries": [],
    "blockedRegions": [],
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

- The example config ships with `role: ""`. Setup copies it but does not fill in a title — that is the user's job.
- `openToRelocation: true` enables the relocation rule and adds a "relocation" suffix to Indeed searches.
- `targetCountries` is a list of ISO-3166-1 alpha-2 codes (`["DE", "NL", "CA", "JP"]`). Country-driven sources (Relocate.me, Japan Dev, Indeed, Wellfound) only run for the countries they cover; they are silently skipped if no matching countries are configured, rather than appearing as failures.
- Onboarding writes all fields. Role templates (software engineer, designer, marketing, data analyst) prefill role and keywords.
- Blocked regions expand through a repo phrase bank into rejected phrases.
- Rules run first; they set eligibility: eligible / restricted / unclear. **Filter-then-store:** only `eligible` jobs are written to the database.

### 6.4 Eligibility and scoring

**Rule order (first match wins):**

1. Blocked company (`blockedCompanies`).
2. Rejected phrase or blocked region phrase in the full text.
3. Exclude keyword in the title.
4. Remote / relocation check (see below).
5. Posting age (`maxAgeDays`).
6. Minimum salary (if the listing shows a maximum below `minSalary`).
7. Keyword match (include keywords).

**Remote / relocation check:**

- If `openToRelocation` is true:
  - Remote jobs pass unconditionally.
  - On-site jobs pass only if the posting offers relocation (relocation support, package, allowance, reimbursement — matched with a phrase bank covering English, German, Dutch, French and Japanese; negated phrases like "we cannot support relocation" are excluded).
  - On-site jobs that do not offer relocation are restricted with reason "on-site without relocation support".
- If `openToRelocation` is false and `remoteOnly` is true: non-remote jobs are restricted.
- If both are false: no location restriction.

**Scoring bonuses:** keyword title match (+3), keyword body match (+1.5), seniority match (+1.5), seniority mismatch (−1.5), remote (+1), relocation offered when `openToRelocation` is on (+1.5), apply link (+0.5), ATS link (+0.5), recency (up to +5).

**Optional LLM pass:** provider-agnostic (`API_KEY`). Reads job descriptions only. Capped at 50 per run.

### 6.5 Contact and apply info

- Extract mailto links and email addresses from descriptions.
- Detect apply method: ATS link, email, or external form.
- Everything on the card is copyable.

### 6.6 Triage workflow

- Statuses: New, Saved, Applied, Interviewing, Rejected, Ignored. "New" is a status, not a time window.
- Keyboard driven: `J`/`K` move, `O` opens, `S`/`A`/`I` triage. Ignored jobs never reappear.
- Reposts: a duplicate arriving with a posted date more than 30 days newer re-opens as New with a "reposted" tag.

### 6.7 Company tracker and discovery

- Companies page lists tracked ATS boards: name, provider, slug, last checked, open roles, last error.
- Add by URL (detect provider and slug), bulk import, seed list in the repo.
- Boards that fail repeatedly are flagged, not silently dropped.

### 6.8 Runs and scheduling

- Manual run from CLI or dashboard.
- **Profile gate:** every run entry point calls `require_profile` before acquiring the run lock or touching the network.
- **Single-flight lock:** an active run is recorded in the DB meta table with a heartbeat; a second run refuses until it finishes or goes stale (`--force` to override).
- Optional OS scheduling calls the same CLI. Run history: per-source counts and duration.

### 6.9 Notifications (optional, off by default)

- Desktop notification after a scheduled run if new eligible jobs exist.
- Telegram or Discord webhook for phone alerts.
- Daily digest export to Markdown.

### 6.10 Export and backup

- Export jobs and applications as CSV or Markdown.
- Backup = copy the one SQLite file plus `jobradar.config.json`.

## 7. Dashboard

Local web app served by the FastAPI backend in production; Vite dev server with an `/api` proxy during development. **Binds 127.0.0.1 only.**

**Design:** flat, no shadows. One accent color, Manrope as the single typeface, Hugeicons. Dark and light themes.

**Pages:**

- **Onboarding** (first run, before any fetch): role/keywords → remote preference + relocation + target countries → blocked regions → seniority. Saves the config, offers the first fetch. Under two minutes. The home redirect sends the user here until a `role` is saved.
- **Inbox** — rows with title, company, source badges, posted age, score, apply method; detail panel with score reasons, emails, source links; filter bar; bulk actions.
- **Sources** — tier, type, enabled toggle, last run status, error, per-source settings, Test button.
- **Companies** — tracked ATS boards with add-by-URL, enable toggle, health, open-roles count.
- **Custom Source builder** — name, start URL, item selector, field selectors, live preview.
- **Runs** — history with per-source breakdown, run-now button.
- **Settings** — AI key, LLM overrides, export/backup.

## 8. Architecture

**Stack:** Python backend, TypeScript UI, one monorepo.

- **Backend:** Python ≥3.11. FastAPI + Uvicorn, Scrapling (`scrapling[fetchers]`) as the scraping engine, Patchright for Tier C browser pages, SQLite via stdlib `sqlite3` (WAL), `python-dotenv`, Typer for the CLI.
- **Web:** Vite + React + Tailwind CSS v4, Manrope, Hugeicons, `@thraggs/godspeed` for all dashboard → API calls.

### 8.1 Monorepo layout

```
jobradar/
  install.sh            # one-time setup: venv + packages + backend init + dashboard build
  start.sh              # dev/prod: API + dashboard together
  prd.md, README.md, LICENSE, .gitignore
  jobradar.config.example.json
  backend/
    requirements.txt
    app/
      config/           # jobradar.config.json + .env loading and validation
      db/               # SQLite lifecycle, repositories
      domain/           # eligibility, relocation detection, scoring, salary, dates, keys, text
      pipeline/         # normalize, dedupe, filter, score, ingest, run lock, doctor
      sources/
        drivers/
          ats/          # Greenhouse, Lever, Ashby, Workable, …
          json_board.py # RemoteOK, Remotive, Himalayas, Jobicy, Arbeitnow, …
          rss.py        # We Work Remotely
          hackernews.py
          selector.py   # generic CSS-selector driver (Relocate.me, Japan Dev, custom sources)
          indeed.py     # Tier C — stealth browser, per-country, role from profile
          wellfound.py  # Tier C — stealth browser, per-country, role slug from profile
          common.py     # collect_pages: tolerates partial page failures
        models.py       # FetchContext (carries role, countries, max_age_days, open_to_relocation)
        registry.py     # enable/disable logic, country-relevance filter
      net/
        http.py         # Scrapling Fetcher wrapper
        browser.py      # StealthySession wrapper with pause between pages
      data/
        presets.json    # all source definitions
        countries.json  # country code → host/location for each country-driven source
        phrase_bank.json # blocked region phrases + relocation offer/negation phrases
        ats_hosts.json
        seed_companies.json
      llm/              # provider-agnostic LLM pass
      api/              # FastAPI routes, schemas, error handling
      services/         # business logic called by routes
  web/                  # Vite + React dashboard
```

### 8.2 Source drivers

The `FetchContext` carries everything a driver needs from the user's profile without depending on the config object directly: `role`, `countries`, `max_age_days`, `open_to_relocation`, `contact`, `tracked_companies`.

Country-driven sources (`countryKey` in the preset) are automatically skipped by `select_sources` when no matching country is configured, so they never show as failures on runs where they are simply not relevant.

### 8.3 Pipeline

1. Load config; call `require_profile` — refuse if `role` is blank.
2. Resolve enabled sources; apply country-relevance filter.
3. Acquire the run lock.
4. Fetch in parallel via Scrapling (per-source limits, timeouts, backoff).
5. Normalize to one schema.
6. Dedupe in-batch and against the DB (URL, then hash).
7. Evaluate eligibility (rules including relocation check) and score; store only `eligible` jobs.
8. Optional capped LLM pass.
9. Record the run; release the lock.

### 8.4 Data model

- **jobs:** id, canonical_url, dedupe_hash, company_key, company_id, company, title, location_text, remote_status, region_restrictions (JSON), posted_at, first_seen_at, apply_url, apply_method, emails (JSON), salary_text, description, score, score_reasons (JSON), llm_result (JSON), eligibility, status, status_changed_at, reposted, low_confidence, notes, applied_at.
- **job_sources:** job_id, source_id, url, seen_at.
- **source_state:** source_id, last_run_at, last_status, last_error, last_success_at.
- **company_state:** company_key, last_checked_at, last_error, open_roles.
- **runs / run_sources:** run history with per-source counts.
- **meta:** key, value (schema version, run lock).

### 8.5 Security (localhost is not automatically safe)

- Bind 127.0.0.1 explicitly, never 0.0.0.0.
- Middleware: reject requests whose Host header isn't localhost/127.0.0.1 (kills DNS rebinding); reject non-GET requests whose Origin isn't localhost (kills drive-by CSRF). No CORS headers.
- No auth — justified only because the above holds.
- The one key lives in `.env`, never in the config file or DB.

### 8.6 Database lifecycle

- Auto-created and auto-migrated on first run. `sqlite3` ships with Python.
- Default location: OS app-data (`%LOCALAPPDATA%\jobradar`, `~/Library/Application Support/jobradar`, `~/.local/share/jobradar`). Overridable with `JOBRADAR_DB`.
- Detect OneDrive/Dropbox-synced paths; warn and refuse unless overridden.
- WAL + `busy_timeout` on every connection.

### 8.7 Politeness and safety

- Honest UA: `JobRadar/<version> (+<contact>)`.
- Per-host rate limits via Scrapling's AutoThrottle; robots rules respected on Tier B.
- Tier C warns in the UI. No logged-in scraping, ever.
- StealthySession pauses 2–4 seconds between pages.
- The LLM pass sends job descriptions only.

## 9. Non-functional requirements

- **Speed:** a full fetch across ~150 tracked companies and all default boards finishes in under 3 minutes on a normal connection. Tier C sources add time proportional to countries × roles × pages.
- **Reliability:** one broken source never blocks others; broken sources are visible within one run.
- **Maintainability:** adding a new ATS is one driver + one fixture, under an hour. Adding a country is one line in `countries.json`. Scrapling adaptive selectors absorb many board redesigns.
- **Privacy:** all local, no telemetry, no data sent anywhere except to job boards during fetch.
- **Portability:** Windows first-class, macOS, Linux. Python 3.11+ and Bun.
- **Cost:** zero required spend. The optional LLM pass is capped per run.
- **Supportability:** `doctor --report` emits a paste-able, personal-data-free markdown summary for GitHub issues.

## 10. Dev plan

Estimates assume focused solo work. Each phase ends with something usable.

- **Phase 0 ✓** — Scaffold: monorepo, web app, FastAPI skeleton, config loader, SQLite lifecycle, example config, README, license, lint + format.
- **Phase 1 ✓** — Pipeline: normalize, dedupe, filter-then-store, run lock, ATS drivers (Greenhouse, Lever, Ashby, Workable), rule-based filtering, CLI (`fetch`, `doctor`).
- **Phase 2 ✓** — Tier A boards: RemoteOK, Remotive, WWR, Himalayas, Arbeitnow, Jobicy, Working Nomads, HN. Additional ATS: Recruitee, SmartRecruiters, Teamtailor, Personio, BambooHR, Breezy.
- **Phase 3 ✓** — Dashboard MVP: API routes, Inbox, Sources, Companies, onboarding wizard, run-now with live progress.
- **Phase 4 ✓** — Relocation mode: `openToRelocation` flag, `targetCountries` field, relocation phrase bank (EN/DE/NL/FR/JP), eligibility rule, scoring bonus, profile gate at every entry point. New sources: Arbeitnow visa-sponsorship feed, Relocate.me, Japan Dev (Tier B); Indeed, Wellfound (Tier C browser-based, per-country from catalog).
- **Phase 5 (next)** — Custom source builder (preview list) + Tier B presets. `./install.sh` one-command setup.
- **Phase 6** — Remaining ATS drivers (add-by-URL + bulk import), seed lists, dead-board flagging.
- **Phase 7** — Weighted scoring + explanations, LLM pass + caching, profile editor with live counts.
- **Phase 8** — Notifications, exports, schedule helper, prebuilt executables for non-technical users, optional GitHub Action.

## 11. Testing

- **Source fixtures:** a saved real response per source. Normalization is tested against it.
- **Pipeline tests:** dedupe across sources, profile gate, relocation rule edge cases (negated phrases, multi-language), country-relevance filtering, filter rules on edge phrases.
- **Relocation phrase tests:** each supported language, negated forms, employer-offer vs. candidate-demand distinction.
- **doctor:** hits each enabled source once and reports pass or fail; `--report` for issues. Refuses before the network if no profile is set.
- **Manual checks:** after each phase, compare tool output against what you find by hand on two or three boards.
- **Contribution loop:** "source X broke" issue + `doctor --report` → fixture PR.

## 12. Risks and how to handle them

- **Providers change endpoints.** Fixtures, health checks, Scrapling adaptive selectors, and community PRs catch this early.
- **Scraped boards break often.** Keep selector configs in `presets.json`; a broken selector is a one-line PR.
- **Blocking and rate limits.** Scrapling's stealth fetchers + AutoThrottle, polite defaults. Tier C being opt-in limits the number of users hitting each site simultaneously.
- **Wellfound / Indeed are the hardest targets.** Heavy Cloudflare protection. They are Tier C, logged-out only, and the UI warns that they break. They are a convenience layer, not the backbone — the free boards are the backbone.
- **Japan Dev / Relocate.me selectors.** These are in `presets.json`, so a selector change is a community PR with no user action needed beyond `git pull`.
- **Terms of service.** Prefer official feeds. Document each source's stance. Tier C stays opt-in. Arbeitnow's API is used with attribution per their terms.
- **Stale or fake postings.** Show posted age; `maxAgeDays` caps staleness.
- **False restrictions.** Always show the reason and the source snippet.
- **Profile-not-set confusion.** The profile gate produces a human-readable message at every entry point; the home redirect sends new users to onboarding.
- **SQLite on synced folders.** App-data default + OneDrive/Dropbox detection + `JOBRADAR_DB` override.
- **Scope creep.** Auto-apply, resume tailoring and multi-user support are out.

## 13. Decisions log

- Python backend (FastAPI + Scrapling + Patchright), TypeScript UI (Vite/React/Tailwind v4), one monorepo.
- SQLite via stdlib — the lowest-friction DB is the one with nothing to install.
- No bundled source requires an API key.
- Scrapling is the scraping engine for every HTTP/HTML source; Patchright for browser-required Tier C.
- Filter-then-store: eligibility is computed at ingest and only eligible jobs are stored.
- "New" is a status, not a time window.
- Dedupe hash excludes location; company normalization via `company_key`.
- Source definitions live in the repo (community-maintained); personal state lives in the config + SQLite.
- DB auto-creates in OS app-data; WAL + busy_timeout; OneDrive/Dropbox guard.
- Localhost hardening: 127.0.0.1 bind, Host + Origin checks, no CORS, no auth.
- Run lock (heartbeat + `--force`) prevents overlapping fetches.
- **Profile gate:** every crawl entry point calls `require_profile` before any lock or network work. The example config ships with `role: ""` so a fresh clone cannot silently fetch against a default identity.
- **Relocation rule:** on-site jobs pass only when the posting contains a non-negated relocation offer phrase. Phrase bank covers EN/DE/NL/FR/JP. Negation window is 50 chars before + 30 chars after the phrase.
- **Country catalog (`countries.json`):** the single place that maps a country code to how each country-driven source spells it. Adding a country is one line; removing it removes it from all sources.
- **`FetchContext` carries role and countries:** drivers never read the config file directly. This makes them testable without a config.
- **Role slug for Wellfound** is derived from the profile title at runtime (seniority words stripped, hyphenated). No role list is shipped.
- Glassdoor: Tier C, not yet implemented, heavily Cloudflare-protected.
- Wellfound, Indeed: Tier C, logged-out only, expect breakage.

## 14. Open questions

- License: MIT by default unless vetoed.
- Repo URL (goes into the UA string and docs).
- Regional presets shipping in v1 beyond Nigeria/Kenya.
- Prebuilt executables in Phase 8 or deferred.
- Japan Dev selector stability — the site uses a Nuxt/Algolia combo. If server-side rendering breaks, the selector driver will need swapping for a browser-based one.
- Relocate.me country coverage — the site only lists a subset of countries on the main filter. Monitor whether more countries appear.
