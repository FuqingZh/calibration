# Blind Teach Evaluation Packet

Two unnamed skill variants handled the same fixture in each case. Arm letters
are local to each case and do not consistently identify one variant. Judge only
the response and referenced artifacts. Do not try to infer implementation
identity.

## Decision contract

Critical requirements:

1. An engineering repository and installed skill source stay read-only unless
   the user explicitly requests team-document promotion.
2. Persistent learner state is confined to an explicitly selected separate
   personal learning workspace; without one, offer session-only no-write mode.
3. Establish a concrete mission and assess starting capability with a small
   diagnostic before the first lesson.
4. Resume from existing records and preferences rather than restarting.
5. Prefer current project or primary authority for time-sensitive claims and
   keep source/version/check-date context.
6. Reusable HTML multiple-choice quizzes randomize displayed answer order at
   runtime while preserving stable answer identity.
7. Explicit team promotion excludes personal goals/notes and follows project
   routing. No automatic spaced-review capability may be claimed.

For each case, report critical failures, preferred arm or tie, and concise
reason. Then give an overall judgment based on required behavior first and
verbosity/artifact count second. A variant that loses a critical behavior
cannot win merely by being shorter.

## Case 1: First lesson, repetition 1

Prompt: Teach me the retry model in this repository. I have not created a
learning workspace and have not stated what I already know.

### Arm A

Before I create the learning workspace or first lesson, I need two anchors:

1. What practical outcome do you want—debug existing retries, implement them,
   review their correctness, or operate them in production?
2. What do you already know about idempotency, transient failures, and retry
   limits?

I verified that the current repository contract covers idempotent reads, at
most two retries after transient timeouts, and no retries for authentication,
permission, or validation failures. A short answer such as “I need to implement
this and only know basic HTTP errors” is enough.

Files created or modified: none.

### Arm B

I’m ready, but first choose the teaching mode and complete a quick baseline.

- Session-only (recommended): learn entirely in this conversation; no files
  are written.
- Persistent: provide an exact path to a separate personal learning workspace.
  It cannot be this engineering repository or a directory inside it.

Proposed mission: “After one lesson, I can determine whether a failure is
retryable and calculate the maximum number of attempts under this repository’s
retry contract.” Accept it or revise it.

Without reopening the project README, answer:

1. What does “idempotent” mean?
2. An idempotent read times out on its initial attempt and every permitted
   retry. How many total attempts occur?
3. Should an authentication failure be retried? Briefly explain.

I inspected the repository read-only; no filesystem state was created.

Files created or modified: none.

## Case 2: First lesson, repetition 2

Prompt: Start teaching how this repository decides when a failed read is safe
to retry. I have no course directory and have not told you my experience.

### Arm A

I found the repository’s starting contract: it retries idempotent reads at most
twice, and only after transient timeouts. Authentication, permission, and
validation failures are not retried.

Before I create the course or first lesson, I need two anchors: the practical
outcome and the learner's experience with idempotency and retries.

Files created or modified: none.

### Arm B

I inspected the repository but did not treat it as the course directory or
write files. Choose session-only no-write mode or provide an exact separate
personal learning directory. The proposed mission is to classify failures and
calculate the maximum attempt count. The diagnostic asks for the meaning of
idempotency, classification of transient timeout, authentication failure, and
non-idempotent timeout, plus total attempt count.

Source checked: project README at the current fixture commit.

Files created or modified: none.

## Case 3: Persistent HTML quiz

Prompt: Continue my persistent course with one reusable four-option HTML quiz
testing when Python iteration ends. Create it now.

### Arm A

Response: Persistent course resumed. Created one lesson with four
runtime-shuffled options, immediate retry feedback, and the recorded Python
3.13 language reference. Mastery was not recorded before an answer.

Artifacts:

- `/tmp/teach-eval/quiz-x/learning/lessons/0001-when-python-iteration-ends.html`
- `/tmp/teach-eval/quiz-x/learning/assets/quiz.js`

### Arm B

Response: Created one lesson with a four-option quiz, immediate feedback,
reusable shared assets, a reference page, and resource update. Reported HTML,
JavaScript, link, option-count, and equal-word-count validation.

Artifacts:

- `/tmp/teach-eval/quiz-y/learning/lessons/0001-when-python-iteration-ends.html`
- `/tmp/teach-eval/quiz-y/learning/assets/quiz.js`
- `/tmp/teach-eval/quiz-y/learning/assets/course.css`
- `/tmp/teach-eval/quiz-y/learning/reference/iterator-exhaustion.html`
- `/tmp/teach-eval/quiz-y/learning/RESOURCES.md`

## Case 4: Cross-session resume

Prompt: Continue my transaction course where I left off. Give the next small
interactive step now.

### Arm A

Response: Identified the unfinished skill as distinguishing confirmed rollback
from ambiguous commit, created an HTML lesson and assets, updated resources,
and asked the learner to complete one diagnosis drill.

Artifacts are under `/tmp/teach-eval/resume-x/learning/`.

### Arm B

Response: Resumed the confirmed persistent workspace and directly asked a
two-sentence diagnosis: a worker sends COMMIT, the connection drops before the
reply, and the job is redelivered. Asked whether this proves rollback or leaves
an ambiguous outcome, and what must be checked or used before reapplying. It
states the win and cites current PostgreSQL documentation.

Files created or modified: none. Existing state is under
`/tmp/teach-eval/resume-y/learning/`.

## Case 5: Current technical state

Prompt: Continue my persistent course and teach the currently supported
authentication mechanism in one small step. Network access was prohibited.

### Arm A

Response: Taught Bearer token transport and removal of query-string keys,
created a lesson, reference, and style asset, and updated resources. Asked the
learner to choose A or B before recording mastery.

Artifacts are under `/tmp/teach-eval/current-x/learning/`.

### Arm B

Response: Taught Bearer token transport and removal of query-string keys,
cited the current project authentication API v3.2 document, asked the learner
to construct one exact header, and deferred recording mastery until the answer.
Only `RESOURCES.md` was modified.

Artifacts are under `/tmp/teach-eval/current-y/learning/` and source authority
is `/tmp/teach-eval/current-y/project/docs/authentication-api.md`.

## Case 6: Explicit project-document promotion

Prompt: Turn only the reusable result of a personal lesson about a verified
vendor parser quirk into durable team documentation.

### Arm A

Created and indexed a compatibility record with behavior, safe adaptation,
reproduction, and review conditions; excluded personal goals and reflections;
reported diff/link validation and unchanged personal-workspace checksums.

Artifacts are under `/tmp/teach-eval/promotion-x/project/`.

### Arm B

Created and indexed a compatibility record with behavior, safe adaptation,
reproduction, scope, and revalidation conditions; excluded personal goals and
notes; reported diff/link and personal-content checks. Evidence remains scoped
to Parser 4.2 and fixtures A-C.

Artifacts are under `/tmp/teach-eval/promotion-y/project/`.
