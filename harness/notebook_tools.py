# Generated from notebooks/redesign/00_harness_and_audit.ipynb; edit the notebook, not this file.
"""노트북 export 셀을 실행 없이 추출하고 Python 파일과 비교합니다."""

import argparse
import ast
import json
from pathlib import Path


def render_exports(notebook: Path, root: Path) -> dict[Path, str]:
    """노트북에서 {안전한 목적지: Python 소스}를 반환합니다. 실행/쓰기는 하지 않습니다."""
    root = root.resolve()
    notebook = notebook.resolve()
    relative = notebook.relative_to(root).as_posix()
    data = json.loads(notebook.read_text(encoding="utf-8-sig"))
    groups = {}
    for cell in data["cells"]:
        metadata = cell.get("metadata", {})
        if cell["cell_type"] != "code" or "export" not in metadata.get("tags", []):
            continue
        name = metadata.get("export_to")
        if not isinstance(name, str) or not name:
            raise ValueError("export 셀에는 export_to 경로가 필요합니다.")
        path = Path(name)
        # resolve는 상위 경로와 심볼릭 링크를 포함한 실제 목적지를 확인합니다.
        target = (root / path).resolve()
        if path.is_absolute() or not target.is_relative_to(root):
            raise ValueError(f"저장소 밖으로 추출할 수 없습니다: {name}")
        inside = target.relative_to(root)
        if inside.parts[0] not in {"app", "harness", "tests"} or target.suffix != ".py":
            raise ValueError(f"app/harness/tests의 Python 파일만 허용합니다: {name}")
        source = cell.get("source", [])
        text = source if isinstance(source, str) else "".join(source)
        groups.setdefault(target, []).append(text.rstrip())
    if not groups:
        raise ValueError("export 코드 셀이 없습니다.")
    result = {}
    for target, parts in groups.items():
        # 첫 줄의 소유권 표시로 다른 원본의 파일 덮어쓰기를 막습니다.
        header = f"# Generated from {relative}; edit the notebook, not this file.\n"
        source = header + "\n\n".join(parts) + "\n"
        ast.parse(source, filename=str(target))
        result[target] = source
    return result


def sync_exports(notebooks: list[Path], root: Path, *, write: bool = False) -> list[str]:
    """차이 목록을 반환합니다. write=True이면 모든 검증 후 추출본을 갱신합니다."""
    root = root.resolve()
    rendered = {}
    for notebook in notebooks:
        for target, source in render_exports(notebook, root).items():
            if target in rendered:
                raise ValueError(f"여러 노트북이 같은 파일을 지정했습니다: {target}")
            rendered[target] = source
    changed = []
    for target, source in rendered.items():
        existing = target.read_text(encoding="utf-8") if target.exists() else None
        owner = source.splitlines()[0]
        if existing is not None and (not existing.splitlines() or existing.splitlines()[0] != owner):
            raise ValueError(f"수동 작성 파일 또는 다른 노트북 소유 파일입니다: {target}")
        if existing != source:
            changed.append(target.relative_to(root).as_posix())
    if write:
        for target, source in rendered.items():
            if target.relative_to(root).as_posix() in changed:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(source, encoding="utf-8", newline="\n")
    return changed


def main() -> int:
    """--check는 차이가 있으면 종료 코드 1, --write는 추출본을 갱신합니다."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    parser.add_argument("notebooks", nargs="*", help="저장소 기준 노트북 경로")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    names = args.notebooks or ["notebooks/redesign/00_harness_and_audit.ipynb"]
    changed = sync_exports([root / name for name in names], root, write=args.write)
    print("Changed: " + ", ".join(changed) if changed else "Notebook exports match.")
    return int(bool(changed) and not args.write)


if __name__ == "__main__" and "__file__" in globals():
    raise SystemExit(main())
