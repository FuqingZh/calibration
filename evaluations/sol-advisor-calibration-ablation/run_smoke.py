#!/usr/bin/env python3
"""Run or reanalyze the registered Sol Advisor and CAL-MIN comparison.

The command-line interface is the supported boundary; module helpers are
implementation details. Raw trajectories, isolated homes, and mutable
workspaces stay outside the public evaluation directory.

Examples:
    The CLI exposes a preflight that spends no model tokens:

    >>> "preflight" in parser().format_help()
    True

Notes:
    Prompt normalization may remove only registered per-run identifiers. Token
    totals combine the parent event stream with persisted auxiliary sessions;
    cached input and reasoning output remain subsets and are never added twice.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import selectors
import shutil
import signal
import subprocess
import sys
import time
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = ROOT.parents[1]
FIXTURE = ROOT / "fixture"
CASE_PATH = ROOT / "case.json"
MANIFEST_PATH = ROOT / "manifest.json"
CONFIGURE_ADVISOR = ROOT / "configure_advisor.ts"
PROXY_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "REQUESTS_CA_BUNDLE",
)
USAGE_KEYS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)


class EvaluationError(RuntimeError):
    """Raised when a frozen input or run contract is invalid."""


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EvaluationError(f"{path}: expected a JSON object")
    return value


def run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: float = 120,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise EvaluationError(
            f"{' '.join(command[:4])} failed ({result.returncode}): {detail}"
        )
    return result


def clean_environment(codex_home: Path, bun_bin: Path) -> dict[str, str]:
    path_parts = [
        str(bun_bin.parent),
        str(Path(sys.executable).parent),
        "/usr/local/bin",
        "/usr/bin",
        "/bin",
    ]
    values = {
        "HOME": str(Path.home()),
        "USER": os.environ.get("USER", "user"),
        "LOGNAME": os.environ.get("LOGNAME", os.environ.get("USER", "user")),
        "LANG": "C.UTF-8",
        "PATH": ":".join(dict.fromkeys(path_parts)),
        "CODEX_HOME": str(codex_home),
    }
    for key in PROXY_KEYS:
        if key in os.environ:
            values[key] = os.environ[key]
    return values


def prepare_home(codex_home: Path, auth_file: Path) -> None:
    codex_home.mkdir(parents=True, mode=0o700)
    os.chmod(codex_home, 0o700)
    (codex_home / "auth.json").symlink_to(auth_file.resolve())
    skills = codex_home / "skills"
    skills.mkdir()
    (skills / "calibration").symlink_to(
        REPOSITORY_ROOT / "skills" / "calibration",
        target_is_directory=True,
    )
    (codex_home / "references").symlink_to(
        REPOSITORY_ROOT / "references",
        target_is_directory=True,
    )
    (codex_home / "docs").symlink_to(
        REPOSITORY_ROOT / "docs",
        target_is_directory=True,
    )


def prepare_workspace(workspace: Path, arm_source: Path) -> None:
    if workspace.exists():
        raise EvaluationError(f"workspace already exists: {workspace}")
    if workspace.resolve().is_relative_to(REPOSITORY_ROOT.resolve()):
        raise EvaluationError(
            "model workspace must be outside the calibration repository tree"
        )
    shutil.copytree(
        FIXTURE, workspace, ignore=shutil.ignore_patterns("PROJECT_AGENTS.md")
    )
    project_contract = (FIXTURE / "PROJECT_AGENTS.md").read_text(encoding="utf-8")
    arm_contract = arm_source.read_text(encoding="utf-8")
    (workspace / "AGENTS.md").write_text(
        arm_contract.rstrip() + "\n\n" + project_contract,
        encoding="utf-8",
    )
    for command in (
        ["git", "init", "-q"],
        ["git", "config", "user.name", "Calibration Evaluation"],
        ["git", "config", "user.email", "evaluation@example.invalid"],
        ["git", "add", "."],
        ["git", "commit", "-q", "-m", "synthetic fixture baseline"],
    ):
        run(command, cwd=workspace)


def changed_paths(workspace: Path) -> list[str]:
    result = run(["git", "status", "--porcelain"], cwd=workspace)
    paths = []
    for line in result.stdout.splitlines():
        paths.append(line[3:].rsplit(" -> ", maxsplit=1)[-1])
    return sorted(paths)


def git_diff(workspace: Path) -> str:
    return run(["git", "diff", "--no-ext-diff", "--unified=0"], cwd=workspace).stdout


def diff_fingerprints(diff: str) -> set[str]:
    path = ""
    values: set[str] = set()
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
        elif path and line[:1] in {"+", "-"} and not line.startswith(("+++", "---")):
            values.add(sha256_text(f"{path}\0{line[0]}\0{line[1:]}"))
    return values


def normalize_prompt(value: object, replacements: dict[str, str]) -> object:
    if isinstance(value, str):
        result = value
        for source, target in sorted(
            replacements.items(), key=lambda item: len(item[0]), reverse=True
        ):
            result = result.replace(source, target)
        return result
    if isinstance(value, list):
        return [normalize_prompt(item, replacements) for item in value]
    if isinstance(value, dict):
        dynamic = {"id", "internal_chat_message_metadata_passthrough"}
        return {
            key: normalize_prompt(item, replacements)
            for key, item in value.items()
            if key not in dynamic
        }
    return value


def summarize_prompt(
    raw: object,
    *,
    replacements: dict[str, str],
    prompt: str,
) -> dict[str, Any]:
    normalized = normalize_prompt(raw, replacements)
    messages = []
    for item in normalized if isinstance(normalized, list) else []:
        messages.append(
            {
                "role": item.get("role") if isinstance(item, dict) else None,
                "sha256": sha256_text(canonical_json(item)),
                "bytes": len(canonical_json(item).encode()),
            }
        )
    return {
        "normalizedSha256": sha256_text(canonical_json(normalized)),
        "messageRecords": messages,
        "promptSha256": sha256_text(prompt),
        "messageCount": len(messages),
        "outerHistoryAbsent": True,
        "captureMode": (
            "structural preflight with workspace-write/on-request; the run uses "
            "workspace-write/automatic review"
        ),
    }


def prompt_record(
    *,
    codex_bin: Path,
    prompt: str,
    workspace: Path,
    codex_home: Path,
    bun_bin: Path,
    output_dir: Path,
) -> dict[str, Any]:
    env = clean_environment(codex_home, bun_bin)
    result = run(
        [
            str(codex_bin),
            "debug",
            "prompt-input",
            "--disable",
            "apps",
            "--disable",
            "remote_plugin",
            "--config",
            'sandbox_mode="workspace-write"',
            "--config",
            'approval_policy="on-request"',
            prompt,
        ],
        cwd=workspace,
        env=env,
    )
    raw = json.loads(result.stdout)
    if "source_thread_id" in canonical_json(
        raw
    ) or "<codex_delegation>" in canonical_json(raw):
        raise EvaluationError("prompt input inherited outer task history")
    (output_dir / "prompt-input.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    replacements = {
        str(workspace): "<WORKSPACE>",
        str(codex_home): "<CODEX_HOME>",
        str(output_dir): "<OUTPUT_DIR>",
    }
    return summarize_prompt(raw, replacements=replacements, prompt=prompt)


def configure_advisor(
    *,
    codex_bin: Path,
    bun_bin: Path,
    advisor_source: Path,
    workspace: Path,
    codex_home: Path,
    model: str,
    effort: str,
) -> dict[str, Any]:
    env = clean_environment(codex_home, bun_bin)
    run(
        [str(codex_bin), "plugin", "marketplace", "add", str(advisor_source), "--json"],
        cwd=workspace,
        env=env,
    )
    run(
        [str(codex_bin), "plugin", "add", "sol-advisor@sol-advisor", "--json"],
        cwd=workspace,
        env=env,
    )
    listed = run([str(codex_bin), "mcp", "list", "--json"], cwd=workspace, env=env)
    servers = json.loads(listed.stdout)
    server = next((item for item in servers if item.get("name") == "sol-advisor"), None)
    if not server:
        raise EvaluationError("installed Sol Advisor MCP server was not discoverable")
    transport = server["transport"]
    server_env = env | {str(key): str(value) for key, value in transport["env"].items()}
    configured = run(
        [
            str(bun_bin),
            str(CONFIGURE_ADVISOR),
            str(transport["args"][0]),
            str(workspace),
            model,
            effort,
        ],
        cwd=workspace,
        env=server_env,
    )
    payload = json.loads(configured.stdout)
    if payload.get("valid") is not True or payload.get("status") != "ready":
        raise EvaluationError(f"Sol Advisor setup did not validate: {payload}")
    return {
        "status": payload["status"],
        "valid": payload["valid"],
        "planDigest": payload["planDigest"],
        "installedRoles": sorted(Path(path).name for path in payload["installed"]),
    }


def stream_model(
    *,
    command: list[str],
    workspace: Path,
    env: dict[str, str],
    output_dir: Path,
    timeout: float,
) -> tuple[int, float, list[dict[str, Any]]]:
    raw_path = output_dir / "trajectory.jsonl"
    timed_path = output_dir / "trajectory-timed.jsonl"
    stderr_path = output_dir / "codex.stderr"
    snapshots: list[dict[str, Any]] = []
    previous_diff = ""
    started = time.monotonic()
    with (
        raw_path.open("w", encoding="utf-8") as raw_stream,
        timed_path.open("w", encoding="utf-8") as timed_stream,
        stderr_path.open("w", encoding="utf-8") as stderr_stream,
    ):
        process = subprocess.Popen(
            command,
            cwd=workspace,
            env=env,
            stdout=subprocess.PIPE,
            stderr=stderr_stream,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
        if process.stdout is None:
            raise EvaluationError("Codex stdout pipe was not created")
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        while True:
            elapsed = time.monotonic() - started
            if elapsed > timeout:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                raise EvaluationError(f"Codex arm exceeded {timeout:.0f} seconds")
            ready = selector.select(timeout=1)
            for key, _ in ready:
                line = key.fileobj.readline()
                if not line:
                    continue
                raw_stream.write(line)
                raw_stream.flush()
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    event = {"type": "invalid-json", "raw": line.rstrip()}
                timed_stream.write(
                    json.dumps(
                        {"elapsedSeconds": time.monotonic() - started, "event": event},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                timed_stream.flush()
                event_type = str(event.get("type", ""))
                item = event.get("item", {}) if isinstance(event, dict) else {}
                if event_type in {"thread.started", "turn.completed"}:
                    print(f"  {event_type}", flush=True)
                elif event_type == "item.completed" and isinstance(item, dict):
                    item_type = item.get("type")
                    if item_type in {
                        "agent_message",
                        "mcp_tool_call",
                        "command_execution",
                    }:
                        print(f"  item.completed:{item_type}", flush=True)
                current_diff = git_diff(workspace)
                if current_diff != previous_diff:
                    snapshots.append(
                        {
                            "elapsedSeconds": time.monotonic() - started,
                            "diffSha256": sha256_text(current_diff),
                            "fingerprints": sorted(diff_fingerprints(current_diff)),
                        }
                    )
                    previous_diff = current_diff
            if process.poll() is not None:
                for line in process.stdout:
                    raw_stream.write(line)
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        event = {"type": "invalid-json", "raw": line.rstrip()}
                    timed_stream.write(
                        json.dumps(
                            {
                                "elapsedSeconds": time.monotonic() - started,
                                "event": event,
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                break
        return process.returncode, time.monotonic() - started, snapshots


def event_items(path: Path) -> Iterable[dict[str, Any]]:
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            yield event


def item_text(item: dict[str, Any]) -> str:
    for key in ("text", "message", "command", "name"):
        value = item.get(key)
        if isinstance(value, str):
            return value
    return ""


def tool_identity(item: dict[str, Any]) -> str:
    return canonical_json(
        {
            key: item[key]
            for key in ("type", "tool", "name", "command", "prompt")
            if key in item
        }
    )


def word_set(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z0-9_.-]+", text.lower()))


def empty_usage() -> dict[str, int]:
    return {key: 0 for key in USAGE_KEYS}


def add_usage(*values: dict[str, int]) -> dict[str, int]:
    return {key: sum(value.get(key, 0) for value in values) for key in USAGE_KEYS}


def observable_metrics(path: Path) -> dict[str, Any]:
    usage = empty_usage()
    summaries: list[str] = []
    agent_messages: list[str] = []
    commands: list[str] = []
    errors: list[str] = []
    compactions = 0
    thread_ids: list[str] = []
    for event in event_items(path):
        event_type = str(event.get("type", ""))
        if "compact" in event_type.lower():
            compactions += 1
        if event_type == "thread.started" and isinstance(event.get("thread_id"), str):
            thread_ids.append(event["thread_id"])
        if event_type == "turn.completed" and isinstance(event.get("usage"), dict):
            for key in usage:
                value = event["usage"].get(key, 0)
                if isinstance(value, int):
                    usage[key] += value
        item = event.get("item")
        if event_type != "item.completed" or not isinstance(item, dict):
            continue
        text = item_text(item)
        if item.get("type") == "reasoning" and text:
            summaries.append(text)
        elif item.get("type") == "agent_message" and text:
            agent_messages.append(text)
        elif item.get("type") in {
            "command_execution",
            "mcp_tool_call",
            "collab_tool_call",
            "collaboration_tool_call",
        }:
            commands.append(tool_identity(item))
        elif item.get("type") == "error" and text:
            errors.append(text)
    observable = summaries + agent_messages[:-1]
    repeated_pairs = 0
    for index, left in enumerate(observable):
        left_words = word_set(left)
        if len(left_words) < 8:
            continue
        for right in observable[index + 1 :]:
            right_words = word_set(right)
            union = left_words | right_words
            if union and len(left_words & right_words) / len(union) >= 0.7:
                repeated_pairs += 1
    message_text = "\n".join(agent_messages)
    calibration_skill_reads = sum(
        1
        for command in commands
        if re.search(
            r"/skills/calibration/SKILL\.md|\$calibration",
            command,
            re.I,
        )
    )
    calibration_announcements = len(
        re.findall(
            r"(?:using|invoking|routed? through) `?\$calibration", message_text, re.I
        )
    )
    calibration_routes = max(calibration_skill_reads, calibration_announcements)
    reference_loads = sum("/references/engineering/" in command for command in commands)
    capsule_labels = (
        "authority:",
        "frozen boundary:",
        "compatibility:",
        "validation:",
        "reopen only if:",
    )
    capsule_count = sum(
        all(label in message.lower() for label in capsule_labels)
        for message in agent_messages
    )
    ao_routes = sum(
        1
        for command in commands
        if re.search(r"(?:^|[\s\"/])ao(?:[\s\".]|$)|mcp[^\n]*ao", command, re.I)
    )
    return {
        "threadIds": thread_ids,
        "parentUsage": usage,
        "reasoningSummaryCount": len(summaries),
        "commentaryCount": max(0, len(agent_messages) - 1),
        "repeatedObservablePairs": repeated_pairs,
        "compactionCount": compactions,
        "calibrationRouteCount": calibration_routes,
        "calibrationSkillReadCount": calibration_skill_reads,
        "calibrationReferenceLoadCount": reference_loads,
        "decisionCapsuleCount": capsule_count,
        "scopeIncrementDecisionCount": 0,
        "reopenEventCount": 0,
        "aoRouteCount": ao_routes,
        "collaborationWaitCount": sum(
            '"tool":"wait"' in command for command in commands
        ),
        "scopeArtifactMentionCount": len(
            re.findall(r"data-diagnostics\.parquet", message_text, re.I)
        ),
        "topLevelErrors": errors,
    }


def auxiliary_sessions(codex_home: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted((codex_home / "sessions").glob("**/*.jsonl")):
        metadata: dict[str, Any] = {}
        context: dict[str, Any] = {}
        usage = empty_usage()
        for event in event_items(path):
            payload = event.get("payload")
            if not isinstance(payload, dict):
                continue
            if event.get("type") == "session_meta":
                metadata = payload
            elif event.get("type") == "turn_context" and not context:
                context = payload
            elif event.get("type") == "event_msg":
                info = payload.get("info")
                if payload.get("type") != "token_count" or not isinstance(info, dict):
                    continue
                total = info.get("total_token_usage")
                if isinstance(total, dict):
                    usage = {
                        key: int(total.get(key, 0))
                        for key in USAGE_KEYS
                        if isinstance(total.get(key, 0), int)
                    }
        source = metadata.get("source")
        subagent = source.get("subagent") if isinstance(source, dict) else None
        spawn = subagent.get("thread_spawn") if isinstance(subagent, dict) else None
        role = metadata.get("agent_role")
        kind = "native-role" if isinstance(spawn, dict) else "guardian"
        sandbox = context.get("sandbox_policy")
        records.append(
            {
                "sessionId": metadata.get("id"),
                "kind": kind,
                "role": role,
                "model": context.get("model"),
                "reasoningEffort": context.get("effort"),
                "sandboxPolicy": (
                    sandbox.get("type") if isinstance(sandbox, dict) else None
                ),
                "approvalPolicy": context.get("approval_policy"),
                "usage": usage,
            }
        )
    return records


def collected_telemetry(output_dir: Path) -> dict[str, Any]:
    telemetry = observable_metrics(output_dir / "trajectory.jsonl")
    sessions = auxiliary_sessions(output_dir / "codex-home")
    auxiliary_usage = add_usage(
        *(
            session["usage"]
            for session in sessions
            if isinstance(session["usage"], dict)
        )
    )
    telemetry["auxiliarySessions"] = sessions
    telemetry["auxiliaryUsage"] = auxiliary_usage
    telemetry["totalObservedUsage"] = add_usage(
        telemetry["parentUsage"],
        auxiliary_usage,
    )
    telemetry["usageCoverage"] = (
        "top-level exec plus every persisted native-role and guardian session in "
        "the fresh isolated Codex home"
    )
    telemetry["advisorRouteCount"] = sum(
        session["kind"] == "native-role" for session in sessions
    )
    return telemetry


def classify_run(
    *,
    arm: dict[str, Any],
    telemetry: dict[str, Any],
    verification: dict[str, Any],
    exit_code: int,
    final_diff: str,
    model: str,
    effort: str,
) -> tuple[list[str], list[str]]:
    critical_failures = []
    protocol_deviations = []
    sessions = telemetry["auxiliarySessions"]
    native_sessions = [
        session for session in sessions if session["kind"] == "native-role"
    ]
    if exit_code:
        critical_failures.append(f"codex_exit_{exit_code}")
    if not verification["passed"]:
        critical_failures.append("final_verification_or_scope_failed")
    if telemetry["aoRouteCount"]:
        critical_failures.append("ao_route_outside_frozen_boundary")
    if "data-diagnostics.parquet" in final_diff:
        critical_failures.append("unrequested_public_artifact")
    if arm["advisor"]:
        if len(native_sessions) < 2:
            critical_failures.append("advisor_native_roles_missing")
        if any(
            session["model"] != model or session["reasoningEffort"] != effort
            for session in native_sessions
        ):
            critical_failures.append("advisor_role_model_or_effort_mismatch")
        if any(
            "exceeded the main prompt context limit" in error
            for error in telemetry["topLevelErrors"]
        ):
            protocol_deviations.append("advisor_skill_truncated_then_read_explicitly")
        if any(
            session["role"] == "sol_advisor_advisor"
            and session["sandboxPolicy"] != "read-only"
            for session in native_sessions
        ):
            protocol_deviations.append("advisor_requested_read_only_but_host_broadened")
    elif native_sessions:
        critical_failures.append("unexpected_native_role_in_no_advisor_arm")
    return critical_failures, protocol_deviations


def verify_workspace(case: dict[str, Any], workspace: Path) -> dict[str, Any]:
    command = [str(part) for part in case["verify"]]
    result = run(command, cwd=workspace, check=False, timeout=180)
    paths = changed_paths(workspace)
    allowed = set(case["allowedChanges"])
    required = set(case["requiredChanges"])
    return {
        "exitCode": result.returncode,
        "passed": result.returncode == 0
        and set(paths) <= allowed
        and required <= set(paths),
        "changedPaths": paths,
        "unexpectedChanges": sorted(set(paths) - allowed),
        "missingRequiredChanges": sorted(required - set(paths)),
        "stdoutTail": "\n".join(result.stdout.splitlines()[-16:]),
        "stderrTail": "\n".join(result.stderr.splitlines()[-16:]),
    }


def run_arm(
    *,
    arm_id: str,
    arm: dict[str, Any],
    case: dict[str, Any],
    model: str,
    effort: str,
    codex_bin: Path,
    bun_bin: Path,
    advisor_source: Path,
    auth_file: Path,
    workspace: Path,
    output_dir: Path,
    timeout: float,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True)
    codex_home = output_dir / "codex-home"
    prepare_home(codex_home, auth_file)
    prepare_workspace(workspace, ROOT / arm["calibration"])
    initial = run(
        [str(part) for part in case["verify"]], cwd=workspace, check=False, timeout=180
    )
    if initial.returncode == 0 or case["initialFailure"] not in initial.stderr:
        raise EvaluationError(
            f"{arm_id}: fixture did not reproduce its registered initial failure"
        )
    advisor_setup = None
    if arm["advisor"]:
        advisor_setup = configure_advisor(
            codex_bin=codex_bin,
            bun_bin=bun_bin,
            advisor_source=advisor_source,
            workspace=workspace,
            codex_home=codex_home,
            model=model,
            effort=effort,
        )
    task = (ROOT / case["task"]).read_text(encoding="utf-8").strip()
    if arm["advisor"]:
        task = (
            (ROOT / case["advisorActivation"]).read_text(encoding="utf-8").strip()
            + "\n\n"
            + task
        )
    prompt = prompt_record(
        codex_bin=codex_bin,
        prompt=task,
        workspace=workspace,
        codex_home=codex_home,
        bun_bin=bun_bin,
        output_dir=output_dir,
    )
    final_message = output_dir / "final-message.txt"
    command = [
        str(codex_bin),
        "exec",
        "--ephemeral",
        "--approve-for-me",
        "--disable",
        "apps",
        "--disable",
        "remote_plugin",
        "--json",
        "--color",
        "never",
        "--model",
        model,
        "--config",
        f'model_reasoning_effort="{effort}"',
        "--cd",
        str(workspace),
        "--output-last-message",
        str(final_message),
        task,
    ]
    exit_code, elapsed, snapshots = stream_model(
        command=command,
        workspace=workspace,
        env=clean_environment(codex_home, bun_bin),
        output_dir=output_dir,
        timeout=timeout,
    )
    final_diff = git_diff(workspace)
    (output_dir / "final.diff").write_text(final_diff, encoding="utf-8")
    (output_dir / "diff-snapshots.json").write_text(
        json.dumps(snapshots, indent=2) + "\n", encoding="utf-8"
    )
    verification = verify_workspace(case, workspace)
    telemetry = collected_telemetry(output_dir)
    final_fingerprints = diff_fingerprints(final_diff)
    first_effective = next(
        (
            snapshot["elapsedSeconds"]
            for snapshot in snapshots
            if final_fingerprints & set(snapshot["fingerprints"])
        ),
        None,
    )
    intermediate = (
        set().union(*(set(snapshot["fingerprints"]) for snapshot in snapshots))
        if snapshots
        else set()
    )
    critical_failures, protocol_deviations = classify_run(
        arm=arm,
        telemetry=telemetry,
        verification=verification,
        exit_code=exit_code,
        final_diff=final_diff,
        model=model,
        effort=effort,
    )
    result = {
        "arm": arm_id,
        "calibration": arm["calibration"],
        "advisor": arm["advisor"],
        "advisorSetup": advisor_setup,
        "requestedModel": model,
        "requestedReasoningEffort": effort,
        "observedBackendModelBuild": None,
        "modelIdentityLimitation": (
            "the CLI exposed the requested model configuration but not a backend "
            "build identity"
        ),
        "prompt": prompt,
        "codexExitCode": exit_code,
        "wallSeconds": elapsed,
        "timeToFirstEffectiveEditSeconds": first_effective,
        "reworkFingerprintCount": len(intermediate - final_fingerprints),
        "finalDiffSha256": sha256_text(final_diff),
        "verification": verification,
        "telemetry": telemetry,
        "criticalFailures": critical_failures,
        "protocolDeviations": protocol_deviations,
        "passedSmokeGate": not critical_failures,
    }
    (output_dir / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


def preflight(
    *, codex_bin: Path, bun_bin: Path, advisor_source: Path, auth_file: Path
) -> dict[str, Any]:
    manifest = read_json(MANIFEST_PATH)
    current_arm = ROOT / "arms/C0-current.AGENTS.md"
    candidate_arm = ROOT / "arms/C1-cal-min.AGENTS.md"
    if sha256_file(current_arm) != manifest["currentArmSourceSha256"]:
        raise EvaluationError("C0 arm hash does not match the registered manifest")
    if sha256_file(candidate_arm) != manifest["candidateArmSourceSha256"]:
        raise EvaluationError("C1 arm hash does not match the registered manifest")
    calibration_tree = run(
        ["git", "rev-parse", "HEAD:skills/calibration"],
        cwd=REPOSITORY_ROOT,
    ).stdout.strip()
    if calibration_tree != manifest["calibrationSkillTree"]:
        raise EvaluationError("Calibration skill changed from the registered tree")
    fixture_hash = sha256_tree(FIXTURE)
    if fixture_hash != manifest["fixtureSha256"]:
        raise EvaluationError("evaluation fixture changed from the registered tree")
    head = run(["git", "rev-parse", "HEAD"], cwd=advisor_source).stdout.strip()
    if head != manifest["solAdvisor"]["commit"]:
        raise EvaluationError(f"Sol Advisor head changed: {head}")
    if run(["git", "status", "--porcelain"], cwd=advisor_source).stdout.strip():
        raise EvaluationError("Sol Advisor source has local changes")
    codex_version = run([str(codex_bin), "--version"], cwd=ROOT).stdout.strip()
    bun_version = run([str(bun_bin), "--version"], cwd=ROOT).stdout.strip()
    if manifest["codexCli"]["version"] not in codex_version:
        raise EvaluationError(f"unexpected Codex CLI version: {codex_version}")
    if bun_version != manifest["bun"]["version"]:
        raise EvaluationError(f"unexpected Bun version: {bun_version}")
    if not auth_file.is_file():
        raise EvaluationError(f"missing Codex auth file: {auth_file}")
    r_result = run(["Rscript", "--version"], cwd=ROOT)
    r_version = r_result.stdout.strip() or r_result.stderr.strip()
    openpyxl = run(
        [sys.executable, "-c", "import openpyxl; print(openpyxl.__version__)"], cwd=ROOT
    ).stdout.strip()
    return {
        "codex": codex_version,
        "bun": bun_version,
        "Rscript": r_version,
        "python": sys.version.split()[0],
        "openpyxl": openpyxl,
        "solAdvisorCommit": head,
        "codexBinarySha256": sha256_file(codex_bin),
        "calibrationSkillTree": calibration_tree,
        "fixtureSha256": fixture_hash,
    }


def prompt_matrix(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_arm = {str(result["arm"]): result for result in results}
    if set(by_arm) != {"C0-A0", "C1-A0", "C0-A1", "C1-A1"}:
        return {"checked": False, "valid": None, "comparisons": []}
    contracts = (
        ("C0-A0", "C1-A0", {3}),
        ("C0-A1", "C1-A1", {3}),
        ("C0-A0", "C0-A1", {0, 4}),
        ("C1-A0", "C1-A1", {0, 4}),
    )
    comparisons = []
    for left, right, expected in contracts:
        left_records = by_arm[left]["prompt"]["messageRecords"]
        right_records = by_arm[right]["prompt"]["messageRecords"]
        limit = max(len(left_records), len(right_records))
        actual = {
            index
            for index in range(limit)
            if index >= len(left_records)
            or index >= len(right_records)
            or left_records[index]["sha256"] != right_records[index]["sha256"]
        }
        comparisons.append(
            {
                "left": left,
                "right": right,
                "expectedDifferentMessageIndexes": sorted(expected),
                "actualDifferentMessageIndexes": sorted(actual),
                "valid": actual == expected,
            }
        )
    return {
        "checked": True,
        "valid": all(item["valid"] for item in comparisons),
        "comparisons": comparisons,
    }


def analyze_existing(run_root: Path, workspace_root: Path) -> dict[str, Any]:
    source = read_json(run_root / "summary.json")
    manifest = read_json(MANIFEST_PATH)
    run_id = str(source["runId"])
    results = []
    for original in source["results"]:
        arm_id = str(original["arm"])
        arm = manifest["arms"][arm_id]
        output_dir = run_root / arm_id
        workspace = workspace_root / run_id / arm_id
        result = dict(original)
        telemetry = collected_telemetry(output_dir)
        final_diff = (output_dir / "final.diff").read_text(encoding="utf-8")
        model = str(result["requestedModel"])
        effort = str(result["requestedReasoningEffort"])
        critical, deviations = classify_run(
            arm=arm,
            telemetry=telemetry,
            verification=result["verification"],
            exit_code=int(result["codexExitCode"]),
            final_diff=final_diff,
            model=model,
            effort=effort,
        )
        task = (ROOT / read_json(CASE_PATH)["task"]).read_text(encoding="utf-8").strip()
        if arm["advisor"]:
            activation = (
                (ROOT / read_json(CASE_PATH)["advisorActivation"])
                .read_text(encoding="utf-8")
                .strip()
            )
            task = activation + "\n\n" + task
        raw_prompt = json.loads(
            (output_dir / "prompt-input.json").read_text(encoding="utf-8")
        )
        result["prompt"] = summarize_prompt(
            raw_prompt,
            replacements={
                str(workspace): "<WORKSPACE>",
                str(output_dir / "codex-home"): "<CODEX_HOME>",
                str(output_dir): "<OUTPUT_DIR>",
            },
            prompt=task,
        )
        result["telemetry"] = telemetry
        result["criticalFailures"] = critical
        result["protocolDeviations"] = deviations
        result["passedSmokeGate"] = not critical
        (output_dir / "result.reanalyzed.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        results.append(result)
    matrix = prompt_matrix(results)
    arm_gates = all(result["passedSmokeGate"] for result in results)
    summary = dict(source)
    summary["results"] = results
    summary["promptMatrix"] = matrix
    summary["allArmCriticalGatesPassed"] = arm_gates
    summary["allSmokeGatesPassed"] = arm_gates and matrix["valid"] is not False
    summary["reanalyzedWithCurrentHarness"] = True
    (run_root / "summary.reanalyzed.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def smoke(args: argparse.Namespace) -> int:
    case = read_json(CASE_PATH)
    manifest = read_json(MANIFEST_PATH)
    versions = preflight(
        codex_bin=args.codex_bin,
        bun_bin=args.bun_bin,
        advisor_source=args.advisor_source,
        auth_file=args.auth_file,
    )
    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    output_root = args.output_root / run_id
    workspace_root = args.workspace_root / run_id
    if output_root.exists() or workspace_root.exists():
        raise EvaluationError("generated run identity already exists")
    output_root.mkdir(parents=True)
    workspace_root.mkdir(parents=True)
    requested_order = args.order or manifest["smokeOrder"]
    order = [arm for arm in requested_order if arm in args.arms]
    if set(order) != set(args.arms) or len(order) != len(args.arms):
        raise EvaluationError("run order must contain every selected arm exactly once")
    print(f"run_id={run_id}", flush=True)
    print(f"order={','.join(order)}", flush=True)
    results = []
    for arm_id in order:
        print(f"[{arm_id}] starting", flush=True)
        result = run_arm(
            arm_id=arm_id,
            arm=manifest["arms"][arm_id],
            case=case,
            model=args.model,
            effort=args.effort,
            codex_bin=args.codex_bin,
            bun_bin=args.bun_bin,
            advisor_source=args.advisor_source,
            auth_file=args.auth_file,
            workspace=workspace_root / arm_id,
            output_dir=output_root / arm_id,
            timeout=args.arm_timeout,
        )
        results.append(result)
        print(
            f"[{arm_id}] gate={'pass' if result['passedSmokeGate'] else 'fail'} "
            f"wall={result['wallSeconds']:.1f}s",
            flush=True,
        )
    matrix = prompt_matrix(results)
    arm_gates = all(result["passedSmokeGate"] for result in results)
    all_gates = arm_gates and matrix["valid"] is not False
    summary = {
        "schemaVersion": 1,
        "runId": run_id,
        "phase": args.phase,
        "repetition": args.repetition,
        "startedFromFreshContexts": True,
        "versions": versions,
        "armOrder": order,
        "results": results,
        "promptMatrix": matrix,
        "allArmCriticalGatesPassed": arm_gates,
        "allSmokeGatesPassed": all_gates,
        "officialRepetitionsAuthorized": args.phase == "smoke" and all_gates,
        "lunaArmRun": False,
    }
    (output_root / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"summary={output_root / 'summary.json'}", flush=True)
    return 0 if all_gates else 2


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    subparsers = value.add_subparsers(dest="command", required=True)
    for name in ("preflight", "smoke", "analyze"):
        child = subparsers.add_parser(name)
        if name in {"preflight", "smoke"}:
            child.add_argument("--codex-bin", type=Path, required=True)
            child.add_argument("--bun-bin", type=Path, required=True)
            child.add_argument("--advisor-source", type=Path, required=True)
            child.add_argument("--auth-file", type=Path, required=True)
        if name == "smoke":
            child.add_argument("--output-root", type=Path, required=True)
            child.add_argument("--workspace-root", type=Path, required=True)
            child.add_argument("--model", default="gpt-5.6-sol")
            child.add_argument("--effort", default="max")
            child.add_argument("--arm-timeout", type=float, default=900)
            child.add_argument(
                "--phase",
                choices=("smoke", "official"),
                default="smoke",
            )
            child.add_argument("--repetition", type=int, default=0)
            child.add_argument(
                "--arms",
                nargs="+",
                choices=("C0-A0", "C1-A0", "C0-A1", "C1-A1"),
                default=("C0-A0", "C1-A0", "C0-A1", "C1-A1"),
            )
            child.add_argument(
                "--order",
                nargs="+",
                choices=("C0-A0", "C1-A0", "C0-A1", "C1-A1"),
            )
        elif name == "analyze":
            child.add_argument("--run-root", type=Path, required=True)
            child.add_argument("--workspace-root", type=Path, required=True)
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "analyze":
            result = analyze_existing(args.run_root, args.workspace_root)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["allSmokeGatesPassed"] else 2
        if args.command == "preflight":
            result = preflight(
                codex_bin=args.codex_bin,
                bun_bin=args.bun_bin,
                advisor_source=args.advisor_source,
                auth_file=args.auth_file,
            )
            print(json.dumps(result, indent=2))
            return 0
        return smoke(args)
    except (
        EvaluationError,
        OSError,
        subprocess.TimeoutExpired,
        json.JSONDecodeError,
    ) as error:
        print(json.dumps({"state": "failed", "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
