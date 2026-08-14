from pathlib import Path

import dynamicdb

from .publication_core import (
    _connect_publication,
    _create_metadata_schema,
    _create_stage_path,
    _prepare_destination,
    _publication_metadata,
    _validate_publication,
    _write_metadata,
)


def publish(path: Path, key: str) -> tuple[Path, dict[str, str]]:
    destination = _prepare_destination(path)
    stage = _create_stage_path(destination)
    connection = _connect_publication(stage)
    _create_metadata_schema(connection)
    metadata = _publication_metadata("example")
    row = dynamicdb.fetch_row(key)
    _write_metadata(metadata, row)
    _validate_publication(metadata)
    return destination, metadata
