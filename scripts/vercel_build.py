"""Copy Flask static files into public/static so Vercel serves them from the CDN."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_STATIC = ROOT / "src" / "static"
PUBLIC_STATIC = ROOT / "public" / "static"


def main() -> None:
    if not SRC_STATIC.is_dir():
        raise SystemExit(f"Missing static directory: {SRC_STATIC}")

    if PUBLIC_STATIC.exists():
        shutil.rmtree(PUBLIC_STATIC)

    shutil.copytree(SRC_STATIC, PUBLIC_STATIC)
    print(f"Copied {SRC_STATIC} -> {PUBLIC_STATIC}")


if __name__ == "__main__":
    main()
