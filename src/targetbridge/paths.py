from pathlib import Path

def contained(root, candidate):
    """Resolve both sides, accepting macOS canonical roots and rejecting escapes."""
    root = Path(root).resolve()
    candidate = Path(candidate).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("Path escapes allowed root")
    return candidate

def fresh_output(repo, output):
    repo = Path(repo).resolve()
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("Output exists; choose a fresh directory")
    for protected in (repo / "results", repo / "data", repo / "config", repo / "provenance", repo / "src"):
        if output == protected or output.is_relative_to(protected):
            raise ValueError("Output would modify accepted source evidence")
    if output == repo or repo.is_relative_to(output):
        raise ValueError("Output may not contain the repository")
    return output
