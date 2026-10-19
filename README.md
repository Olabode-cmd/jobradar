# JobRadar

Watches job boards for you. You say what you're looking for once — role, keywords, target countries, remote or open to relocating — and JobRadar pulls fresh postings, removes duplicates, filters out anything that doesn't fit your profile, and shows you a clean list one click from applying.

Everything runs on your own computer. No account, no cloud, no tracking.

---

## What you need

Install these before running anything else.

**Python 3.11 or newer**
Download from [python.org/downloads](https://www.python.org/downloads/). On Windows, tick *Add Python to PATH* during install. Verify:

```bash
python --version   # should print 3.11 or higher
```

**Bun** (JavaScript runtime and package manager)
Install in one command:

```bash
# Mac / Linux
curl -fsSL https://bun.sh/install | bash

# Windows (PowerShell)
powershell -c "irm bun.sh/install.ps1 | iex"
```

Or see [bun.sh](https://bun.sh) for other options. Verify:

```bash
bun --version
```

**Git** — from [git-scm.com](https://git-scm.com/downloads) if not already present.

---

## Install

```bash
git clone <repo-url> jobradar
cd jobradar
./install.sh
```

That one script does everything:

1. Creates a Python virtual environment in `backend/.venv`
2. Installs all Python packages
3. Creates `.env` and initialises the database
4. Installs dashboard Node packages and builds the static UI

It is safe to run again if anything goes wrong.

> **Windows (Git Bash or WSL):** `./install.sh` works as-is. In a plain Command Prompt, run each step manually — see the script's comments.

---

## Start

```bash
./start.sh
```

Open **<http://127.0.0.1:8000>** in your browser. The first screen walks you through four questions:

1. What job title and keywords are you looking for?
2. Remote only, or open to relocating? Which countries?
3. Which regions can you *not* work in?
4. How senior are you?

After that, click **Fetch jobs now** and your inbox fills up.

Nothing is fetched until you save a job title. The setup is zero-required-keys: the AI scoring pass is optional.

---

## Daily use

**Inbox** — every untriaged job, best fit first. Press `J`/`K` to move between cards, `O` to open the apply page, and `S`/`A`/`I` to save, mark applied, or ignore. Ignored jobs never come back.

**Runs** — trigger a fetch from here, or watch it while it runs. Each source shows how many jobs came in, how many were new, and how many were dropped by your filters.

**Sources** — flip boards on or off. The **Test** button fetches a source once and shows the first few results without saving anything. Tier C boards (Indeed, Wellfound) are off by default because they block bots — you can turn them on, but expect occasional breakage.

**Companies** — paste a company's careers page link to track it directly. Works with Greenhouse, Lever, Ashby, Workable, Recruitee, SmartRecruiters, Teamtailor, Personio, BambooHR and Breezy.

**Profile** — change what you're looking for any time. Edits `jobradar.config.json`.

**Settings** — optional AI key, exports, and **Clear jobs** to start over (your profile and sources are kept).

---

## Relocation

Set `openToRelocation: true` on the Profile page (or in onboarding). JobRadar then:

- Keeps on-site jobs **only** when the posting mentions relocation support, a relocation package, or an equivalent in German, Dutch, French or Japanese.
- Skips on-site jobs that say the candidate must be "willing to relocate" — that is a demand, not an offer.
- Adds a relocation bonus to the score of jobs that do offer it.

Add target countries (two-letter codes: `DE`, `NL`, `CA`, `JP`, …) to activate country-based boards:

| Source | Countries | Tier |
|---|---|---|
| Arbeitnow (visa sponsorship) | Germany and Europe | A |
| Relocate.me | NL, JP, UK, DE, ES, PT, CY | B |
| Japan Dev | JP | B |
| Indeed | Any country in the catalog | C (off by default) |
| Wellfound | Any country in the catalog | C (off by default) |

Countries are set per person and stored in your gitignored `jobradar.config.json`. Adding a country you don't see: open `backend/app/data/countries.json` and add a line for the country code.

---

## Optional: AI scoring

JobRadar works fully without a key. Add one and each fetch runs an AI model over the strongest matches to explain its score and double-check eligibility. It reads job descriptions only, never your CV, and checks at most 50 jobs per run.

Open **Settings**, paste your key, and press **Test connection**.

Keys starting with `sk-ant-` are treated as Anthropic. Anything else is treated as OpenAI-compatible — works with OpenRouter, Groq, Ollama and local models too. Set **Base URL** and **Model** in Settings (or `LLM_BASE_URL` / `LLM_MODEL` in `.env`) for non-default providers.

---

## Optional: Indeed and Wellfound (Tier C)

These need a real browser installed:

```bash
# Windows
backend/.venv/Scripts/python.exe -m patchright install chromium

# Mac / Linux
backend/.venv/bin/python -m patchright install chromium
```

Then enable them on the **Sources** page. Expect occasional blocked pages — these sites actively detect bots. When blocked, the source logs an error and the rest of your fetch continues normally.

---

## Where things live

| What | Where |
|---|---|
| Your search settings | `jobradar.config.json` (gitignored — edit in the dashboard or by hand) |
| Your optional AI key | `.env` (gitignored) |
| Your jobs and history | one SQLite file, path shown in **Settings → Your data** |

To back up: copy the config file and the database file.

---

## Command line

```bash
cd backend

python -m app.cli fetch           # fetch now
python -m app.cli fetch --dry-run # count what would be stored, without storing
python -m app.cli doctor          # check every source, print pass/fail
python -m app.cli doctor --report # paste-able summary for bug reports
python -m app.cli sources         # list sources and their status
python -m app.cli reset-db        # delete all jobs and history (--yes skips prompt, --keep-triaged keeps acted-on jobs)
```

---

## Developing

```bash
./start.sh              # API + dashboard dev server together (Ctrl+C stops both)
bun run dev:api         # API on :8000 with auto-reload
bun run dev:web         # dashboard on :5173, proxies /api to :8000
bun run test:api        # backend unit tests
cd web && bun run typecheck
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) for how the code is organised and how to add a source. The full product spec is in [prd.md](./prd.md).

Bugs, broken sources and ideas are welcome as issues. Please include the output of `python -m app.cli doctor --report` with bug reports.
