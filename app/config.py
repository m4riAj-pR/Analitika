import os
from pathlib import Path


_ENV_LOADED = False


def load_env_file(path: str | os.PathLike[str] | None = None) -> None:
    """Carga variables desde .env para desarrollo local sin pisar el entorno real."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return

    env_path = Path(path) if path else Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        _ENV_LOADED = True
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        if key:
            os.environ[key] = value

    _ENV_LOADED = True


def get_required_env(name: str, description: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} no configurada ({description}). Verifica tu archivo .env.")
    return value
