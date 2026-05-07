from md2kindle.config import AppConfig, load_config
from md2kindle.infrastructure.binaries import find_binary


def test_find_binary_prefers_highest_sorted_match(monkeypatch):
    root = "C:/project"
    bin_dir = "C:/project/bin"
    older = "C:/project/bin/kcc_c2e_9.6.2.exe"
    newer = "C:/project/bin/kcc_c2e_10.1.2.exe"
    monkeypatch.setattr(
        "glob.glob",
        lambda pattern: [older, newer]
        if pattern.replace("\\", "/") == "C:/project/bin/kcc*c2e*.exe"
        else [],
    )

    result = find_binary("kcc*c2e*.exe", root_dir=root, bin_dir=bin_dir)

    assert result == sorted([older, newer], reverse=True)[0]


def test_load_config_returns_explicit_app_config(monkeypatch):
    root = "C:/project"
    monkeypatch.setattr("shutil.which", lambda cmd: f"/usr/bin/{cmd}")
    monkeypatch.setattr("glob.glob", lambda pattern: [])

    config = load_config(root_dir=root)

    assert isinstance(config, AppConfig)
    assert config.output_folder_manga == "C:/project\\downloads"
    assert config.output_folder_kcc == "C:/project\\output"
    assert config.binaries.mangadex_dl == "/usr/bin/mangadex-dl"
    assert config.binaries.kcc_c2e == "/usr/bin/kcc-c2e"
