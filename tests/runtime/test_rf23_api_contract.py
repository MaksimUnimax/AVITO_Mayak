from pathlib import Path


def test_api_process_and_factory_are_present() -> None:
    root = Path(__file__).parents[2]
    assert (root / "src/mayak/runtime/api.py").is_file()
    assert (root / "src/mayak/entrypoints/api/application.py").is_file()
    assert (root / "src/mayak/runtime/rf23_composition.py").is_file()


def test_compose_keeps_loopback_publication_and_internal_bind() -> None:
    compose = (Path(__file__).parents[2] / "compose.yaml").read_text(encoding="utf-8")
    assert "127.0.0.1:${MAYAK_API_HOST_PORT:-18085}:8000/tcp" in compose
    assert "MAYAK_API_BIND_HOST: 0.0.0.0" in compose
    postgres = compose.split("\n  mayak-postgres:\n", 1)[1].split(
        "\n  mayak-db-bootstrap:\n", 1
    )[0]
    assert "ports:" not in postgres
