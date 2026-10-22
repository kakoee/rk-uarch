"""Check committed prediction/result ancestry and immutability (U-P9/U-P10).

Run from a full Git checkout. This checks repository history, not whether someone
measured privately before committing. It does not generate or inspect predictions.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import PurePosixPath

PREFIX = 'validation/L3_silicon/'


def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], text=True, stderr=subprocess.PIPE).strip()


def blob(commit: str, path: str) -> str | None:
    result = subprocess.run(['git', 'rev-parse', '--verify', f'{commit}:{path}'],
                            capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def evidence(path: str) -> tuple[str, str] | None:
    parts = PurePosixPath(path).parts
    if len(parts) < 5 or parts[:2] != ('validation', 'L3_silicon'):
        return None
    if parts[3] == 'predictions' and path.endswith('.json') and len(parts) == 5:
        return 'prediction', path
    if parts[3] == 'results':
        # A flat <id>.json receipt or raw files under <id>/ map to <id>.json.
        if len(parts) == 5:
            if not path.endswith('.json'):
                raise ValueError(f'result file needs an <id>/ directory: {path}')
            name = parts[4]
        else:
            name = parts[4] + '.json'
        return 'result', '/'.join((*parts[:3], 'predictions', name))
    return None


def origin(path: str) -> str:
    additions = set(git('log', '--full-history', '--no-merges', '--no-renames',
                        '--diff-filter=A', '--format=%H', 'HEAD', '--', path).splitlines())
    if len(additions) != 1:
        raise ValueError(f'expected one immutable addition: {path}')
    first = additions.pop()
    expected = blob(first, path)
    revisions = set(git('log', '--full-history', '-m', '--format=%H',
                        'HEAD', '--', path).splitlines()) | {'HEAD'}
    if expected is None or any(blob(revision, path) != expected for revision in revisions):
        raise ValueError(f'evidence changed or deleted: {path}')
    return first


def check() -> str:
    if git('rev-parse', '--is-shallow-repository') != 'false':
        raise ValueError('full Git history required (fetch-depth: 0)')
    paths = set(git('log', '--full-history', '-m', '--no-renames', '--format=',
                    '--name-only', 'HEAD', '--', PREFIX).splitlines())
    records = {path: record for path in sorted(paths) if (record := evidence(path))}
    origins = {path: origin(path) for path in records}
    for path, (kind, prediction) in records.items():
        if kind == 'prediction':
            message = git('show', '-s', '--format=%s', origins[path])
            if not message.startswith('FROZEN PREDICTIONS:'):
                raise ValueError(f'prediction needs a FROZEN PREDICTIONS: commit: {path}')
            continue
        if prediction not in origins:
            raise ValueError(f'missing prediction {prediction} for {path}')
        before, after = origins[prediction], origins[path]
        ancestor = subprocess.run(['git', 'merge-base', '--is-ancestor', before, after],
                                  capture_output=True).returncode
        if before == after or ancestor != 0:
            raise ValueError(f'prediction must strictly precede result in ancestry: {path}')
    if not records:
        return 'no prediction or measurement files; ordering infrastructure only'
    return f'ordering and immutable history verified for {len(records)} evidence files'


if __name__ == '__main__':
    try:
        print(check())
    except (ValueError, subprocess.CalledProcessError) as error:
        print(f'ordering refused: {error}', file=sys.stderr)
        sys.exit(1)
