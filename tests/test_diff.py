"""Tests for envault.diff module."""

import pytest
from envault.diff import DiffResult, diff_envs, parse_env


# ---------------------------------------------------------------------------
# parse_env
# ---------------------------------------------------------------------------

def test_parse_env_basic():
    text = "KEY=value\nOTHER=123\n"
    result = parse_env(text)
    assert result == {"KEY": "value", "OTHER": "123"}


def test_parse_env_skips_comments_and_blanks():
    text = "# comment\n\nKEY=val\n"
    assert parse_env(text) == {"KEY": "val"}


def test_parse_env_strips_double_quotes():
    assert parse_env('KEY="hello world"') == {"KEY": "hello world"}


def test_parse_env_strips_single_quotes():
    assert parse_env("KEY='hello'") == {"KEY": "hello"}


def test_parse_env_no_value_after_equals():
    assert parse_env("EMPTY=") == {"EMPTY": ""}


def test_parse_env_skips_lines_without_equals():
    assert parse_env("NODIVIDER\nKEY=ok") == {"KEY": "ok"}


# ---------------------------------------------------------------------------
# diff_envs
# ---------------------------------------------------------------------------

LOCAL = "KEY=value\nNEW=added\n"
VAULT = "KEY=value\nOLD=removed\n"


def test_diff_added_keys():
    result = diff_envs(LOCAL, VAULT)
    assert "NEW" in result.added


def test_diff_removed_keys():
    result = diff_envs(LOCAL, VAULT)
    assert "OLD" in result.removed


def test_diff_unchanged_keys():
    result = diff_envs(LOCAL, VAULT)
    assert "KEY" in result.unchanged


def test_diff_changed_keys():
    local = "KEY=new_value\n"
    vault = "KEY=old_value\n"
    result = diff_envs(local, vault)
    assert "KEY" in result.changed


def test_diff_has_changes_true():
    assert diff_envs(LOCAL, VAULT).has_changes is True


def test_diff_has_changes_false():
    same = "KEY=value\n"
    assert diff_envs(same, same).has_changes is False


# ---------------------------------------------------------------------------
# DiffResult.summary
# ---------------------------------------------------------------------------

def test_summary_no_changes():
    result = DiffResult(unchanged=["KEY"])
    assert "(no changes)" in result.summary()


def test_summary_contains_added_marker():
    result = DiffResult(added=["NEW"])
    assert "+ NEW" in result.summary()


def test_summary_contains_removed_marker():
    result = DiffResult(removed=["OLD"])
    assert "- OLD" in result.summary()


def test_summary_contains_changed_marker():
    result = DiffResult(changed=["MOD"])
    assert "~ MOD" in result.summary()
