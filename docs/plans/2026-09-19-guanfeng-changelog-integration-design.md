# Guanfeng Changelog Integration Design

## Goal

Selectively integrate the behavior changes documented in
`collaborators/guanfeng/CHANGELOG.md` into the official `source/` Skill without
replacing the current source tree or changing any version identifiers.

## Scope

The integration adds the following behaviors where they are absent from the
official source:

- `direct` and `human` browser interaction modes, with `human` as the channel
  default and explicit capability declaration in compiled workflows.
- Requirement-version consistency across search rounds.
- Reuse and validation of prior candidate scores and decisions.
- Validation against the plan embedded in the workflow that actually ran,
  instead of trusting an editable historical plan file.
- Deterministic settlement of the last completed round into
  `final-report-data.json`.
- Guidance for paginated result reading, file editing, confirmation forms, and
  the absence of a `reflect` Builder command.

The integration preserves the official Skill's existing target-company
research, company probe, pacing, three-round search policy, reference files,
and reporting behavior. It does not modify `SKILL_VERSION`, frozen version
packages, or installed Domi Skills.

## Approach

Treat the collaborator tree as a change reference, not as a replacement.
For each changelog item, map the behavior to the corresponding official file,
then port only the smallest compatible code or documentation change.

The existing Builder remains the integration point. Candidate-decision
validation is added as a separate module so scoring rules remain testable and
do not enlarge the Builder further. Existing probe and pacing paths continue
to work unchanged. New plan fields are additive and become mandatory only at
the round boundaries described by the Skill contract.

## Data Flow

1. The Skill writes an iteration plan containing `requirement_version` and,
   after the first completed round, `decision_basis`.
2. The Builder loads the plan, then loads the prior plan from the persisted
   workflow that actually executed.
3. The decision validator checks requirement consistency, result references,
   score history, PRF state, and the already-selected next action.
4. The Builder compiles the official search workflow, preserving company probe
   and pacing behavior while applying the selected interaction mode.
5. The compiled workflow embeds a protected input-plan snapshot.
6. Settlement validates the final decision and writes a permission-restricted
   report-data file for the final report renderer.

## Error Handling

- Invalid or missing historical workflow results fail with actionable errors;
  the Builder must not silently fall back to edited historical plan files when
  a persisted executed plan is available.
- Same-version changes to hard or semantic criteria are rejected.
- Candidate results must remain content-addressed and scoped to the current
  task.
- Interrupted human-mode actions are left to the host workflow semantics; the
  Skill does not retry external writes automatically.
- Settlement never creates an additional search round.

## Testing

Add Python `unittest` coverage for the new decision-validation module and the
Builder integration. Tests will first demonstrate missing behavior, then cover:

- interaction-mode metadata and capability requirements;
- same-version criteria drift rejection;
- executed-plan snapshot reuse;
- deterministic score calculation and history preservation;
- settlement output and file permissions;
- continued compilation of preflight, search, and company-probe workflows;
- static parsing of JSON assets and Python sources.

Documentation checks will verify that the official SOP and search-plan
contract describe the integrated behavior without removing existing official
features.
