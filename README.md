# JobRadar

JobRadar watches job boards for you. You tell it what you're looking for once, and it pulls fresh jobs from the boards you pick, removes duplicates, filters out the ones that don't fit, and shows you a clean list, one click from applying. It never applies for you.

Everything runs on your own computer. There is no account, no cloud service and no tracking.

## What you need

- **Python 3.11 or newer** — from [python.org](https://www.python.org/downloads/)
- **Git** — from [git-scm.com](https://git-scm.com/downloads)
- **Bun** — from [bun.sh](https://bun.sh) (only to build the dashboard once)

## Get it running (about 5 minutes)

**1. Copy the project to your computer**

```bash
git clone <repo-url> jobradar
cd jobradar
```

**2. Install the backend**

```bash
cd backend
python -m venv .venv
```

Activate it:

- **Windows:** `.venv\Scripts\activate`
- **Mac / Linux:** `source .venv/bin/activate`

```bash
pip install -r requirements.txt
python -m app.cli setup
cd ..
```

`setup` creates the files JobRadar needs (`.env`, `jobradar.config.json` and the database). It is safe to run again.

**3. Build the dashboard**

```bash
cd web
bun install
bun run build
cd ..
```

**4. Start it**

```bash
cd backend
python -m app.cli serve
```

Open <http://127.0.0.1:8000>. The first time, JobRadar asks four short questions about the job you want, then offers to fetch your first jobs.

## Using it

- **Inbox** — jobs you haven't triaged, best fit first. Use `J` / `K` to move, `O` to open the apply page, and `S`, `A` or `I` to save, mark applied or ignore.
- **Runs** — fetch jobs now and see what each source returned.
- **Sources** — switch boards on or off, and press **Test** to see what a board returns without saving anything.
- **Companies** — paste a company's careers page link (Greenhouse, Lever, Ashby, Workable, Recruitee, SmartRecruiters, Teamtailor, Personio, BambooHR or Breezy) to check it on every run.
- **Profile** — change what you're looking for any time. It edits `jobradar.config.json`.
- **Settings** — optional AI key, and exports of your jobs.

### Command line

```bash
cd backend
python -m app.cli fetch        # fetch now (add --dry-run to count without saving)
python -m app.cli doctor       # check every source (add --report for a shareable summary)
python -m app.cli sources      # list sources and whether they're on
```

## Optional: smarter scoring with an AI key

JobRadar works fully without a key. If you add one, an AI model double-checks the best matches after each fetch and explains its score. It reads job descriptions only, never your CV, and checks at most 50 jobs per run.

Open **Settings**, paste the key, save, then press **Test connection**. Or put it in `.env` yourself:

```
API_KEY=your-key-here
```

Keys starting with `sk-ant-` are treated as Anthropic; anything else as OpenAI-compatible. For OpenRouter, Groq or a local model such as Ollama, also set **Base URL** and **Model** in Settings (or `LLM_BASE_URL` and `LLM_MODEL` in `.env`).

## Where things live

| What                  | Where                                                         |
| --------------------- | ------------------------------------------------------------- |
| Your search settings  | `jobradar.config.json` (edit it in the dashboard, or by hand) |
| Your optional AI key  | `.env`                                                        |
| Your jobs and history | one database file, shown in **Settings → Your data**          |

To back up, copy the config file and the database file.

## Working on it

```bash
bun run dev:api      # API with auto-reload on :8000
bun run dev:web      # dashboard dev server on :5173, proxies /api to :8000
bun run test:api     # backend tests
cd web && bun run typecheck
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) for how the code is organised and how to add a source. The full plan is in [prd.md](./prd.md). Bugs, ideas and "this board broke" reports are welcome as issues; please include the output of `python -m app.cli doctor --report`.
