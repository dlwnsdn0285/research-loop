from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re
import shutil

from .config import load_config
from .manifest import new_manifest, write_manifest
from .validator import discover_runs, validate_run

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]+", "-", text.strip().lower()).strip("-")
    return text or "run"


def copy_if_missing(src: Path, dst: Path) -> None:
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def copy_tree_if_missing(src_dir: Path, dst_dir: Path) -> None:
    if not src_dir.exists():
        return
    for src in src_dir.rglob("*"):
        if src.is_file():
            rel = src.relative_to(src_dir)
            copy_if_missing(src, dst_dir / rel)


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    root.mkdir(parents=True, exist_ok=True)

    copy_if_missing(PACKAGE_ROOT / "RESEARCH_PROTOCOL.md", root / "RESEARCH_PROTOCOL.md")
    copy_if_missing(PACKAGE_ROOT / "research-loop.yaml.example", root / "research-loop.yaml")
    copy_tree_if_missing(PACKAGE_ROOT / "templates", root / "templates")
    copy_if_missing(PACKAGE_ROOT / "templates" / "AGENTS.md", root / "AGENTS.md")
    copy_if_missing(PACKAGE_ROOT / "templates" / "CLAUDE.md", root / "CLAUDE.md")

    copy_tree_if_missing(PACKAGE_ROOT / "skills" / "codex", root / ".agents" / "skills")
    copy_tree_if_missing(PACKAGE_ROOT / "skills" / "claude", root / ".claude" / "skills")
    copy_if_missing(
        PACKAGE_ROOT / ".github" / "workflows" / "validate-research-runs.yml",
        root / ".github" / "workflows" / "validate-research-runs.yml",
    )

    cfg = load_config(root)
    (root / cfg["history_root"]).mkdir(parents=True, exist_ok=True)
    print(f"[OK] initialized Research Loop in {root}")
    print("[OK] installed protocol, templates, agent instructions, provider skills, and CI validation")
    return 0


def next_run_id(day_dir: Path) -> int:
    nums = []
    if day_dir.exists():
        for p in day_dir.iterdir():
            m = re.match(r"exp(\d+)_", p.name)
            if m:
                nums.append(int(m.group(1)))
    return max(nums, default=0) + 1


def cmd_new(args: argparse.Namespace) -> int:
    root = Path(args.project).resolve()
    cfg = load_config(root)
    day = args.date or date.today().isoformat()
    day_dir = root / cfg["history_root"] / day
    n = next_run_id(day_dir)
    slug = slugify(args.name)
    run_name = f"exp{n:02d}_{slug}"
    run_dir = day_dir / run_name
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "raw").mkdir()
    shutil.copy2(root / "templates" / "01_PLAN.md", run_dir / "01_PLAN.md")
    manifest = new_manifest(run_name, day, args.parent)
    manifest["name"] = args.name
    write_manifest(run_dir, manifest)
    print(run_dir)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    root = Path(args.project).resolve()
    cfg = load_config(root)
    runs = discover_runs(root / cfg["history_root"]) if args.all else [Path(args.run).resolve()]
    failures = 0
    for run in runs:
        errors = validate_run(run, root)
        if errors:
            failures += 1
            print(f"[FAIL] {run}")
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"[OK] {run}")
    return 1 if failures else 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="research-loop")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="initialize Research Loop in a project")
    p_init.add_argument("path", nargs="?", default=".")
    p_init.set_defaults(func=cmd_init)

    p_new = sub.add_parser("new", help="create a new research run")
    p_new.add_argument("name")
    p_new.add_argument("--project", default=".")
    p_new.add_argument("--date", default=None)
    p_new.add_argument("--parent", default=None)
    p_new.set_defaults(func=cmd_new)

    p_val = sub.add_parser("validate", help="validate one run or the full history")
    p_val.add_argument("run", nargs="?")
    p_val.add_argument("--project", default=".")
    p_val.add_argument("--all", action="store_true")
    p_val.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    if args.command == "validate" and not args.all and not args.run:
        parser.error("validate requires RUN or --all")
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
