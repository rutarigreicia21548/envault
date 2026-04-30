"""Command-line interface for envault."""

import sys
from pathlib import Path

import click

from envault.storage import LocalStorage
from envault.vault import Vault


def _make_vault(project: str, env_path: Path, password: str) -> Vault:
    storage = LocalStorage()
    return Vault(storage=storage, project=project, env_path=env_path, password=password)


@click.group()
def cli():
    """envault — lightweight secrets manager."""


@cli.command()
@click.argument("project")
@click.option("--env", default=".env", show_default=True, help="Path to .env file.")
@click.password_option(help="Encryption password.")
def push(project: str, env: str, password: str):
    """Encrypt and push .env file to remote storage."""
    env_path = Path(env)
    if not env_path.exists():
        click.echo(f"Error: {env_path} not found.", err=True)
        sys.exit(1)
    vault = _make_vault(project, env_path, password)
    vault.push()
    click.echo(f"Pushed secrets for project '{project}'.")


@cli.command()
@click.argument("project")
@click.option("--env", default=".env", show_default=True, help="Path to .env file.")
@click.option("--password", prompt=True, hide_input=True, help="Encryption password.")
def pull(project: str, env: str, password: str):
    """Pull and decrypt .env file from remote storage."""
    env_path = Path(env)
    vault = _make_vault(project, env_path, password)
    try:
        vault.pull()
    except KeyError:
        click.echo(f"Error: project '{project}' not found in storage.", err=True)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    click.echo(f"Pulled secrets for project '{project}' into {env_path}.")


@cli.command()
@click.argument("project")
@click.option("--env", default=".env", show_default=True, help="Path to .env file.")
@click.option("--password", prompt=True, hide_input=True, help="Encryption password.")
def status(project: str, env: str, password: str):
    """Show sync status between local .env and stored secrets."""
    env_path = Path(env)
    vault = _make_vault(project, env_path, password)
    state = vault.status()
    click.echo(f"Status for project '{project}': {state}")


if __name__ == "__main__":
    cli()
