from __future__ import annotations

import hashlib
import json
from pathlib import Path
from statistics import median
from typing import cast

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVALUATION_ROOT = REPOSITORY_ROOT / "evaluations" / "sol-advisor-calibration-ablation"


def load_object(path: Path) -> dict[str, object]:
    value = cast(object, json.loads(path.read_text(encoding="utf-8")))
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(
        item
        for item in root.rglob("*")
        if item.is_file() and "__pycache__" not in item.parts and item.suffix != ".pyc"
    ):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def test_ablation_checksum_inventory_is_complete_and_valid() -> None:
    checksum_path = EVALUATION_ROOT / "SHA256SUMS"
    recorded: dict[str, str] = {}
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", maxsplit=1)
        assert relative not in recorded
        recorded[relative] = digest

    expected = {
        path.relative_to(EVALUATION_ROOT).as_posix()
        for path in EVALUATION_ROOT.rglob("*")
        if path.is_file()
        and path != checksum_path
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    }
    assert set(recorded) == expected
    assert all(
        sha256_file(EVALUATION_ROOT / relative) == digest
        for relative, digest in recorded.items()
    )


def test_ablation_frozen_sources_match_manifest() -> None:
    manifest = load_object(EVALUATION_ROOT / "manifest.json")
    current = EVALUATION_ROOT / "arms" / "C0-current.AGENTS.md"
    candidate = EVALUATION_ROOT / "arms" / "C1-cal-min.AGENTS.md"

    assert sha256_file(current) == manifest["currentArmSourceSha256"]
    assert sha256_file(candidate) == manifest["candidateArmSourceSha256"]
    assert sha256_tree(EVALUATION_ROOT / "fixture") == manifest["fixtureSha256"]
    evidence = load_object(EVALUATION_ROOT / "runs.json")
    source = cast(dict[str, object], evidence["source"])
    assert source["distributableFixtureSha256"] == manifest["fixtureSha256"]
    assert len(current.read_text(encoding="utf-8").split()) == 1106
    assert len(candidate.read_text(encoding="utf-8").split()) == 489


def test_ablation_results_cover_three_complete_factorial_repetitions() -> None:
    evidence = load_object(EVALUATION_ROOT / "runs.json")
    runs = cast(list[dict[str, object]], evidence["runs"])
    expected = {
        (repetition, arm)
        for repetition in (1, 2, 3)
        for arm in ("C0-A0", "C1-A0", "C0-A1", "C1-A1")
    }

    assert evidence["schemaVersion"] == 1
    assert evidence["decision"] == (
        "reject-cal-min-as-tested-and-do-not-default-sol-advisor-for-bounded-local-repair"
    )
    assert {(run["repetition"], run["arm"]) for run in runs} == expected
    assert all(run["passed"] is True for run in runs)
    assert all(run["criticalFailures"] == [] for run in runs)
    assert all(run["changedPaths"] == ["src/wgcna_worker.R"] for run in runs)

    for run in runs:
        tokens = cast(dict[str, int], run["tokens"])
        observable = cast(dict[str, int], run["observable"])
        routes = cast(dict[str, int], run["routes"])
        assert tokens["total"] == tokens["input"] + tokens["output"]
        assert 0 <= tokens["cachedInput"] <= tokens["input"]
        assert 0 <= tokens["reasoningOutput"] <= tokens["output"]
        assert observable["repeatedPairs"] == 0
        assert observable["compactions"] == 0
        assert observable["reworkFingerprints"] == 0
        assert observable["scopeArtifactMentions"] == 0
        assert routes["ao"] == 0


