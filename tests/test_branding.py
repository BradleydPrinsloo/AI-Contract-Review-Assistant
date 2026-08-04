from pathlib import Path

from contract_review_assistant.app_paths import APP_EXPORTS_DIRNAME
from contract_review_assistant.branding import (
    APP_ICON_FILENAME,
    APP_SPLASH_FILENAME,
    PRODUCT_NAME,
    PRODUCT_VERSION,
    REPORT_EXECUTIVE_TITLE,
    REPORT_FULL_TITLE,
    WINDOWS_EXE_NAME,
)


def test_contractiq_branding_constants_are_consistent() -> None:
    assert PRODUCT_NAME == "ContractIQ"
    assert PRODUCT_VERSION == "2.0.0"
    assert APP_EXPORTS_DIRNAME == "ContractIQ Exports"
    assert WINDOWS_EXE_NAME == "ContractIQ.exe"
    assert REPORT_FULL_TITLE == "ContractIQ Contract Analysis Report"
    assert REPORT_EXECUTIVE_TITLE == "ContractIQ Executive Risk Brief"


def test_contractiq_brand_assets_are_checked_in() -> None:
    assets = Path(__file__).resolve().parents[1] / "assets"
    for filename in (
        "contractiq_logo.svg",
        "contractiq_icon.svg",
        "contractiq_icon.png",
        APP_ICON_FILENAME,
        APP_SPLASH_FILENAME,
    ):
        path = assets / filename
        assert path.exists(), filename
        assert path.stat().st_size > 100, filename
