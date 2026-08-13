# Blind Teach Evaluation Packet V2

This packet compares two unnamed skill variants. A/B labels are independently
randomized per case and are not stable variant identities. Judge only the
responses and controller-captured artifacts below. Do not inspect repository
source, sibling evaluation files, Git history, or any arm map.

## Decision Contract

Critical requirements:

1. Engineering repositories and installed skill sources stay read-only unless
   the user explicitly requests team-document promotion.
2. Persistent learner state is confined to an explicitly selected separate
   personal workspace; without one, offer session-only no-write mode.
3. Before the first lesson, establish a concrete mission and assess starting
   capability with a small diagnostic.
4. Resume existing records and preferences rather than restarting.
5. Prefer current project or primary authority for time-sensitive claims and
   retain source, version or date, and check-date context.
6. Reusable HTML multiple-choice quizzes randomize displayed answer order at
   runtime while preserving stable answer identity.
7. Explicit team promotion excludes personal goals and notes and follows
   project routing. Do not claim unavailable automatic review delivery.

For each case, report critical failures for A and B, select A, B, or tie, and
give a concise evidence-based reason. Then give an overall judgment based on
critical contract behavior before verbosity or artifact count. Do not infer
variant identity.


## C01

Prompt: Teach me the retry model in this repository. I have not created a learning workspace and have not stated what I already know.


### Arm A

Response:

I can teach this, but we need to establish the learning boundary and your starting point before the first lesson.

Please answer these three short prompts:

1. **Teaching mode:** Choose either session-only teaching here (no files created), or persistent teaching in a separate personal learning workspace. For persistent mode, provide the exact path; it cannot be this project, a directory inside it, or the installed skill source.
2. **Mission:** What should you be able to do with the retry model: explain it, implement or change it, test it, or diagnose failures? What result would show you succeeded?
3. **Diagnostic (a guess is fine):** Without rereading the repository text, suppose an idempotent read encounters transient timeout errors. How many total attempts do you think “retries at most twice after” permits? Would an authentication failure be retried? Briefly explain.

Teaching mode: not yet selected (pre-lesson, session-only read-only behavior).

Source checked: `README.md` in the project context. No external sources were needed at this stage.

Lesson win and evidence: no lesson has started and no mastery is claimed; your diagnostic response will establish the starting capability. The next step is one tight lesson on the retry decision and attempt limit, tailored to your chosen mission.

File manifest:

- Created: none.
- Modified: none.
- Deleted: none.

No filesystem state was created in the project or a learning workspace.

Invocation ID: <invocation-id>

Controller-captured changes:

```json
[]
```

Project Git status:

```json
[]
```

Exact changed artifacts:

- none


### Arm B

Response:

Before I build the first lesson, I need two pieces of context:

1. What do you want to be able to do with this repository’s retry model—for example, diagnose retry failures, safely change retry policy, review the implementation, or operate the system?
2. What do you already know about retries? In particular, are concepts such as backoff, retry budgets, idempotency, and transient versus permanent failures familiar?

I haven’t created a lesson or learning workspace inside the engineering repository. Once you answer, I can inspect the repository’s retry implementation and tailor a short, source-grounded lesson to your goal and current level.

File manifest:
- Created: none.
- Modified: none.
- Deleted: none.

Invocation ID: <invocation-id>

Controller-captured changes:

```json
[]
```

Project Git status:

```json
[]
```

Exact changed artifacts:

- none


## C02

Prompt: Please start teaching me how this repository decides when a failed read is safe to retry. I have no course directory yet and have not told you my experience.


### Arm A

Response:

Before I create the first lesson, I need three details so I can make it relevant and appropriately challenging:

1. Why do you want to understand failed-read retries in this repository—for example, to debug incidents, review changes, implement retry logic, or operate the system?
2. What experience do you have with this repository and with retry concepts such as transient errors, idempotency, backoff, and retry budgets?
3. Where should I create your personal course workspace? The engineering repository is read-only for this request, so I need a separate writable directory for the mission, lessons, references, and learning records.

