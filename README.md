# JobRadar

JobRadar watches job boards for you. You tell it what you're looking for once and then it pulls fresh jobs from the boards you pick, removes duplicates, filters out the ones that don't fit, and shows you a clean list, one click from applying.

Everything runs on your own computer.

## What you need

- **Python 3.10 or newer** — download it from [python.org](https://www.python.org/downloads/)
- **Git** — from [git-scm.com](https://git-scm.com/downloads)

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
cd ..
```

**3. Tell JobRadar what you're looking for**

```bash
cp jobradar.config.example.json jobradar.config.json
```

Open `jobradar.config.json` in any text editor. Put your job title and skills in `includeKeywords` (e.g. `"React"`, `"Python"`), and anything you never want to see in `rejectedPhrases` (e.g. `"US only"`, `"security clearance"`). Save the file.

**4. Fetch jobs**

```bash
cd backend
python -m app.cli fetch
```

You'll see a summary — how many jobs each board returned, and how many are new for you. Check the whole database anytime:

```bash
python -m app.cli doctor
```

## Want a live API instead?

```bash
cd backend
python -m uvicorn app.main:app --port 8000
```

Open http://127.0.0.1:8000/api/health in your browser — it reports the database and config status. The dashboard will use this same API.

## Edit your profile in the browser

With the API running (above), start the dashboard in a second terminal:

```bash
cd web
bun install
bun run dev
```

Open http://127.0.0.1:5173. The Profile page edits `jobradar.config.json` directly.

## Where things live

- Your search settings: `jobradar.config.json` (this is the only file you ever edit)
- The optional LLM key for smarter scoring: `.env` (see `.env.example`)
- All your jobs and history: one local database file, created automatically

## Details

Full plan and roadmap: [prd.md](./prd.md). Bugs, ideas, and "this board broke" reports are welcome as issues.