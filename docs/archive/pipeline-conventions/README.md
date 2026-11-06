# Retired Pipeline Conventions

These five files preserve the superseded naming and scientific-pipeline
conventions byte for byte. They are historical evidence, not current defaults,
and are outside the installed skill tree.

| Snapshot | Former active path under `skills/calibration/references/` |
| --- | --- |
| [Schema naming](schema.md) | `naming/schema.md` |
| [Artifact naming](artifact.md) | `naming/artifact.md` |
| [Pipeline directory layout](pipeline-directory-layout.md) | `docs/schema/pipeline_directory_layout_specification/20260304-v1.1.md` |
| [Step-to-step artifact flow](step-to-step-artifact-flow.md) | `docs/schema/step_to_step_artifact_flow_specification/20260304-v1.1.md` |
| [Identifier protocol](identifier.md) | `docs/schema/identifier/20260304-v1.1.md` |

Current [schema](../../../skills/calibration/references/naming/schema.md) and
[artifact](../../../skills/calibration/references/naming/artifact.md) guidance
defer concrete conventions to the protocol, workflow engine, and repository.
The old pipeline and identifier paths remain as retirement pointers. Existing
projects may retain their own adopted contracts; retirement does not authorize migration
of their fields, files, directories, or configuration.

The [archive tests](../../../tests/test_pipeline_conventions_archive.py) check
snapshot hashes and current routing. This is a scope and ownership change;
agent quality and downstream project migration have not been evaluated.