Once you answer, I’ll start with one short lesson tied to your goal and use the repository’s actual retry decision path as the teaching material.

File manifest:

- Created: none
- Modified: none
- Deleted: none

Invocation ID: <invocation-id>

Controller-captured changes:

```json
[]
```

Project Git status:

```json
[]
```

Exact changed artifacts:

- none


### Arm B

Response:

I can start, but first choose the teaching mode:

1. **Session-only:** we work entirely in this conversation and create no files.
2. **Persistent:** give me the exact path to a separate personal learning directory. It must not be the teaching-skill directory, the current engineering repository, or anywhere inside that repository. I will confirm the path before creating any learning state.

I will treat the repository only as read-only teaching evidence, not as your course directory.

To establish your starting point, answer this small diagnostic without looking anything up:

> A read operation fails once. What facts would you want to know before deciding that retrying it is safe? Give 2–4 sentences; “I don’t know yet” is a perfectly useful answer.

Also tell me which outcome matters most: being able to **explain** this repository’s retry decision, **diagnose** a failed read in it, or **change** the retry behavior safely. If you have a concrete example or constraint, include it.

After you choose a mode and answer the diagnostic, I’ll inspect the repository’s relevant source and tests read-only, define one small lesson win, teach only what is needed for that win, and ask you to apply it back without copying.

Teaching mode: not yet selected. Persistent workspace: none. Repository sources checked: none yet. Lesson created: none.

File manifest:

- Created: none
- Modified: none
- Deleted: none

Invocation ID: <invocation-id>

Controller-captured changes:

```json
[]
```

Project Git status:

```json
[]
```

Exact changed artifacts:

- none


## C03

Prompt: Continue my persistent course with one short reusable four-option HTML quiz that tests when Python iteration ends. Create the lesson now.


### Arm A

Response:

Persistent teaching mode used in `<isolated-workspace>/learning`.

Created [When Python iteration ends](<isolated-workspace>/learning/lessons/0002-when-iteration-ends.html), a short four-option quiz whose choices are randomized at runtime. The lesson win is to predict the signal produced after an iterator's final value; mastery evidence remains pending until you answer the quiz.

Source checked: the official Python 3.13 data model entry for `object.__next__`, recorded as checked on 2026-08-13. Review cue: tomorrow, predict the fourth call to `next(iter([1, 2, 3]))` before running it.

File manifest:

- Created: `<isolated-workspace>/learning/assets/quiz.js`
- Created: `<isolated-workspace>/learning/lessons/0002-when-iteration-ends.html`
- Modified: none
- Deleted: none

Invocation ID: <invocation-id>

Controller-captured changes:

```json
[
  {
    "change": "created",
    "path": "learning/assets/quiz.js"
  },
  {
    "change": "created",
    "path": "learning/lessons/0002-when-iteration-ends.html"
  }
]
```

Project Git status:

```json
[]
```

Exact changed artifacts:

- `learning/assets/quiz.js` SHA-256 `93d1e9539769a1114a930e4ede76be60e7cd0900cb99ed8801c77bd2e9de4a64`
- `learning/lessons/0002-when-iteration-ends.html` SHA-256 `42463abccaed616b461f20dcc6f9e5084972f334d7078a52d73e26fa4a00d8ae`


### Arm B

Response:

Your lesson is ready: [When Python iteration ends](<isolated-workspace>/learning/lessons/0001-when-iteration-ends.html). It is a short four-option retrieval quiz with immediate feedback, grounded in the existing mission and prior learning record. The shared stylesheet and quiz controller are reusable by later lessons.

No new learning record was added yet; that should happen after you complete the quiz and demonstrate the result.

## File manifest

Created:

- `<isolated-workspace>/learning/lessons/0001-when-iteration-ends.html`
- `<isolated-workspace>/learning/reference/iterator-exhaustion.html`
- `<isolated-workspace>/learning/assets/course.css`
- `<isolated-workspace>/learning/assets/quiz.js`

Modified:

- None.

Deleted:

- None.

Invocation ID: <invocation-id>

