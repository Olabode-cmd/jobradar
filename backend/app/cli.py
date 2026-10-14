"""JobRadar CLI: fetch, doctor, sources, serve.

Run from the backend directory: `python -m app.cli fetch`
"""

from __future__ import annotations

from typing import Annotated

import typer

from .config import load_config
from .pipeline import doctor as run_doctor
from .pipeline import run_fetch
from .sources.drivers import resolve_enabled_sources

app = typer.Typer(help="JobRadar — local-first job aggregator.", no_args_is_help=True)


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
    for source_id, stats in result["per_source"].items():
        if stats.get("error"):
            typer.echo(f"  {source_id:<20} error: {stats['error']}")
        else:
            typer.echo(f"  {source_id:<20} fetched {stats['fetched']:>4}  new {stats['new']:>4}  known {stats['known']:>4}  {stats['duration_ms']}ms")
            total_new += stats["new"]
    typer.echo(f"{len(result['per_source'])} sources, {total_new} new jobs")


@app.command()
def doctor(report: Annotated[bool, typer.Option("--report", help="Emit a paste-able markdown report")] = False) -> None:
    """Check every enabled source and report pass/fail."""
    config = load_config()
    rows = run_doctor(config)
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
    """List enabled and disabled sources."""
    config = load_config()
    for source in resolve_enabled_sources(config):
        typer.echo(f"  {source['id']:<20} {source.get('tier', 'B'):<3} {source.get('type', 'selector'):<10} enabled")
    for disabled in config.sources.get("disabled", []):
        typer.echo(f"  {disabled:<20} disabled")


@app.command()
def serve(port: Annotated[int, typer.Option("--port", help="Port to bind")] = 8000) -> None:
    """Start the local API server (binds 127.0.0.1)."""
    import uvicorn

    typer.echo(f"JobRadar API on http://127.0.0.1:{port} — Ctrl+C to stop")
    uvicorn.run("app.main:app", host="127.0.0.1", port=port)


if __name__ == "__main__":
    app()