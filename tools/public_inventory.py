#!/usr/bin/env python3
"""Enumerate release payloads, including additions absent from the old manifest.

In a Git checkout, tracked files are never excused by .gitignore. Nonignored
untracked files are included for pre-commit checks. In an extracted release,
explicit local-only paths are excluded. This is not an exhaustive secret scanner.
"""
from __future__ import annotations
import fnmatch
import subprocess
from pathlib import Path

MANIFEST = 'provenance/RELEASE_MANIFEST.tsv'
LOCAL_DIRS = {'.git', '.build', '.venv', '__pycache__', '.pytest_cache'}
EXTERNAL_PATHS = (
    'data/historical_sources/stage0/raw/',
    'data/derived/final_count_export.tsv.gz',
    'data/derived/v3_factorial_sample_values.tsv.gz',
)


def local_only(relative: str) -> bool:
    parts = Path(relative).parts
    # .env and .DS_Store are deliberately NOT ignored by the fallback scanner.
    return (any(p in LOCAL_DIRS for p in parts)
            or relative.endswith(('.pyc', '.pyo', '.log'))
            or any(relative == p or relative.startswith(p) for p in EXTERNAL_PATHS))


def candidates(root: Path) -> tuple[list[str], str]:
    root = root.resolve()
    try:
        top = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=root,
                             capture_output=True, text=True, timeout=10)
        if top.returncode == 0 and Path(top.stdout.strip()).resolve() == root:
            tracked = subprocess.run(['git', 'ls-files', '-z', '--cached'], cwd=root,
                                     capture_output=True, check=True, timeout=10)
            others = subprocess.run(['git', 'ls-files', '-z', '--others', '--exclude-standard'],
                                    cwd=root, capture_output=True, check=True, timeout=10)
            decode = lambda b: {v.decode('utf-8', errors='strict') for v in b.split(b'\0') if v}
            return sorted(decode(tracked.stdout) | decode(others.stdout)), 'git_tracked_plus_nonignored_untracked'
    except (OSError, subprocess.SubprocessError, UnicodeError):
        pass
    return sorted(str(p.relative_to(root)) for p in root.rglob('*')
                  if (p.is_file() or p.is_symlink()) and not local_only(str(p.relative_to(root)))), 'extracted_tree'
