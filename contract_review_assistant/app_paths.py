from __future__ import annotations

import sys
from pathlib import Path

from .branding import APP_EXPORTS_DIRNAME, LEGACY_EXPORTS_DIRNAMES


APP_REPOSITORY_DIRNAME = "repository"
LEGACY_EXPORTS_DIRNAME = LEGACY_EXPORTS_DIRNAMES[0]


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def bundle_root() -> Path:
    if getattr(sys, "frozen", False) and getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS)
    return project_root()


def install_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return project_root()


def external_or_bundled_path(*parts: str) -> Path:
    external = install_root().joinpath(*parts)
    if external.exists():
        return external
    return bundle_root().joinpath(*parts)


def default_exports_dir(home: Path | None = None) -> Path:
    if getattr(sys, "frozen", False):
        home_dir = home or Path.home()
        documents_dir = home_dir / "Documents"
        base_dir = documents_dir if documents_dir.exists() else home_dir
        return base_dir / APP_EXPORTS_DIRNAME
    return project_root() / "exports"


def legacy_exports_dir(home: Path | None = None) -> Path:
    home_dir = home or Path.home()
    documents_dir = home_dir / "Documents"
    base_dir = documents_dir if documents_dir.exists() else home_dir
    return base_dir / LEGACY_EXPORTS_DIRNAME


def default_repository_dir(home: Path | None = None, exports_dir: Path | None = None) -> Path:
    base_dir = exports_dir or default_exports_dir(home=home)
    return base_dir / APP_REPOSITORY_DIRNAME
