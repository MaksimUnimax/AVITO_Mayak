from pathlib import Path


def test_rf23_transport_has_no_direct_schema_or_dml_imports() -> None:
    root = Path(__file__).parents[2] / "src/mayak/entrypoints/api"
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    assert "mayak.persistence.schema" not in text
    assert ".insert(" not in text
    assert ".update(" not in text
    assert ".delete(" not in text
