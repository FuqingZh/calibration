from __future__ import annotations

import hashlib

from tests.support import REPOSITORY_ROOT

ARCHIVE = REPOSITORY_ROOT / "docs/archive/pipeline-conventions"
REFERENCES = REPOSITORY_ROOT / "skills/calibration/references"
SNAPSHOTS = {
    "identifier.md": "128ec173740fbb138430b3c76837952da0ef9de30f9170592601df55997a0951",
    "schema.md": "01bbffe40177b45b15c1139b9490c1d55c6b563c06691808794e429e1a692357",
    "artifact.md": "9271f9c95bd4599897bc6ca222bb2deaab9e66fd3290da809d12bd48a3d21c8f",
    "pipeline-directory-layout.md": (
        "05ac10c81137a145dddbd50e120504631ffe12f5b4cf7412947bf1800a22db9f"
    ),
    "step-to-step-artifact-flow.md": (
        "2475f6c4a96ef1e4b7d9d0ae95bfef874261968864d9910726b14f0da4c07068"
    ),
}


def test_retired_pipeline_snapshots_are_preserved() -> None:
    for name, digest in SNAPSHOTS.items():
        assert hashlib.sha256((ARCHIVE / name).read_bytes()).hexdigest() == digest


def test_retired_paths_redirect_without_active_routing() -> None:
    index = (REFERENCES / "docs_index.md").read_text(encoding="utf-8")
    redirects = {
        "pipeline_directory_layout_specification": "artifact",
        "step_to_step_artifact_flow_specification": "artifact",
        "identifier": "schema",
    }
    for directory, target in redirects.items():
        path = f"docs/schema/{directory}/20260304-v1.1.md"
        pointer = (REFERENCES / path).read_text(encoding="utf-8")
        assert f"](../../../naming/{target}.md)" in pointer
        assert path not in index
