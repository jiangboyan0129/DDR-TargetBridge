"""Verify the revision package, without running any scientific computation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


def verify(root: Path) -> dict:
    root = root.resolve(strict=True)
    manifest = json.loads((root / 'DELIVERY_MANIFEST.json').read_text(encoding='utf-8'))
    seen: set[str] = set()
    for record in manifest['files']:
        name = record['path']
        relative = PurePosixPath(name)
        if (not name or '\\' in name or relative.is_absolute()
                or any(part in ('..', '.') for part in relative.parts)
                or name in seen):
            raise ValueError(f'Invalid or duplicate delivery path: {name!r}')
        seen.add(name)
        path = (root / Path(*relative.parts)).resolve(strict=True)
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f'Not a regular file within package: {name}')
        if path.stat().st_size != record['bytes']:
            raise ValueError(f'File size differs: {name}')
        digest = hashlib.sha256()
        with path.open('rb') as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b''):
                digest.update(block)
        if digest.hexdigest() != record['sha256']:
            raise ValueError(f'SHA-256 differs: {name}')
    return {'status': 'DELIVERY_FILES_MATCH', 'verified_files': len(seen),
            'scientific_computation_executed': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.root), ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SystemExit(f'DELIVERY_CHECK_FAILED: {exc}') from exc
