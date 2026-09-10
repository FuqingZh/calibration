# Chinese Humanizer On-Demand Trial

Status: accepted for an explicitly invoked trial; not a default writing policy.

This portable decision does not assert installation in any particular clone or
Codex home. Live installation and removal state belong to that home's private
`INSTALLATION.json` and installation receipt; inspect them before claiming
availability. The verification below records the original setup event only.

## Source And Trial Setup

- Repository: [holygeek00/humanizer-zh-cn](https://github.com/holygeek00/humanizer-zh-cn).
- Pinned commit: `401e372eeb1a91045d15ec21c2d13b9d0f7842ea`.
- Upstream package version: `2.9.1-zh.2`; installed skill name: `humanizer-zh`.
- License: [MIT at the pinned commit](https://github.com/holygeek00/humanizer-zh-cn/blob/401e372eeb1a91045d15ec21c2d13b9d0f7842ea/LICENSE), copyright Siqi Chen. The installed package retains the license, attribution, localization notes, and upstream links.
- Installation uses the system `skill-installer` helper with repository
  `holygeek00/humanizer-zh-cn`, `--ref` set to the full commit above,
  `--path . --name humanizer-zh`, and the selected personal skills directory.
  Git mode was used after download-mode certificate validation failed; TLS
  verification was not disabled. Root-path sparse checkout omitted nested
  resources, so the installed checkout was fully materialized at the same SHA.

This is a separately managed external skill. Calibration records adoption;
its installer arrays, core references, and global instructions do not load or
install Humanizer. No upstream source is vendored in this repository.

## Invocation And Local Adaptation

Use only when the user explicitly requests Chinese copy review, removal of AI
writing mannerisms, or `$humanizer-zh`. Ordinary answers and unrelated task
outputs do not activate it. Respect the requested text scope and preserve
facts, technical terms, and supplied voice samples.

The trial installation contract requires `agents/openai.yaml` to set `policy.allow_implicit_invocation` to
`false`. A short local scope paragraph follows the title in `SKILL.md`; the
remaining upstream body is unchanged. These are installation adaptations, not
a new upstream release. Before adaptation, the installed skill body matched
the frozen experiment source byte for byte.

Each trial installation retains `INSTALLATION.json`, which records the source SHA, original and installed
file hashes, the two local adaptations, and the evidence locator. A private
installation receipt retains the original files and source Git metadata. Future
updates require an explicit decision and must preserve the invocation policy;
do not track upstream main automatically.

## Blind Evaluation Evidence

Evidence owner: the `design_skeleton` project, document
`website/docs/research/20260909-copy-blind-readout.md`, updated after user voting
on 2026-09-10. The user-supplied experiment directory is retained privately;
the installation receipt identifies the readout and its SHA-256. Private votes
and sample mappings are not copied into the public calibration repository.

The readout, frozen configuration, and private vote resolution were read back:

| Task | Preferred sample | Arm | Repeat |
| --- | --- | --- | --- |
| Homepage introduction | 04 | Chinese Humanizer | 1 |
| neatxlsx mechanism explanation | 06 | Chinese Humanizer | 1 |
| Bio Plot execution explanation | 11 | Chinese Humanizer | 1 |

The experiment generated 18 outputs: three arms, three tasks, two repeats.
Invocation configuration specified `gpt-6-astra` with `medium` effort; server
model routing was not independently exposed. All task favorites came from
Humanizer, but repeat 2 was not independently ranked. This supports the user's
limited trial decision, not stable superiority or six Humanizer wins.

Selected outputs still contained edits the user disliked, including weakening
precise technical terminology and adding unnecessary explanatory narration.
Preserve those project-specific corrections in their owning project; preference
for an output is not permission to copy every sentence. Common defensive prose
may have been induced by shared input mixing background constraints with required
page content. Fact review was performed by the original primary assistant,
without an independent domain reviewer.

The earlier readout deferred installation. The user's explicit instruction in
this task now authorizes the pinned on-demand trial; it does not change that
experiment's evidence or authorize automatic webpage edits. Repeated blind
performance remains a prerequisite for considering long-term default adoption.

## Removal And Validation

To uninstall, locate `humanizer-zh` inside the personal skills directory used
for installation, check its `INSTALLATION.json` identity, and move that entire
directory outside all skill-discovery roots. Retaining it privately makes
removal reversible and preserves the license and receipt. Do not remove another
home's copy or an installation whose identity has changed without inspecting it.
Calibration's normal installer does not recreate this independent trial entry.

At the original trial setup, installation verification covered the exact commit, complete tracked source
tree, frozen evaluation-body equality, retained license, local scope paragraph,
and explicit-invocation metadata. The upstream package validator passed after
adaptation. Repository checks cover this adoption record and navigation only;
no new model comparison, Claude plugin validation, website change, or publication
was performed. Runtime invocation isolation remains to be observed in fresh use.
