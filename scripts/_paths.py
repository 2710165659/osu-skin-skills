"""Resolve bundled resources in source and installed layouts."""

from pathlib import Path


def default_db_path() -> Path:
    """Return the bundled osu_skin.db path without using the working directory."""
    module_dir = Path(__file__).resolve().parent
    installed_path = module_dir / "assets" / "osu_skin.db"
    if installed_path.is_file():
        return installed_path
    return module_dir.parent / "assets" / "osu_skin.db"