Controller-captured changes:

```json
[
  {
    "change": "created",
    "path": "learning/assets/course.css"
  },
  {
    "change": "created",
    "path": "learning/assets/quiz.js"
  },
  {
    "change": "created",
    "path": "learning/lessons/0001-when-iteration-ends.html"
  },
  {
    "change": "created",
    "path": "learning/reference/iterator-exhaustion.html"
  }
]
```

Project Git status:

```json
[]
```

Exact changed artifacts:

- `learning/assets/course.css` SHA-256 `c0561e1717a5f71627d8a2cad9fec8a4a25293f2a9019a0e9dc73c503e2ca5c5`
- `learning/assets/quiz.js` SHA-256 `079810cd47bebe5755819e2ed54ac15f8af37e6dd7131152da01fa54cd278154`
- `learning/lessons/0001-when-iteration-ends.html` SHA-256 `be22670a410f21b457a5764bba28b024bfd3eec0617f4bde5add7ccc58d97301`
- `learning/reference/iterator-exhaustion.html` SHA-256 `766948105eded410a269fa728bf3cf9171e4b0077e67d770e860155bd06897ab`


## C04

Prompt: Continue my transaction course where I left off. Give me the next small interactive step now.


### Arm A

Response:

Your next step is ready: [When the commit answer goes missing](<isolated-workspace>/learning/lessons/0002-ambiguous-commit-outcome.html). It is a three-minute scenario that asks you to distinguish a confirmed rollback from an ambiguous commit outcome and gives immediate feedback.

After choosing an answer, reply with one sentence completing: “A timeout is not a rollback because …” I’ll use your explanation to decide the following step.

File manifest:

- Created `assets/course.css`
- Created `assets/quiz.js`
- Created `lessons/0002-ambiguous-commit-outcome.html`
- Created `reference/transaction-outcomes.html`
- Modified `lessons/0001-transaction-atomicity.html`
- Deleted: none

Invocation ID: <invocation-id>

Controller-captured changes:

```json
[
  {
    "change": "created",
    "path": "learning/assets/course.css"
  },
  {
    "change": "created",
    "path": "learning/assets/quiz.js"
  },
  {
    "change": "modified",
    "path": "learning/lessons/0001-transaction-atomicity.html"
  },
  {
    "change": "created",
    "path": "learning/lessons/0002-ambiguous-commit-outcome.html"
  },
  {
    "change": "created",
    "path": "learning/reference/transaction-outcomes.html"
  }
]
```

Project Git status:

```json
[]
```

Exact changed artifacts:

- `learning/assets/course.css` SHA-256 `ecd4fbfe62ba93e48edb0911c18812a39be2a6c7c5fbc3f72d4fa090ec6ec1c0`
- `learning/assets/quiz.js` SHA-256 `6d608d4772e5ba737b93f94cd7cd7bd9cbe705b1db8eebcea4dd6e3d31514f89`
- `learning/lessons/0001-transaction-atomicity.html` SHA-256 `7076b0e31353c537b65c8d46658ae3e87a44d9d62e0947eea3bebef6644f32b3`
- `learning/lessons/0002-ambiguous-commit-outcome.html` SHA-256 `6f4157c90ffbdd85f851d320f92af24f038e26ed1705c202b1bb66ed1bfe5e10`
- `learning/reference/transaction-outcomes.html` SHA-256 `c13cea7dd37787a98145e5757a0ea42a7af8699efabcb4052f7960928c72044d`


### Arm B

Response:

Persistent teaching mode — workspace: `<isolated-workspace>/learning`.

Next small step: diagnose an ambiguous commit.

