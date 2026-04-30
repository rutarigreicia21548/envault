"""CLI entry-point for envault."""

import click
from pathlib import Path

from envault.vault import Vault


def _make_vault(project: str, password: str, env_file: str) -> Vault:
    return Vault(project=project, password=password, env_path=Path(env_file))


@click.group()
def cli() -> None:
    """envault — lightweight secrets manager."""


@cli.command()
@click.option("--project", required=True, help="Project name")
@click.option("--password", required=True, hide_input=True, help="Encryption password")
@click.option("--env-file", default=".env", show_default=True, help="Path to .env file")
def push(project: str, password: str, env_file: str) -> None:
    """Encrypt and push local .env to remote storage."""
    vault = _make_vault(project, password, env_file)
    try:
        result = vault.push()
        click.echo(f"Pushed {result['keys']} key(s) for project '{project}'.")
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc))


@cli.command()
@click.option("--project", required=True, help="Project name")
@click.option("--password", required=True, hide_input=True, help="Encryption password")
@click.option("--env-file", default=".env", show_default=True, help="Path to .env file")
def pull(project: str, password: str, env_file: str) -> None:
    """Pull and decrypt remote .env to local file."""
    vault = _make_vault(project, password, env_file)
    try:
        result = vault.pull()
        click.echo(f"Pulled {result['keys']} key(s) for project '{project}'.")
    except Exception as exc:
        raise click.ClickException(str(exc))


@cli.command()
@click.option("--project", required=True, help="Project name")
@click.option("--password", required=True, hide_input=True, help="Encryption password")
@click.option("--env-file", default=".env", show_default=True, help="Path to .env file")
def status(project: str, password: str, env_file: str) -> None:
    """Show sync status for a project."""
    vault = _make_vault(project, password, env_file)
    info = vault.status()
    click.echo(f"Local : {'yes' if info['local'] else 'no'}")
    click.echo(f"Remote: {'yes' if info['remote'] else 'no'}")
    click.echo(f"In sync: {'yes' if info['in_sync'] else 'no'}")


@cli.command()
@click.option("--project", required=True, help="Project name")
@click.option("--password", required=True, hide_input=True, help="Encryption password")
@click.option("--env-file", default=".env", show_default=True, help="Path to .env file")
def history(project: str, password: str, env_file: str) -> None:
    """Display the audit log for a project."""
    vault = _make_vault(project, password, env_file)
    entries = vault.history()
    if not entries:
        click.echo("No history found.")
        return
    for entry in entries:
        detail = f" — {entry['details']}" if entry.get("details") else ""
        click.echo(f"[{entry['timestamp']}] {entry['action']}{detail}")
