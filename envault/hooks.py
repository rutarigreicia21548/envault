"""Pre/post hook support for envault vault operations.

Allows users to register shell commands or Python callables that run
before or after push/pull operations, enabling custom workflows such
as reloading services, notifying teammates, or validating secrets.
"""

from __future__ import annotations

import subprocess
import json
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

# Hook event names
EVENT_PRE_PUSH = "pre_push"
EVENT_POST_PUSH = "post_push"
EVENT_PRE_PULL = "pre_pull"
EVENT_POST_PULL = "post_pull"

ALL_EVENTS = [EVENT_PRE_PUSH, EVENT_POST_PUSH, EVENT_PRE_PULL, EVENT_POST_PULL]

_HOOKS_FILE = ".envault_hooks.json"


class HookError(Exception):
    """Raised when a hook command fails."""


def _hooks_path(base_dir: Optional[Path] = None) -> Path:
    """Return the path to the hooks config file."""
    base = base_dir or Path.cwd()
    return base / _HOOKS_FILE


def load_hooks(base_dir: Optional[Path] = None) -> Dict[str, List[str]]:
    """Load shell hooks from the hooks config file.

    Returns a dict mapping event names to lists of shell command strings.
    Missing events default to empty lists.
    """
    path = _hooks_path(base_dir)
    if not path.exists():
        return {event: [] for event in ALL_EVENTS}

    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    hooks: Dict[str, List[str]] = {event: [] for event in ALL_EVENTS}
    for event in ALL_EVENTS:
        raw = data.get(event, [])
        if isinstance(raw, list):
            hooks[event] = [str(cmd) for cmd in raw]
        elif isinstance(raw, str):
            hooks[event] = [raw]
    return hooks


def save_hooks(hooks: Dict[str, List[str]], base_dir: Optional[Path] = None) -> None:
    """Persist hook configuration to the hooks config file."""
    path = _hooks_path(base_dir)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(hooks, fh, indent=2)
        fh.write("\n")


def add_hook(event: str, command: str, base_dir: Optional[Path] = None) -> None:
    """Append a shell command to the hook list for *event*.

    Args:
        event: One of the EVENT_* constants.
        command: Shell command string to execute.
        base_dir: Directory containing the hooks file (defaults to cwd).

    Raises:
        ValueError: If *event* is not a recognised hook event.
    """
    if event not in ALL_EVENTS:
        raise ValueError(f"Unknown hook event '{event}'. Choose from: {ALL_EVENTS}")
    hooks = load_hooks(base_dir)
    hooks[event].append(command)
    save_hooks(hooks, base_dir)


def remove_hook(event: str, index: int, base_dir: Optional[Path] = None) -> str:
    """Remove the hook at *index* for *event* and return the removed command.

    Raises:
        ValueError: If *event* is unknown or *index* is out of range.
    """
    if event not in ALL_EVENTS:
        raise ValueError(f"Unknown hook event '{event}'.")
    hooks = load_hooks(base_dir)
    try:
        removed = hooks[event].pop(index)
    except IndexError:
        raise ValueError(
            f"No hook at index {index} for event '{event}'. "
            f"{len(hooks[event])} hook(s) registered."
        )
    save_hooks(hooks, base_dir)
    return removed


def run_hooks(
    event: str,
    base_dir: Optional[Path] = None,
    extra_env: Optional[Dict[str, str]] = None,
) -> List[str]:
    """Execute all shell hooks registered for *event*.

    Each command is run in a subprocess with the current environment,
    optionally extended with *extra_env* key/value pairs (e.g. project name).

    Returns:
        List of stdout strings from each hook command.

    Raises:
        HookError: If any hook command exits with a non-zero return code.
    """
    hooks = load_hooks(base_dir)
    commands = hooks.get(event, [])
    if not commands:
        return []

    env = {**os.environ}
    if extra_env:
        env.update(extra_env)

    outputs: List[str] = []
    for cmd in commands:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            raise HookError(
                f"Hook '{cmd}' for event '{event}' failed "
                f"(exit {result.returncode}):\n{result.stderr.strip()}"
            )
        outputs.append(result.stdout)
    return outputs
