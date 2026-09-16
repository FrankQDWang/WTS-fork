# WTS Human-Readable Case Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert the exported WTS 0.1 Domi session into a concise evidence-preserving transcript plus a separate SOP and intelligence review, and document the repeatable mapping rule.

**Architecture:** Keep the redacted `messages.json` as the machine-readable source of truth outside the versioned conversation directory. Replace the current event-dump Case with a phase-oriented readable projection, then produce a review whose claims link back to transcript anchors. Use small read-only validation scripts to prove verbatim message preservation, required-event coverage, deduplication, and credential safety.

**Tech Stack:** Markdown, Python 3 standard library (`json`, `re`, `pathlib`), Git.

---

### Task 1: Build an observable-event inventory

**Files:**
- Read: `domi-session-export/local-session-ab797d57-1123-43fd-aa7b-9cb1a610e591/messages.json`
- Read: `versions/wts-v0-1/SKILL.md`
- Read: `versions/wts-v0-1/references/search-plan.md`
- Read: `versions/wts-v0-1/references/scoring.md`
- Read: `versions/wts-v0-1/references/final-report.md`

**Step 1: Extract the event sequence without message bodies or hidden reasoning**

Run a read-only Python script that prints, for every non-`model_activity` event:

- sequence index and event type;
- visible text events;
- human-interaction prompt, options, and submitted answer;
- tool name and non-secret input shape;
- tool result status, result reference, counts, and error fields;
- written/read file paths;
- terminal completion state.

Do not print `reasoning_content`, credentials, full candidate profiles, duplicated Skill source, or full tool-result payloads.

**Step 2: Group the inventory into WTS phases**

Assign observable events to:

1. request and requirement parsing;
2. clarification and confirmation;
3. target-company research and confirmation;
4. preflight and login;
5. company-term probe;
6. search round 1;
7. search round 2;
8. search round 3, if present;
9. scoring, reflection, Controller, and stopping;
10. final report.

Record an event as `unmapped` when evidence is insufficient; do not infer a phase from hidden reasoning.

**Step 3: Compare the phase inventory to the frozen WTS 0.1 requirements**

Create a checklist of required observable actions and their evidence locations. Use `not observed` when the session record does not prove an action.

### Task 2: Rewrite the human-readable transcript

**Files:**
- Modify: `versions/wts-v0-1/conversations/case-001.md`
- Source: `domi-session-export/local-session-ab797d57-1123-43fd-aa7b-9cb1a610e591/messages.json`

**Step 1: Preserve identity and source metadata**

Keep the existing frontmatter fields:

```yaml
skill: wts-v0-1
case: case-001
tested_at: 2026-09-16
agent: Domi Dev
session_id: local-session-ab797d57-1123-43fd-aa7b-9cb1a610e591
status: completed
```

Add a short note that the transcript is a readable projection of the redacted database export, not a verbatim dump of every internal event.

**Step 2: Preserve the user request verbatim**

Write the complete sanitized user `content` under `## 用户原始需求`. Do not summarize or rewrite it.

**Step 3: Write the phase-oriented execution transcript**

For each observed phase, use this structure:

```markdown
## <phase>

### Agent 对用户的表达
<verbatim visible text, when present>

### 用户交互
- 问题：...
- 选项：...
- 用户选择：...

### 关键动作与结果
- 动作：...
- 关键入参：...
- 结果：...

### 可观察的下一步依据
<only evidence explicitly present in text, files, tool inputs, or tool outputs>
```

Omit empty subsections. Preserve exact search terms, filter values, counts, user choices, errors, retries, and explicit decision text. Summarize candidate-result payloads into counts and already-masked display names plus job/company evidence only when it directly affects a decision.

**Step 4: Preserve the final assistant response verbatim**

Write the complete sanitized assistant `content` under `## Agent 最终答复` without rewriting it.

**Step 5: Add the source index**

Link the transcript to:

```text
../../../domi-session-export/local-session-ab797d57-1123-43fd-aa7b-9cb1a610e591/messages.json
```

Also record that the source contains 2 messages and 293 assistant execution events.

**Step 6: Run transcript validation**

Run a Python assertion script that checks:

