from __future__ import annotations

import hashlib
import json
import re
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from contract_review_assistant.app_paths import project_root as default_project_root
from contract_review_assistant.branding import APP_EXPORTS_DIRNAME, PRODUCT_NAME, PRODUCT_SLUG, WINDOWS_EXE_NAME

APP_NAME = PRODUCT_NAME
APP_SLUG = PRODUCT_SLUG
EXE_NAME = WINDOWS_EXE_NAME
START_HERE_FILENAME = "START-HERE.cmd"
QUICK_START_FILENAME = "QUICK-START.txt"
MANIFEST_FILENAME = "RELEASE-MANIFEST.json"
BUNDLE_CHECKSUM_FILENAME = "BUNDLE-CONTENTS-SHA256.txt"
BUNDLE_VERIFY_SCRIPT = "VERIFY-CHECKSUMS.ps1"
VERSION_INFO_PATH = Path("packaging") / "windows" / "file_version_info.txt"
VERIFY_SCRIPT_SOURCE_PATH = Path("packaging") / "windows" / BUNDLE_VERIFY_SCRIPT
DOC_FILES = (
    "README-FIRST.md",
    "CLIENT-HANDOFF.md",
    "RELEASE-NOTES.md",
)

_PRODUCT_VERSION_RE = re.compile(r"StringStruct\('ProductVersion', '([^']+)'\)")
_FILE_VERSION_RE = re.compile(r"filevers=\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)")


@dataclass(frozen=True)
class ReleaseBundleResult:
    version: str
    bundle_dir: Path
    bundle_zip: Path
    bundle_zip_sha256: Path
    checksum_manifest: Path

    def to_dict(self) -> dict[str, str]:
        return {
            "version": self.version,
            "bundle_dir": str(self.bundle_dir),
            "bundle_zip": str(self.bundle_zip),
            "bundle_zip_sha256": str(self.bundle_zip_sha256),
            "checksum_manifest": str(self.checksum_manifest),
        }


def extract_release_version(version_info_path: Path) -> str:
    text = version_info_path.read_text(encoding="utf-8")
    product_match = _PRODUCT_VERSION_RE.search(text)
    if product_match:
        return product_match.group(1)

    file_match = _FILE_VERSION_RE.search(text)
    if file_match:
        parts = list(file_match.groups())
        while parts and parts[-1] == "0":
            parts.pop()
        return ".".join(parts or ["0"])

    raise ValueError(f"Could not determine release version from {version_info_path}")


