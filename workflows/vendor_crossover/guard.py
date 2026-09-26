from pathlib import Path
import hashlib
import json

class GuardError(RuntimeError):
    pass

def sha256(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def checked_path(root,relative,expected_hash=None,expected_size=None):
    root=Path(root).resolve(strict=True)
    rel=Path(relative)
    if rel.is_absolute() or '..' in rel.parts: raise GuardError('Non-relative or traversing path')
    p=(root/rel).resolve(strict=True)
    if not p.is_relative_to(root) or not p.is_file(): raise GuardError('Outside authorized directory or not a file')
    if expected_size is not None and p.stat().st_size!=expected_size: raise GuardError('Size mismatch: '+str(relative))
    if expected_hash is not None and sha256(p)!=expected_hash: raise GuardError('SHA-256 mismatch: '+str(relative))
    return p

def assert_authorized(flag):
    if flag != 'I_AUTHORIZE_THE_FROZEN_TWO_MODULE_R2_CHECK':
        raise GuardError('R2 remains closed. Explicit separate human authorization token required.')

def dump(path,obj):
    Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
