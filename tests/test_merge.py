"""Tests for envault.merge."""

import pytest

from envault.merge import (
    MergeConflict,
    MergeResult,
    merge_envs,
    parse_env,
)


# ---------------------------------------------------------------------------
# parse_env
# ---------------------------------------------------------------------------

def test_parse_env_basic():
    text = "FOO=bar\nBAZ=qux\n"
    assert parse_env(text) == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_skips_comments_and_blanks():
    text = "# comment\n\nFOO=bar\n"
    assert parse_env(text) == {"FOO": "bar"}


def test_parse_env_strips_quotes():
    text = 'FOO="hello world"\nBAR=\'single\'\n'
    assert parse_env(text) == {"FOO": "hello world", "BAR": "single"}


def test_parse_env_no_equals_skipped():
    text = "NOEQUALS\nFOO=bar\n"
    assert parse_env(text) == {"FOO": "bar"}


# ---------------------------------------------------------------------------
# merge_envs — no conflicts
# ---------------------------------------------------------------------------

def test_merge_only_local_key():
    result = merge_envs(base={}, local={"A": "1"}, remote={})
    assert result.merged == {"A": "1"}
    assert not result.has_conflicts


def test_merge_only_remote_key():
    result = merge_envs(base={}, local={}, remote={"B": "2"})
    assert result.merged == {"B": "2"}
    assert not result.has_conflicts


def test_merge_same_value_no_conflict():
    base = {"X": "old"}
    result = merge_envs(base=base, local={"X": "new"}, remote={"X": "new"})
    assert result.merged["X"] == "new"
    assert not result.has_conflicts


def test_merge_only_remote_changed():
    base = {"X": "old"}
    result = merge_envs(base=base, local={"X": "old"}, remote={"X": "new"})
    assert result.merged["X"] == "new"
    assert not result.has_conflicts


def test_merge_only_local_changed():
    base = {"X": "old"}
    result = merge_envs(base=base, local={"X": "new"}, remote={"X": "old"})
    assert result.merged["X"] == "new"
    assert not result.has_conflicts


# ---------------------------------------------------------------------------
# merge_envs — conflicts
# ---------------------------------------------------------------------------

def test_merge_conflict_detected():
    base = {"X": "old"}
    result = merge_envs(base=base, local={"X": "local_val"}, remote={"X": "remote_val"})
    assert result.has_conflicts
    assert len(result.conflicts) == 1
    assert result.conflicts[0].key == "X"


def test_merge_conflict_strategy_ours():
    base = {"X": "old"}
    result = merge_envs(base, {"X": "local"}, {"X": "remote"}, strategy="ours")
    assert result.merged["X"] == "local"


def test_merge_conflict_strategy_theirs():
    base = {"X": "old"}
    result = merge_envs(base, {"X": "local"}, {"X": "remote"}, strategy="theirs")
    assert result.merged["X"] == "remote"


def test_merge_invalid_strategy_raises():
    with pytest.raises(ValueError, match="Unknown merge strategy"):
        merge_envs({}, {}, {}, strategy="bogus")


# ---------------------------------------------------------------------------
# MergeResult helpers
# ---------------------------------------------------------------------------

def test_merge_result_summary_no_conflicts():
    result = MergeResult(merged={"A": "1", "B": "2"})
    assert "2 key(s)" in result.summary()
    assert "conflict" not in result.summary()


def test_merge_result_summary_with_conflicts():
    conflict = MergeConflict("X", "local", "remote")
    result = MergeResult(merged={"X": "local"}, conflicts=[conflict])
    summary = result.summary()
    assert "1 conflict" in summary
    assert "X" in summary


def test_merge_conflict_str():
    c = MergeConflict("KEY", "a", "b")
    s = str(c)
    assert "KEY" in s
    assert "a" in s
    assert "b" in s