def bundle_name_for_version(version: str) -> str:
    return f"{APP_SLUG}_v{version}_portable"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def describe_bundle_files(bundle_dir: Path) -> list[dict[str, object]]:
    details: list[dict[str, object]] = []
    for path in sorted(bundle_dir.rglob("*")):
        if not path.is_file() or path.name == BUNDLE_CHECKSUM_FILENAME:
            continue
        details.append(
            {
                "path": path.relative_to(bundle_dir).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return details


def write_checksum_manifest(bundle_dir: Path) -> Path:
    entries: list[str] = []
    for path in sorted(bundle_dir.rglob("*")):
        if not path.is_file() or path.name == BUNDLE_CHECKSUM_FILENAME:
            continue
        relative = path.relative_to(bundle_dir).as_posix()
        entries.append(f"{sha256_file(path)} *{relative}")

    manifest_path = bundle_dir / BUNDLE_CHECKSUM_FILENAME
    manifest_text = "\n".join(entries)
    if manifest_text:
        manifest_text += "\n"
    manifest_path.write_text(manifest_text, encoding="utf-8")
    return manifest_path


def write_start_here_launcher(bundle_dir: Path) -> Path:
    launcher_text = (
        "@echo off\r\n"
        "setlocal\r\n"
        "cd /d \"%~dp0\"\r\n"
        "\r\n"
        f"if not exist \"{EXE_NAME}\" (\r\n"
        f"    echo Could not find {EXE_NAME} in this folder.\r\n"
        "    echo Keep START-HERE.cmd beside the delivered app files.\r\n"
        "    pause\r\n"
        "    exit /b 1\r\n"
        ")\r\n"
        "\r\n"
        f"echo Launching {APP_NAME}...\r\n"
        f"start \"\" \"%~dp0{EXE_NAME}\"\r\n"
        "if errorlevel 1 (\r\n"
        "    echo The app could not be started.\r\n"
        "    pause\r\n"
        "    exit /b 1\r\n"
        ")\r\n"
        "\r\n"
        "exit /b 0\r\n"
    )
    launcher_path = bundle_dir / START_HERE_FILENAME
    launcher_path.write_text(launcher_text, encoding="utf-8")
    return launcher_path


def write_quick_start(bundle_dir: Path) -> Path:
    lines = [
        f"{APP_NAME} — quick start",
        "",
        "No installation is required for this portable build.",
        "",
        "1. Double-click START-HERE.cmd.",
        "2. In the app, click Open Contract.",
        "3. Select an authorized PDF, DOCX, or TXT contract.",
        "4. Click Scan Contract.",
        "5. Review the risk score, findings, and summary.",
        "6. Export or save the review results where appropriate.",
        "",
        "Helpful notes:",
        "- If Windows shows a SmartScreen warning, only continue if you trust the release source.",
        f"- The app keeps local scan history under Documents\\{APP_EXPORTS_DIRNAME}\\repository.",
        "- Exported reports save wherever you choose in the Save dialog.",
        "- Do not process contracts unless you are authorized to access them.",
        "",
        "For fuller instructions, see README-FIRST.md.",
    ]
    quick_start_path = bundle_dir / QUICK_START_FILENAME
    quick_start_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return quick_start_path


def zip_bundle(bundle_dir: Path, zip_path: Path) -> Path:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(bundle_dir.rglob("*")):
            if path.is_dir():
                continue
            arcname = Path(bundle_dir.name) / path.relative_to(bundle_dir)
            archive.write(path, arcname.as_posix())
    return zip_path


def write_zip_checksum(zip_path: Path) -> Path:
    checksum_path = zip_path.with_name(f"{zip_path.name}.sha256")
    checksum_path.write_text(f"{sha256_file(zip_path)} *{zip_path.name}\n", encoding="utf-8")
    return checksum_path


def release_manifest_notes(*, signed: bool) -> list[str]:
    if signed:
        return [
            "This release bundle contains the signed Windows executable for client delivery.",
            "Use VERIFY-CHECKSUMS.ps1 or BUNDLE-CONTENTS-SHA256.txt to validate bundle contents after delivery.",
        ]

    return [
        "This release bundle is portable and does not require mandatory cloud configuration for rule-based scanning.",
        "The executable is unsigned in this build environment because no code-signing certificate/tool was available.",
        "Use VERIFY-CHECKSUMS.ps1 or BUNDLE-CONTENTS-SHA256.txt to validate bundle contents after delivery.",
    ]


def build_handoff_bundle(
    project_root: Path | None = None,
    *,
    release_root: Path | None = None,
    source_exe: Path | None = None,
    signed: bool = False,
    clean: bool = True,
) -> ReleaseBundleResult:
    root = project_root or default_project_root()
    version = extract_release_version(root / VERSION_INFO_PATH)
    bundle_name = bundle_name_for_version(version)

    release_dir = release_root or root / "release"
    bundle_dir = release_dir / bundle_name
    zip_path = release_dir / f"{bundle_name}.zip"
    zip_sha_path = release_dir / f"{zip_path.name}.sha256"

    exe_path = source_exe or (root / "dist" / EXE_NAME)
    required_paths = [
        exe_path,
        *(root / name for name in DOC_FILES),
        root / VERIFY_SCRIPT_SOURCE_PATH,
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required release inputs:\n- " + "\n- ".join(missing))

    if clean and bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    if zip_sha_path.exists():
        zip_sha_path.unlink()

    shutil.copy2(exe_path, bundle_dir / EXE_NAME)
    for doc_name in DOC_FILES:
        shutil.copy2(root / doc_name, bundle_dir / doc_name)
    shutil.copy2(root / VERIFY_SCRIPT_SOURCE_PATH, bundle_dir / BUNDLE_VERIFY_SCRIPT)

    write_start_here_launcher(bundle_dir)
    write_quick_start(bundle_dir)

    manifest = {
        "app_name": APP_NAME,
        "version": version,
        "bundle_name": bundle_name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "packaging": "portable-windows-exe",
        "primary_executable": EXE_NAME,
        "client_launcher": START_HERE_FILENAME,
        "client_quick_start": QUICK_START_FILENAME,
        "checksum_manifest": BUNDLE_CHECKSUM_FILENAME,
        "checksum_verifier": BUNDLE_VERIFY_SCRIPT,
        "signed": signed,
        "notes": release_manifest_notes(signed=signed),
        "included_files": describe_bundle_files(bundle_dir),
    }
    (bundle_dir / MANIFEST_FILENAME).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    checksum_manifest = write_checksum_manifest(bundle_dir)
    zip_bundle(bundle_dir, zip_path)
    zip_sha256 = write_zip_checksum(zip_path)

    return ReleaseBundleResult(
        version=version,
        bundle_dir=bundle_dir,
        bundle_zip=zip_path,
        bundle_zip_sha256=zip_sha256,
        checksum_manifest=checksum_manifest,
    )
