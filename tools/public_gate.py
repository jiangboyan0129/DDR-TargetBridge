#!/usr/bin/env python3
"""Public payload completeness, links, size and bounded privacy checks.

A pass applies to the enumerated current payload. It does not establish data
rights, author identity, absence of every possible secret, or biological validity.
"""
from __future__ import annotations
import csv
import gzip
import hashlib
import json
import re
import sys
import zipfile
import zlib
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from public_inventory import candidates, MANIFEST

TEXT_SUFFIXES = {'.md', '.json', '.tsv', '.csv', '.py', '.txt', '.svg', '.yml', '.yaml', '.cff', '.template'}
MAX_FILE = 100 * 1024 * 1024
MAX_EXPANDED = 128 * 1024 * 1024
PATTERNS = [
    rb'/' + rb'Users/', rb'/' + rb'private/var/folders/',
    rb'-----BEGIN ' + rb'(?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    rb'ghp_' + rb'[A-Za-z0-9]{36}',
    rb'github_pat_' + rb'[A-Za-z0-9_]{50,}',
    rb'sk-proj-' + rb'[A-Za-z0-9_-]{30,}',
]


def chunks(path: Path):
    """Read bounded representations; PDF stream inspection is not full PDF parsing."""
    if path.suffix in TEXT_SUFFIXES or path.name in {'Makefile', '.gitignore', '.gitattributes'}:
        yield path.read_bytes()
    elif path.suffix in {'.pptx', '.docx', '.xlsx'}:
        with zipfile.ZipFile(path) as archive:
            infos = [i for i in archive.infolist() if i.filename.endswith(('.xml', '.rels'))]
            if sum(i.file_size for i in infos) > MAX_EXPANDED:
                raise ValueError('Office XML exceeds scan budget')
            for info in infos:
                yield archive.read(info)
    elif path.suffix == '.gz':
        with gzip.open(path, 'rb') as handle:
            content = handle.read(MAX_EXPANDED + 1)
        if len(content) > MAX_EXPANDED:
            raise ValueError('Expanded gzip exceeds scan budget')
        yield content
    elif path.suffix == '.pdf':
        raw = path.read_bytes()
        yield raw
        # Catch common paths in plain or Flate-compressed streams. Final PDFs also
        # require manual text/metadata and rendered-page review at publication.
        total = 0
        for stream in re.findall(rb'stream\r?\n(.*?)\r?\nendstream', raw, flags=re.S):
            try:
                obj = zlib.decompressobj()
                decoded = obj.decompress(stream, MAX_EXPANDED - total + 1)
                total += len(decoded)
                if total > MAX_EXPANDED:
                    raise ValueError('PDF streams exceed scan budget')
                yield decoded
            except zlib.error:
                continue


def inspect(root: Path) -> dict:
    root = root.resolve()
    issues = []
    warnings = []
    with (root / MANIFEST).open(encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle, delimiter='\t'))
    listed = [row['path'] for row in rows]
    if len(listed) != len(set(listed)):
        issues.append('Duplicate manifest identity')
    paths, scope = candidates(root)
    payload = set(paths)
    for relative in sorted(payload - set(listed) - {MANIFEST}):
        issues.append('Unmanifested public file: ' + relative)
    for relative in sorted(set(listed) - payload):
        issues.append('Manifest member absent from current payload: ' + relative)

    max_size = 0
    for relative in paths:
        path = root / relative
        if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file():
            issues.append('Missing/unsafe public file: ' + relative)
            continue
        max_size = max(max_size, path.stat().st_size)
        if path.stat().st_size >= MAX_FILE:
            issues.append('Oversize: ' + relative)
        if any(part in {'.env', '.DS_Store', '__pycache__'} or part.startswith('.env.') for part in path.parts):
            issues.append('Private artifact: ' + relative)
        try:
            for content in chunks(path):
                if any(re.search(pattern, content) for pattern in PATTERNS):
                    issues.append('Private pattern: ' + relative)
                    break
        except (OSError, ValueError, zipfile.BadZipFile) as error:
            issues.append(f'Cannot inspect {relative}: {error}')

        if path.suffix == '.md' and not relative.startswith('provenance/releases/v1.0.0/'):
            # Include reports and portfolio, not only README/docs. Angle-bracket
            # link syntax and %20 are supported; anchors do not name files.
            text = path.read_text(encoding='utf-8')
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', text):
                target = target.strip().strip('<>')
                if target.startswith(('https://', 'http://', '#', 'mailto:', 'data:')):
                    continue
                target = unquote(target.split('#', 1)[0])
                resolved = (path.parent / target).resolve()
                if not resolved.is_relative_to(root) or not resolved.exists():
                    (warnings if relative == 'data/historical_sources/stage0/Stage0_Report.md' else issues).append(f'Broken relative link in archived source context: {relative} -> {target}' if relative == 'data/historical_sources/stage0/Stage0_Report.md' else f'Broken relative link: {relative} -> {target}')
                elif resolved.is_file() and resolved.relative_to(root).as_posix() not in payload:
                    issues.append(f'Unpublished link: {relative} -> {target}')

    facts = json.loads((root / 'config/portfolio_facts.json').read_text())
    grid = root / 'results/canonical/support_views/decision_grid.tsv'
    if hashlib.sha256(grid.read_bytes()).hexdigest() != facts['source_sha256']:
        issues.append('Canonical scientific result changed')
    return {'status': 'PUBLIC_PACKAGE_GATE_FAIL' if issues else 'PUBLIC_PACKAGE_GATE_PASS',
            'scope': scope, 'files': len(paths), 'max_file_bytes': max_size,
            'scientific_result_sha256_unchanged': not ('Canonical scientific result changed' in issues),
            'privacy_scope': 'bounded patterns, Office XML, gzip and common PDF streams; not exhaustive',
            'issues': issues, 'warnings': warnings}


def main():
    result = inspect(ROOT)
    print(json.dumps(result, indent=2))
    if result['issues']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
