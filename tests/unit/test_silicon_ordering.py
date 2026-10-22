"""Prediction ordering is a Git ancestry rule, not a wall-clock comparison."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / 'validation/L3_silicon/check_ordering.py'
PREDICTION = 'validation/L3_silicon/chip/predictions/dot.json'
RESULT = 'validation/L3_silicon/chip/results/dot.json'


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, 'init', '-q', '-b', 'main')
    git(tmp_path, 'config', 'user.name', 'Ordering test')
    git(tmp_path, 'config', 'user.email', 'test@example.invalid')
    git(tmp_path, 'config', 'core.hooksPath', '/dev/null')
    git(tmp_path, 'commit', '--allow-empty', '-qm', 'initial')
    return tmp_path


def commit(root, paths, message):
    for name, content in paths.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if content is None:
            path.unlink()
        else:
            path.write_text(content)
    git(root, 'add', '-A')
    git(root, 'commit', '-qm', message)


def check(root):
    return subprocess.run([sys.executable, str(CHECKER)], cwd=root,
                          capture_output=True, text=True)


def test_empty_history_is_not_measurement_evidence(repo):
    result = check(repo)
    assert result.returncode == 0, result.stderr
    assert 'no prediction or measurement files' in result.stdout


def test_prediction_then_result_passes(repo):
    commit(repo, {PREDICTION: '{}'}, 'FROZEN PREDICTIONS: dot')
    commit(repo, {RESULT: '{}'}, 'measured dot')
    assert check(repo).returncode == 0


@pytest.mark.parametrize('order', ['missing', 'before', 'same'])
def test_result_requires_strictly_prior_prediction(repo, order):
    if order == 'same':
        commit(repo, {PREDICTION: '{}', RESULT: '{}'}, 'FROZEN PREDICTIONS: too late')
    else:
        commit(repo, {RESULT: '{}'}, 'measurement first')
        if order == 'before':
            commit(repo, {PREDICTION: '{}'}, 'FROZEN PREDICTIONS: too late')
    result = check(repo)
    assert result.returncode != 0
    assert 'prediction' in result.stderr


@pytest.mark.parametrize('path', [PREDICTION, RESULT])
@pytest.mark.parametrize('content', ['{"changed": true}', None])
def test_published_bytes_cannot_be_rewritten_or_deleted(repo, path, content):
    commit(repo, {PREDICTION: '{}'}, 'FROZEN PREDICTIONS: dot')
    commit(repo, {RESULT: '{}'}, 'measured dot')
    commit(repo, {path: content}, 'rewrite evidence')
    result = check(repo)
    assert result.returncode != 0
    assert 'changed or deleted' in result.stderr


def test_independent_branch_prediction_is_not_prior(repo):
    initial = git(repo, 'rev-parse', 'HEAD')
    commit(repo, {PREDICTION: '{}'}, 'FROZEN PREDICTIONS: dot')
    git(repo, 'checkout', '-qb', 'measurement', initial)
    commit(repo, {RESULT: '{}'}, 'measured dot')
    git(repo, 'checkout', '-q', 'main')
    git(repo, 'merge', '--no-ff', '-qm', 'merge independent measurement', 'measurement')
    result = check(repo)
    assert result.returncode != 0
    assert 'ordering refused:' in result.stderr


def test_raw_result_requires_prediction_too(repo):
    commit(repo, {'validation/L3_silicon/chip/results/dot/raw.csv': 'time\n1\n'}, 'raw first')
    result = check(repo)
    assert result.returncode != 0
    assert 'ordering refused:' in result.stderr


def test_prediction_commit_has_explicit_freeze_message(repo):
    commit(repo, {PREDICTION: '{}'}, 'ordinary development')
    result = check(repo)
    assert result.returncode != 0
    assert 'ordering refused:' in result.stderr


def test_legitimate_branch_merge_preserves_order(repo):
    commit(repo, {PREDICTION: '{}'}, 'FROZEN PREDICTIONS: dot')
    git(repo, 'checkout', '-qb', 'measurement')
    commit(repo, {RESULT: '{}'}, 'measured dot')
    git(repo, 'checkout', '-q', 'main')
    git(repo, 'merge', '--no-ff', '-qm', 'merge measurement', 'measurement')
    result = check(repo)
    assert result.returncode == 0, result.stderr


def test_edit_then_restore_does_not_erase_history(repo):
    commit(repo, {PREDICTION: '{}'}, 'FROZEN PREDICTIONS: dot')
    commit(repo, {PREDICTION: '{"x": 1}'}, 'edit')
    commit(repo, {PREDICTION: '{}'}, 'restore')
    result = check(repo)
    assert result.returncode != 0
    assert 'changed or deleted' in result.stderr


def test_shallow_clone_refuses(repo, tmp_path):
    commit(repo, {PREDICTION: '{}'}, 'FROZEN PREDICTIONS: dot')
    clone = tmp_path / 'shallow'
    subprocess.run(['git', 'clone', '-q', '--depth=1', repo.as_uri(), str(clone)], check=True)
    result = check(clone)
    assert result.returncode != 0
    assert 'full Git history required' in result.stderr
