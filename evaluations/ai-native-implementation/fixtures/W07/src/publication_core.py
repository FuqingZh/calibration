from pathlib import Path


def _prepare_destination(path: Path) -> Path:
    return path.resolve()


def _create_stage_path(path: Path) -> Path:
    return path.with_suffix(".stage")


def _connect_publication(path: Path) -> str:
    return str(path)


def _create_metadata_schema(connection: str) -> str:
    return f"schema:{connection}"


def _publication_metadata(resource: str) -> dict[str, str]:
    return {"resource": resource}


def _write_metadata(metadata: dict[str, str], row: dict[str, object]) -> None:
    metadata["key"] = str(row["key"])


def _validate_publication(metadata: dict[str, str]) -> None:
    if "resource" not in metadata:
        raise ValueError("missing resource")
