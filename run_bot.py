from __future__ import annotations

from pathlib import Path


CONFLICT_MARKERS = ("<" * 7, "=" * 7, ">" * 7)


def check_merge_conflicts(root: Path) -> list[tuple[Path, int, str]]:
    findings: list[tuple[Path, int, str]] = []
    for file in root.glob("*.py"):
        try:
            lines = file.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, start=1):
            if any(marker in line for marker in CONFLICT_MARKERS):
                findings.append((file, i, line.strip()))
    return findings


def main() -> None:
    findings = check_merge_conflicts(Path("."))
    if findings:
        print("ERROR: Git merge conflict markers detected. Fix before starting bot:")
        for file, lineno, line in findings:
            print(f" - {file}:{lineno}: {line}")
        raise SystemExit(2)

    from main import main as run_main

    run_main()


if __name__ == "__main__":
    main()
