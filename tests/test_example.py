from pathlib import Path

from dotkeep.manifest import load

EXAMPLE = Path(__file__).parent.parent / "examples" / "dotfiles"


def test_example_manifest_loads_on_every_platform():
    for platform in ("linux", "macos", "windows"):
        manifest = load(EXAMPLE, platform)
        for entry in manifest.entries:
            assert (EXAMPLE / entry.source).exists(), entry
