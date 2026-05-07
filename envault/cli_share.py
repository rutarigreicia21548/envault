"""CLI commands for creating and redeeming share tokens."""

import sys

import click

from envault.share import ShareError, create_share_token, redeem_share_token, token_fingerprint
from envault.vault import Vault
from envault.cli import _make_vault


@click.group("share")
def share_group():
    """Share secrets securely with other team members."""


@share_group.command("create")
@click.option("--project", "-p", required=True, help="Project name.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.option("--ttl", default=3600, show_default=True, help="Token TTL in seconds.")
@click.option("--label", default="", help="Optional label for this share.")
def share_create(project: str, password: str, ttl: int, label: str):
    """Create a share token from the current vault secrets."""
    try:
        vault = _make_vault(project, password)
        secrets = vault.pull()
        token = create_share_token(secrets, password, ttl=ttl, label=label or None)
        fp = token_fingerprint(token)
        click.echo(f"Share token (fingerprint: {fp}):\n")
        click.echo(token)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@share_group.command("redeem")
@click.argument("token")
@click.option("--password", prompt=True, hide_input=True, help="Token password.")
@click.option("--project", "-p", required=True, help="Project to write secrets into.")
@click.option("--vault-password", prompt="Vault password", hide_input=True)
def share_redeem(token: str, password: str, project: str, vault_password: str):
    """Redeem a share token and push secrets into a vault project."""
    try:
        secrets = redeem_share_token(token, password)
        vault = _make_vault(project, vault_password)
        vault.push(secrets)
        fp = token_fingerprint(token)
        click.echo(f"Redeemed token {fp}: {len(secrets)} secret(s) pushed to '{project}'.")
    except ShareError as exc:
        click.echo(f"Share error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
