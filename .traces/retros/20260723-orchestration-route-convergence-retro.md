# Orchestration Route Convergence

Date: 2026-07-23

Project: calibration

Status: Promoted

## Expected

- Goal: reduce the human time and attention spent polling CI, relaying review
  feedback, and restarting repository work.
- Risk: adopt a scheduler or orchestrator that adds more configuration and
  operating burden than the attention it saves.
- Validation plan: compare native Codex/GitHub capabilities, Scheduled Tasks,
  Symphony, and existing third-party orchestration against a bounded real pull
  request.
- Key assumptions: a recurring schedule might provide the missing bridge, or
  Symphony might need to own the full engineering workflow before any
  continuation benefit was available.

## Actual

- Changes: GitHub Actions and Automatic Codex Review remained native owners of
  validation and review. Symphony stopped at its readiness gates. AO supplied
  the narrower missing lifecycle and was patched for COMMENTED-review refresh
  and reliable long tmux message submission. The tested build was installed as
  a user-level service with one registered repository.
- Validation: source inspection, focused Go tests, a long-message live check,
  a real Automatic Review finding, successful autonomous repair through
  commit, passing canary CI, systemd restart/readback, persisted project config,
  and 13 passing `ao doctor` checks.
- Result: event-to-original-worker continuation is operational on the current
  host. Auto-merge remains disabled. Cross-host and broad cross-repository
  effectiveness remain unproven.

## Delta

- Underestimated: the decisive gap was a small bot-review routing filter plus
  terminal submission behavior, not the absence of a complete engineering
  control plane.
- Overestimated: the need to solve scheduling, issue tracking, staging,
  credentials, workflow schemas, and full repository orchestration before
  testing whether review feedback could resume one worker.
- Surprise: Automatic Codex Review's COMMENTED finding did not change GitHub's
  aggregate review decision, and a successfully delivered long tmux paste
  could still remain unsubmitted in Codex. Final reconstruction also showed
  that `ao doctor` accepting tmux 2.7 did not prove runtime compatibility; AO's
  integration tests require the newer `window-size` option and passed with
  tmux 3.5.

## Rule To Carry Forward

- Future rule: start from the exact state transition that still consumes human
  attention. Preserve native owners on both sides, reuse a maintained engine
  for only the missing bridge, and prove one real event end to end before
  adding scheduling, tracker, deployment, or merge machinery.
- Promote to docs/canon: yes. The decision and reproducible host contract are
  now recorded in `docs/decisions/2026-07-23-ao-review-continuation-adoption.md`
  and `docs/runbooks/agent-orchestrator-review-continuation.md`.
