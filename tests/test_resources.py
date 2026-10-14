import importlib.resources
import json

from cloak_turnstile.runner import PATCH_DIR


def test_extension_resources_are_packaged():
    manifest = json.loads((PATCH_DIR / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["manifest_version"] == 3
    content = manifest["content_scripts"][0]
    assert content["world"] == "MAIN"
    assert content["all_frames"] is True
    for name in content["js"]:
        assert (PATCH_DIR / name).is_file()
    root = importlib.resources.files("cloak_turnstile")
    assert root.joinpath("_vendor/turnstile/scripts/solve_agent_browser.py").is_file()
