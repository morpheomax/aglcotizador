from pathlib import Path


def test_project_scaffold_exists() -> None:
    expected_paths = [
        Path("app.py"),
        Path("src/engine"),
        Path("src/bom"),
        Path("src/data"),
        Path("src/exporters"),
        Path("src/models"),
        Path("src/ui"),
        Path("data/raw/calculo_supresion.xlsx"),
    ]

    for path in expected_paths:
        assert path.exists(), f"Missing expected project path: {path}"
