"""JobRadar CLI: setup, fetch, doctor, sources, reset-db, serve.

Run from the backend directory: `python -m app.cli setup`
"""

from __future__ import annotations

from typing import Annotated

import typer

from .config import load_config
from .core.errors import ConflictError
from .db import default_db_path, open_db
from .pipeline import run_doctor, run_fetch
from .services.data_service import clear_data
from .services.setup_service import run_setup
from .sources import list_all_sources

app = typer.Typer(help="JobRadar — local-first job aggregator.", no_args_is_help=True)


@app.command()
def setup() -> None:
    """Create .env, the config file and the database if they are missing. Safe to re-run."""
    created = run_setup()
    for line in created:
        typer.echo(line)
    typer.echo("Setup complete." if created else "Already set up. Nothing to create.")


@app.command()
def fetch(
    sources: Annotated[list[str] | None, typer.Option("--source", help="Only these source IDs (repeatable)")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Fetch and report without storing")] = False,
    force: Annotated[bool, typer.Option("--force", help="Override an in-progress run")] = False,
) -> None:
    """Fetch all enabled sources and store new jobs."""
    config = load_config()
    for error in config.errors:
        typer.echo(f"warning: {error}", err=True)

    result = run_fetch(config, only=sources, dry_run=dry_run, force=force)

    if result["status"] == "blocked":
        typer.echo(f"blocked: {result['message']}", err=True)
        raise typer.Exit(1)

    typer.echo(f"run #{result['run_id']} — {result['started_at']}")
    if result.get("dry_run"):
        typer.echo("dry run: nothing stored")
    total_new = 0
    total_dropped = 0
    for source_id, stats in result["per_source"].items():
        if stats.get("error"):
            typer.echo(f"  {source_id:<20} error: {stats['error']}")
        else:
            typer.echo(
                f"  {source_id:<20} fetched {stats['fetched']:>4}  new {stats['new']:>4}  "
                f"known {stats['known']:>4}  dropped {stats['dropped']:>4}  {stats['duration_ms']}ms"
            )
            total_new += stats["new"]
            total_dropped += stats["dropped"]
    typer.echo(
        f"{len(result['per_source'])} sources, {total_new} new jobs, "
        f"{total_dropped} dropped by your profile"
    )


@app.command()
def doctor(report: Annotated[bool, typer.Option("--report", help="Emit a paste-able markdown report")] = False) -> None:
    """Check every enabled source and report pass/fail."""
    rows = run_doctor(load_config())
    if report:
        typer.echo("```markdown")
        typer.echo("## JobRadar doctor report")
        typer.echo("")
        for row in rows:
            state = "ok" if row["ok"] else "FAIL"
            typer.echo(f"- **{row['id']}** ({row['tier']}/{row['kind']}): {state} — {row['records']} records, {row['duration_ms']}ms")
            if row["error"]:
                typer.echo(f"  - error: {row['error']}")
        typer.echo("```")
        return
    for row in rows:
        state = "ok" if row["ok"] else "FAIL"
        typer.echo(f"  {row['id']:<20} {state:<5} {row['records']:>4} records  {row['duration_ms']}ms")
        if row["error"]:
            typer.echo(f"    {row['error']}")


@app.command()
def sources() -> None:
    """List every source and whether it is enabled."""
    for source in list_all_sources(load_config()):
        state = "enabled" if source["enabled"] else "disabled"
        typer.echo(f"  {source['id']:<20} {source.get('tier', 'B'):<3} {source.get('type', 'selector'):<10} {state}")


@app.command(name="reset-db")
def reset_db(
    yes: Annotated[bool, typer.Option("--yes", help="Skip the confirmation prompt")] = False,
    keep_triaged: Annotated[
        bool, typer.Option("--keep-triaged", help="Keep jobs you have saved, applied to, rejected or ignored")
    ] = False,
) -> None:
    """Delete stored jobs and run history. Your config file and API key are not touched."""
    scope = "every untriaged job" if keep_triaged else "every job"
    if not yes and not typer.confirm(f"Delete {scope} and all run history from {default_db_path()}?"):
        typer.echo("Cancelled. Nothing deleted.")
        raise typer.Exit(1)
    conn = open_db()
    try:
        result = clear_data(conn, keep_triaged)
    except ConflictError as exc:
        typer.echo(f"blocked: {exc}", err=True)
        raise typer.Exit(1)
    finally:
        conn.close()
    typer.echo(f"Deleted {result['deleted']} jobs, kept {result['kept']}.")


@app.command()
def serve(port: Annotated[int, typer.Option("--port", help="Port to bind")] = 8000) -> None:
    """Start the local API server (binds 127.0.0.1)."""
    import uvicorn

    typer.echo(f"JobRadar API on http://127.0.0.1:{port} — Ctrl+C to stop")
    uvicorn.run("app.main:app", host="127.0.0.1", port=port)


if __name__ == "__main__":
    app()
