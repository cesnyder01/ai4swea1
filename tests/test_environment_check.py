from src.check_environment import format_bytes, get_package_version


def test_format_bytes_handles_basic_values() -> None:
    assert format_bytes(0) == "0.00 B"
    assert format_bytes(1024) == "1.00 KiB"


def test_get_package_version_reports_missing_package() -> None:
    assert get_package_version("definitely-not-installed-package") == "not installed"
