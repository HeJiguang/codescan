from codescan.config import DEFAULT_CONFIG
from codescan.vulndb import VulnerabilityDB


def test_default_vulndb_config_is_safe_for_local_startup() -> None:
    vulndb_config = DEFAULT_CONFIG["vulndb"]

    assert vulndb_config["update_url"] == ""
    assert vulndb_config["auto_update"] is False


def test_vulndb_init_skips_auto_update_when_url_missing(monkeypatch) -> None:
    from codescan.config import config

    original_vulndb_config = dict(config.config.get("vulndb", {}))
    config.config["vulndb"] = {
        "auto_update": True,
        "update_url": "",
        "update_interval_days": 7,
    }

    def fail_update(self):
        raise AssertionError("update() should not run when update_url is empty")

    monkeypatch.setattr(VulnerabilityDB, "update", fail_update)

    try:
        VulnerabilityDB()
    finally:
        config.config["vulndb"] = original_vulndb_config