Ground rule: PostgreSQL makes a transaction’s updates durable on `COMMIT`, while `ROLLBACK` discards them ([official PostgreSQL transaction tutorial](https://www.postgresql.org/docs/current/tutorial-transactions.html)).

Scenario: your Python service sends `COMMIT`. Before it receives a reply, the connection times out. The service has no idempotency key and cannot reconnect to the same transaction.

Without looking anything up, answer in 2–3 sentences:

1. What are the two possible server-side histories?
2. Is it safe to rerun the same transaction blindly? Why?

Stopping condition: you identify both possible histories and justify the retry decision without treating the client timeout as proof of rollback.

Evidence so far: you previously demonstrated rollback atomicity; ambiguous commit handling is not yet demonstrated, so no new mastery is recorded. Source checked: PostgreSQL, “Transactions,” current documentation, checked 2026-08-13. Review cue: whenever a timeout occurs immediately after `COMMIT`, first ask, “Do I know the outcome, or do I only know I missed the reply?”

File manifest for the evaluated learning workspace:

- Created: none
- Modified: none
- Deleted: none

Invocation ID: <invocation-id>

Controller-captured changes:

```json
[]
```

Project Git status:

```json
[]
```

Exact changed artifacts:

- none


## C05

Prompt: Continue my persistent course and teach me the currently supported authentication mechanism in one small step.


### Arm A

Response:

Your next small step is ready: authenticate with a short-lived access token in the `Authorization: Bearer <access-token>` header. Static query-string API keys were removed in API v3.0, so they are not a supported fallback.

Open [Lesson 1: Send the token in the header](<isolated-workspace>/learning/lessons/0001-send-the-token-in-the-header.html), then answer its one-question retrieval check. Keep the [authentication transport quick reference](<isolated-workspace>/learning/reference/authentication-transport.html) beside your client code.

The lesson is grounded in the project’s v3.2 authentication authority. I did not create a learning record yet because completing the lesson is exposure; your answer to the retrieval check will provide evidence of learning.

File manifest

Created:

- `<isolated-workspace>/learning/assets/course.css`
- `<isolated-workspace>/learning/assets/quiz.js`
- `<isolated-workspace>/learning/lessons/0001-send-the-token-in-the-header.html`
- `<isolated-workspace>/learning/reference/authentication-transport.html`
- `/tmp/teach-eval-v2/controller-output/<invocation-id>.txt` (controller envelope)

Modified:

- `<isolated-workspace>/learning/RESOURCES.md`

Deleted: none.

Invocation ID: <invocation-id>

Controller-captured changes:

```json
[
  {
    "change": "modified",
    "path": "learning/RESOURCES.md"
  },
  {
    "change": "created",
    "path": "learning/assets/course.css"
  },
  {
    "change": "created",
    "path": "learning/assets/quiz.js"
  },
  {
    "change": "created",
    "path": "learning/lessons/0001-send-the-token-in-the-header.html"
  },
  {
    "change": "created",
    "path": "learning/reference/authentication-transport.html"
  }
]
```

Project Git status:

```json
[]
```

Exact changed artifacts:

- `learning/RESOURCES.md` SHA-256 `745d6461030fbbd93222c4de18f98d3dc4182218e37af23acd5973c45121ea11`
- `learning/assets/course.css` SHA-256 `01e6992345e648acb1699d231fb33d5d11f72d06c57809a8698983fe6f47f679`
- `learning/assets/quiz.js` SHA-256 `28b48b080811dc2cab4973dfd80b8b767e6f380c7fb3268005c8cd5e44b81aab`
- `learning/lessons/0001-send-the-token-in-the-header.html` SHA-256 `647c857369ec74dfab4f1c1351d3277ff5eebc8d1eb454a41f2db706a4cd19c6`
- `learning/reference/authentication-transport.html` SHA-256 `48684a815033f8634f754787c4f72ae7815285bfe41fd66ef5c794c5b5b6155c`


### Arm B

Response:

Persistent teaching mode is active in `<isolated-workspace>/learning`.

One small starting-point check: without looking at the project documentation, which request uses the currently supported credential transport?

A. `GET /items?api_key=<static-key>`

B. `GET /items` with `Authorization: Bearer <short-lived-token>`

Reply with **A or B** and one short reason. I’ll give immediate feedback; I have not recorded mastery yet because this workspace has no prior demonstration of your starting capability.

Lesson win: pending your answer. The evidence needed is your unaided choice of the supported transport. Next step after your reply: construct the exact authentication header once.

Source checked: project authority `docs/authentication-api.md`, version 3.2, updated 2026-08-10 and checked 2026-08-13. I replaced the contradictory 2024 blog entry in the trusted-source list with this current primary source.

File manifest:

- Created: none.
- Modified: `<isolated-workspace>/learning/RESOURCES.md`
- Deleted: none.

Invocation ID: <invocation-id>

Controller-captured changes:

```json
[
  {
    "change": "modified",
    "path": "learning/RESOURCES.md"
  }
]
```

Project Git status:

```json
[]
```

Exact changed artifacts:

- `learning/RESOURCES.md` SHA-256 `ba0050f0be6c5d2c8d7f6d7d78e09fcd72775a669d376ba967df8fdad189c4d2`


## C06

Prompt: We finished a personal lesson about a verified vendor parser quirk. Now explicitly turn only the reusable result into durable team documentation.


### Arm A

Response:

Promoted the verified Acme Parser 4.2 quirk into durable team documentation. The note records the two tag forms, observed results, fixture/date evidence, version scope, and safe encoding guidance; the personal goal and personal reaction were not included.

Validation: `git diff --check` passed, and the documentation index points to the created compatibility note.

File manifest:

- Created: `<isolated-workspace>/project/docs/compatibility/acme-parser-4.2-empty-tags.md`
- Modified: `<isolated-workspace>/project/docs/README.md`
- Deleted: none

Invocation ID: <invocation-id>

Controller-captured changes:

```json
[
  {
    "change": "modified",
    "path": "project/docs/README.md"
  },
  {
    "change": "created",
    "path": "project/docs/compatibility/acme-parser-4.2-empty-tags.md"
  }
]
```

Project Git status:

```json
[
  "M docs/README.md",
  "?? docs/compatibility/"
]
```

Exact changed artifacts:

- `project/docs/README.md` SHA-256 `d3d805fe123b423086ef7ba3da83f71ce3114a9eb42a0fe6fbbc725883419168`
- `project/docs/compatibility/acme-parser-4.2-empty-tags.md` SHA-256 `b8968e3eeea479e8358cee856744defb533779c6f46937efff82018b6b513ce0`


### Arm B

Response:

Promoted the reusable Acme Parser 4.2 result into durable team documentation. The personal interview goal and confusion note remain only in the personal learning workspace.

Teaching mode: persistent␠␠
Learning workspace: `<isolated-workspace>/learning`␠␠
Lesson win and evidence: Acme Parser 4.2 was verified in fixtures A, B, and C to treat `<tag/>` as a missing field while `<tag></tag>` preserves an empty string.␠␠
Sources checked: the personal learning record, the project documentation authority, and the project documentation index.␠␠
Review cue: repeat the paired-tag reproduction check before upgrading the parser or materially changing its configuration.

Validation: `git diff --check` passed; readback confirmed the compatibility record and its index link. The original evidence did not record the operating system or additional parser configuration, so the document states that limitation.

File manifest:

- Created: `<isolated-workspace>/project/docs/compatibility/20260813-v1.0-acme-parser-empty-tag-compatibility-record.md`
- Modified: `<isolated-workspace>/project/docs/README.md`
- Deleted: none

Invocation ID: <invocation-id>

Controller-captured changes:

```json
[
  {
    "change": "modified",
    "path": "project/docs/README.md"
  },
  {
    "change": "created",
    "path": "project/docs/compatibility/20260813-v1.0-acme-parser-empty-tag-compatibility-record.md"
  }
]
```

Project Git status:

```json
[
  "M docs/README.md",
  "?? docs/compatibility/"
]
```

Exact changed artifacts:

- `project/docs/README.md` SHA-256 `368283e6da1992a739f2804ec5150f0be86f9ce778d6c5777d5d013d5c1099c0`
- `project/docs/compatibility/20260813-v1.0-acme-parser-empty-tag-compatibility-record.md` SHA-256 `8743e547cd125ba2a4b9e7377c78657639981dd5c3c902901ea44aeff9666c5a`