def test_ablation_summary_arithmetic_recomputes_from_per_run_evidence() -> None:
    evidence = load_object(EVALUATION_ROOT / "runs.json")
    runs = cast(list[dict[str, object]], evidence["runs"])
    recorded_medians = cast(dict[str, dict[str, float | int]], evidence["medians"])
    contrasts = cast(dict[str, dict[str, object]], evidence["contrasts"])

    def measures(run: dict[str, object]) -> dict[str, float | int]:
        tokens = cast(dict[str, int], run["tokens"])
        observable = cast(dict[str, int], run["observable"])
        return {
            "wallSeconds": cast(float, run["wallSeconds"]),
            "timeToFirstEffectiveEditSeconds": cast(
                float, run["timeToFirstEffectiveEditSeconds"]
            ),
            "inputTokens": tokens["input"],
            "outputTokens": tokens["output"],
            "totalTokens": tokens["total"],
            "commentary": observable["commentary"],
        }

    by_repetition_and_arm = {
        (cast(int, run["repetition"]), cast(str, run["arm"])): run for run in runs
    }
    for arm, recorded in recorded_medians.items():
        arm_measures = [measures(run) for run in runs if run["arm"] == arm]
        expected = {
            name: round(float(median(values)), 3)
            if name.endswith("Seconds")
            else int(median(values))
            for name in recorded
            for values in ([item[name] for item in arm_measures],)
        }
        assert recorded == expected

    paired_metrics = (
        "wallSeconds",
        "timeToFirstEffectiveEditSeconds",
        "inputTokens",
        "totalTokens",
        "commentary",
    )
    for contrast in contrasts.values():
        candidate = cast(str, contrast["candidateArm"])
        reference = cast(str, contrast["referenceArm"])
        expected_pairs: list[dict[str, float | int]] = []
        for repetition in (1, 2, 3):
            candidate_values = measures(by_repetition_and_arm[(repetition, candidate)])
            reference_values = measures(by_repetition_and_arm[(repetition, reference)])
            pair: dict[str, float | int] = {"repetition": repetition}
            for name in paired_metrics:
                delta = candidate_values[name] - reference_values[name]
                pair[name] = (
                    round(float(delta), 3) if name.endswith("Seconds") else delta
                )
            expected_pairs.append(pair)

        assert contrast["pairedDeltas"] == expected_pairs
        recorded_delta = cast(dict[str, float | int], contrast["medianDelta"])
        expected_delta = {
            name: round(float(median(pair[name] for pair in expected_pairs)), 3)
            if name.endswith("Seconds")
            else int(median(pair[name] for pair in expected_pairs))
            for name in paired_metrics
        }
        assert recorded_delta == expected_delta


def test_ablation_prompt_and_role_evidence_matches_arm_contract() -> None:
    evidence = load_object(EVALUATION_ROOT / "runs.json")
    protocol = cast(dict[str, object], evidence["protocol"])
    runs = cast(list[dict[str, object]], evidence["runs"])

    assert protocol["promptMatrixValidEveryRepetition"] is True
    assert protocol["backendBuildIdentityExposed"] is False
    assert protocol["lunaArmRun"] is False

    for arm in ("C0-A0", "C1-A0", "C0-A1", "C1-A1"):
        arm_runs = [run for run in runs if run["arm"] == arm]
        assert len({run["promptSha256"] for run in arm_runs}) == 1
        for run in arm_runs:
            routes = cast(dict[str, int], run["routes"])
            roles = cast(list[dict[str, object]], run["roleSessions"])
            if arm.endswith("A1"):
                assert routes["advisorNativeRoles"] == 2
                assert len(roles) == 2
                assert {role["model"] for role in roles} == {"gpt-5.6-sol"}
                assert {role["reasoningEffort"] for role in roles} == {"max"}
                assert {role["sandboxPolicy"] for role in roles} == {"workspace-write"}
            else:
                assert routes["advisorNativeRoles"] == 0
                assert roles == []
            assert routes["calibration"] == int(arm.startswith("C1"))


def test_ablation_decision_follows_directional_efficiency_evidence() -> None:
    evidence = load_object(EVALUATION_ROOT / "runs.json")
    contrasts = cast(dict[str, dict[str, object]], evidence["contrasts"])
    results = (EVALUATION_ROOT / "results.md").read_text(encoding="utf-8")

    for name in (
        "calMinWithoutAdvisor",
        "calMinWithAdvisor",
        "advisorWithCurrentCalibration",
        "advisorWithCalMin",
    ):
        delta = cast(dict[str, float], contrasts[name]["medianDelta"])
        assert delta["wallSeconds"] > 0
        assert delta["timeToFirstEffectiveEditSeconds"] > 0
        assert delta["totalTokens"] > 0

    assert "Reject `CAL-MIN` as tested" in results
    assert "do not enable Sol Advisor by default" in results
    assert "separate Sol-to-Luna arm was not run" in results
