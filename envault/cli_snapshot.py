"""CLI commands for snapshot management."""

from __future__ import annotations

import click

from envault.cli import _make_vault, cli
from envault.snapshot import (
    SnapshotError,
    create_snapshot,
    delete_snapshot,
    list_snapshots,
    load_snapshot,
)


@cli.group("snapshot")
def snapshot_group() -> None:
    """Manage point-in-time snapshots of vault secrets."""


@snapshot_group.command("create")
@click.option("--project", "-p", required=True, help="Project name.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.option("--label", default=None, help="Snapshot label (default: timestamp).")
def snapshot_create(project: str, password: str, label: str | None) -> None:
    """Create a snapshot of the current vault secrets."""
    vault = _make_vault(project, password)
    try:
        secrets = vault.pull(write_file=False)
    except Exception as exc:  # pragma: no cover
        raise click.ClickException(str(exc)) from exc

    snap = create_snapshot(vault.storage, project, secrets, label=label)
    click.echo(f"Snapshot '{snap.label}' created at {snap.created_at}.")


@snapshot_group.command("list")
@click.option("--project", "-p", required=True, help="Project name.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
def snapshot_list(project: str, password: str) -> None:
    """List all snapshots for a project."""
    vault = _make_vault(project, password)
    labels = list_snapshots(vault.storage)
    if not labels:
        click.echo("No snapshots found.")
        return
    for label in sorted(labels):
        click.echo(label)


@snapshot_group.command("restore")
@click.option("--project", "-p", required=True, help="Project name.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.argument("label")
def snapshot_restore(project: str, password: str, label: str) -> None:
    """Restore vault secrets from a snapshot."""
    vault = _make_vault(project, password)
    try:
        snap = load_snapshot(vault.storage, label)
    except SnapshotError as exc:
        raise click.ClickException(str(exc)) from exc

    vault.push(snap.secrets)
    click.echo(f"Vault restored from snapshot '{label}'.")


@snapshot_group.command("delete")
@click.option("--project", "-p", required=True, help="Project name.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.argument("label")
def snapshot_delete(project: str, password: str, label: str) -> None:
    """Delete a snapshot."""
    vault = _make_vault(project, password)
    try:
        delete_snapshot(vault.storage, label)
    except SnapshotError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Snapshot '{label}' deleted.")