```python
assert source_user_content in transcript
assert source_assistant_content in transcript
assert transcript.count('local-session-ab797d57-1123-43fd-aa7b-9cb1a610e591') >= 1
assert 'model_activity' not in transcript
assert 'reasoning_content' not in transcript
assert transcript.count('"request_id"') == 0
assert len(transcript.encode()) < 150_000
```

Expected: all assertions pass. If the 150 KB limit cannot be met without removing decision evidence, document the reason and use the smallest evidence-complete result.

### Task 3: Create the evidence-backed review

**Files:**
- Create: `versions/wts-v0-1/conversations/case-001-review.md`
- Read: `versions/wts-v0-1/conversations/case-001.md`
- Read: `versions/wts-v0-1/SKILL.md`
- Read: `versions/wts-v0-1/references/*.md`

**Step 1: Write the review header and evaluation boundary**

Include the Skill version, Case number, Session ID, reviewed transcript link, and this statement in substance:

> This review evaluates observable behavior and artifacts. It does not claim access to the model's hidden chain of thought.

**Step 2: Write a one-paragraph overall assessment**

State the overall SOP adherence, the most consequential deviation, and the strongest observed intelligence signal. Separate facts from reviewer inference.

**Step 3: Build the SOP adherence table**

Use columns:

```text
Requirement | Status | Observable evidence | Assessment
```

Allowed statuses are `遵循`, `部分遵循`, `未遵循`, and `无法观测`. Each evidence cell must link to a stable heading in `case-001.md`.

**Step 4: Reconstruct the key decision chain**

Describe requirement interpretation, company research, query design, round-to-round adjustment, candidate evaluation, and stopping decision. Label any reconstruction that is not explicitly stated as `复盘推断`.

**Step 5: Identify intelligence emergence**

For each proposed emergence include:

```text
Observed behavior | Why it is valuable | Transcript evidence | Productization recommendation
```

Do not count simple SOP compliance as emergence. Distinguish repeatable capability from a one-off outcome.

**Step 6: Record problems, risks, and version implications**

Cover unsupported claims, mechanical repetition, missed gates, weak error handling, or mismatch between the user's 5-second pacing instruction and actual observable behavior. State whether each item suggests a Skill change, runtime change, or only better instrumentation.

### Task 4: Update the conversation-archive specification

**Files:**
- Modify: `Agent.md:310-520`

**Step 1: Replace the single-file Case format with the paired-file convention**

Document:

```text
case-NNN.md
case-NNN-review.md
```

Keep `messages.json` as a trace source in `domi-session-export/<session_id>/`, not as the primary review artifact.

**Step 2: Add the mapping rules**

Specify retained content, removed noise, phase grouping, evidence links, inference labels, and the separation between SOP adherence and intelligence emergence.

**Step 3: Add duplicate and numbering rules**

Treat the transcript and review as one logical Case. Determine the next number from transcript filenames only, and reject a duplicate Session ID across either file.

### Task 5: Validate the complete paired Case

**Files:**
- Validate: `versions/wts-v0-1/conversations/case-001.md`
- Validate: `versions/wts-v0-1/conversations/case-001-review.md`
- Validate: `Agent.md`

**Step 1: Check Markdown and Git whitespace**

Run:

```bash
git diff --check -- Agent.md versions/wts-v0-1/conversations/case-001.md versions/wts-v0-1/conversations/case-001-review.md
```

Expected: no output and exit code 0.

**Step 2: Check identity, pairing, and source consistency**

Run a Python assertion script verifying:

- both Markdown files contain the same Case number and Session ID;
- the review links to the transcript;
- the transcript links to `messages.json`;
- the complete sanitized user and assistant messages remain verbatim in the transcript;
- no duplicate Case uses the same Session ID.

Expected: all assertions pass.

**Step 3: Scan both files for credentials and hidden-reasoning fields**

Use a Python regex scanner for Bearer values, API keys, access/refresh tokens, Cookie assignments, password/secret assignments, GitHub token prefixes, and OpenAI-style secret prefixes. Also assert that `reasoning_content` and raw `model_activity` data are absent.

Expected: zero credential matches and zero hidden-reasoning fields.

**Step 4: Report the result without committing unrelated changes**

List the two Case files, their sizes, covered phases, validation results, and any evidence gaps. Do not stage or commit unrelated changes in `source/SKILL.md` or `.DS_Store` files.
